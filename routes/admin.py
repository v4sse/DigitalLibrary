from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, session
from bson import ObjectId
from db import books, users, admins, reviews, book_copies, borrows
from utils import serialize

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def require_admin(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return wrapper


@admin_bp.route("/books", methods=["POST"])
@require_admin
def add_book():
    data = request.json
    for field in ("name", "genre", "author", "copies"):
        if not data.get(field):
            return jsonify({"error": f"'{field}' is required"}), 400

    copies = int(data["copies"])
    result = books.insert_one({
        "name":   data["name"],
        "genre":  data["genre"],
        "author": data["author"]
    })
    book_copies.insert_one({
        "book":     result.inserted_id,
        "copies":   copies,
        "borrowed": 0,
        "left":     copies
    })
    return jsonify({"message": "Book added", "id": str(result.inserted_id)}), 201


@admin_bp.route("/books/<book_id>/copies", methods=["PUT"])
@require_admin
def update_copies(book_id):
    try:
        book_obj_id = ObjectId(book_id)
    except Exception:
        return jsonify({"error": "Invalid book id"}), 400

    data = request.json
    new_total = data.get("copies")
    if new_total is None or int(new_total) < 0:
        return jsonify({"error": "Provide a valid 'copies' value"}), 400

    copy = book_copies.find_one({"book": book_obj_id})
    if not copy:
        return jsonify({"error": "Book not found"}), 404

    new_total  = int(new_total)
    new_left   = new_total - copy["borrowed"]
    if new_left < 0:
        return jsonify({"error": f"Cannot set copies below current borrowed count ({copy['borrowed']})"}), 400

    book_copies.update_one(
        {"book": book_obj_id},
        {"$set": {"copies": new_total, "left": new_left}}
    )
    return jsonify({"message": "Copies updated", "copies": new_total, "left": new_left})


@admin_bp.route("/books/<book_id>", methods=["DELETE"])
@require_admin
def delete_book(book_id):
    try:
        book_obj_id = ObjectId(book_id)
    except Exception:
        return jsonify({"error": "Invalid book id"}), 400

    copy = book_copies.find_one({"book": book_obj_id})
    if copy and copy["borrowed"] > 0:
        return jsonify({"error": f"Cannot delete: {copy['borrowed']} copies still borrowed"}), 400

    books.delete_one({"_id": book_obj_id})
    book_copies.delete_one({"book": book_obj_id})
    reviews.delete_many({"book": book_obj_id})

    users.update_many({}, {"$pull": {"borrowedBooks": book_obj_id}})

    return jsonify({"message": "Book deleted"})


@admin_bp.route("/books", methods=["GET"])
@require_admin
def all_books():
    """All books with copy counts and avg rating."""
    pipeline = [
        {
            "$lookup": {
                "from": "bookCopies",
                "localField": "_id",
                "foreignField": "book",
                "as": "copies"
            }
        },
        {
            "$lookup": {
                "from": "reviews",
                "localField": "_id",
                "foreignField": "book",
                "as": "reviews"
            }
        },
        {
            "$addFields": {
                "totalCopies": {"$arrayElemAt": ["$copies.copies",   0]},
                "borrowed":    {"$arrayElemAt": ["$copies.borrowed", 0]},
                "left":        {"$arrayElemAt": ["$copies.left",     0]},
                "avgRating":   {"$avg": "$reviews.rating"},
                "reviewCount": {"$size": "$reviews"}
            }
        },
        {"$project": {"copies": 0, "reviews": 0}},
        {"$sort": {"borrowed": -1}}
    ]
    result = list(books.aggregate(pipeline))
    return jsonify(serialize(result))


@admin_bp.route("/users", methods=["GET"])
@require_admin
def all_users():
    """All users with their borrowed books populated."""
    pipeline = [
        {
            "$lookup": {
                "from": "books",
                "localField": "borrowedBooks",
                "foreignField": "_id",
                "as": "borrowedBooks"
            }
        },
        {"$project": {"password": 0}}
    ]
    result = list(users.aggregate(pipeline))
    return jsonify(serialize(result))


@admin_bp.route("/stats", methods=["GET"])
@require_admin
def stats():
    """Aggregated stats: totals per genre, most borrowed books."""
    genre_pipeline = [
        {
            "$lookup": {
                "from": "bookCopies",
                "localField": "_id",
                "foreignField": "book",
                "as": "copies"
            }
        },
        {
            "$lookup": {
                "from": "reviews",
                "localField": "_id",
                "foreignField": "book",
                "as": "reviews"
            }
        },
        {
            "$addFields": {
                "borrowed":  {"$arrayElemAt": ["$copies.borrowed", 0]},
                "left":      {"$arrayElemAt": ["$copies.left",     0]},
                "avgRating": {"$avg": "$reviews.rating"}
            }
        },
        {
            "$group": {
                "_id":           "$genre",
                "totalBooks":    {"$sum": 1},
                "totalBorrowed": {"$sum": "$borrowed"},
                "avgRating":     {"$avg": "$avgRating"},
                "books": {
                    "$push": {
                        "name":      "$name",
                        "author":    "$author",
                        "borrowed":  "$borrowed",
                        "left":      "$left",
                        "avgRating": "$avgRating"
                    }
                }
            }
        },
        {"$sort": {"totalBorrowed": -1}}
    ]

    top_books_pipeline = [
        {
            "$lookup": {
                "from": "books",
                "localField": "book",
                "foreignField": "_id",
                "as": "bookInfo"
            }
        },
        {"$unwind": "$bookInfo"},
        {
            "$project": {
                "name":    "$bookInfo.name",
                "author":  "$bookInfo.author",
                "genre":   "$bookInfo.genre",
                "borrowed": 1,
                "left":     1,
                "copies":   1
            }
        },
        {"$sort": {"borrowed": -1}},
        {"$limit": 10}
    ]

    return jsonify(serialize({
        "byGenre":  list(books.aggregate(genre_pipeline)),
        "topBooks": list(book_copies.aggregate(top_books_pipeline))
    }))


@admin_bp.route("/users/<user_id>/force-return/<book_id>", methods=["POST"])
@require_admin
def force_return(user_id, book_id):
    try:
        user_obj_id = ObjectId(user_id)
        book_obj_id = ObjectId(book_id)
    except Exception:
        return jsonify({"error": "Invalid id"}), 400

    user = users.find_one({"_id": user_obj_id})
    if not user:
        return jsonify({"error": "User not found"}), 404

    if book_obj_id not in user.get("borrowedBooks", []):
        return jsonify({"error": "User has not borrowed this book"}), 400

    book_copies.update_one(
        {"book": book_obj_id},
        {"$inc": {"borrowed": -1, "left": 1}}
    )
    users.update_one(
        {"_id": user_obj_id},
        {"$pull": {"borrowedBooks": book_obj_id}}
    )
    borrows.find_one_and_update(
        {"user": user_obj_id, "book": book_obj_id, "returnedAt": None},
        {"$set": {"returnedAt": datetime.now(timezone.utc), "forcedReturn": True}}
    )
    return jsonify({"message": "Book forcefully returned"})


@admin_bp.route("/users/<user_id>/blacklist", methods=["POST"])
@require_admin
def blacklist_user(user_id):
    try:
        user_obj_id = ObjectId(user_id)
    except Exception:
        return jsonify({"error": "Invalid user id"}), 400

    result = users.update_one({"_id": user_obj_id}, {"$set": {"blacklisted": True}})
    if result.matched_count == 0:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"message": "User blacklisted"})


@admin_bp.route("/users/<user_id>/unblacklist", methods=["POST"])
@require_admin
def unblacklist_user(user_id):
    try:
        user_obj_id = ObjectId(user_id)
    except Exception:
        return jsonify({"error": "Invalid user id"}), 400

    result = users.update_one({"_id": user_obj_id}, {"$set": {"blacklisted": False}})
    if result.matched_count == 0:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"message": "User unblacklisted"})


@admin_bp.route("/borrows", methods=["GET"])
@require_admin
def all_borrows():
    """All borrow records with user and book info, newest first."""
    pipeline = [
        {
            "$lookup": {
                "from": "users",
                "localField": "user",
                "foreignField": "_id",
                "as": "userInfo"
            }
        },
        {
            "$lookup": {
                "from": "books",
                "localField": "book",
                "foreignField": "_id",
                "as": "bookInfo"
            }
        },
        {
            "$addFields": {
                "username": {"$arrayElemAt": ["$userInfo.username", 0]},
                "bookName": {"$arrayElemAt": ["$bookInfo.name",     0]},
                "author":   {"$arrayElemAt": ["$bookInfo.author",   0]}
            }
        },
        {"$project": {"userInfo": 0, "bookInfo": 0}},
        {"$sort": {"borrowedAt": -1}}
    ]
    result = list(borrows.aggregate(pipeline))
    return jsonify(serialize(result))
