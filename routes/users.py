from datetime import datetime, timezone
from flask import Blueprint, jsonify, session
from bson import ObjectId
from db import books, users, book_copies, borrows
from utils import serialize

users_bp = Blueprint("users", __name__, url_prefix="/users")


def require_user(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("role") != "user":
            return jsonify({"error": "Login as user"}), 401
        return f(*args, **kwargs)
    return wrapper


@users_bp.route("/me", methods=["GET"])
@require_user
def my_profile():
    pipeline = [
        {"$match": {"_id": ObjectId(session["user_id"])}},
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
    if not result:
        return jsonify({"error": "User not found"}), 404
    return jsonify(serialize(result[0]))


@users_bp.route("/history", methods=["GET"])
@require_user
def borrow_history():
    user_obj_id = ObjectId(session["user_id"])
    pipeline = [
        {"$match": {"user": user_obj_id}},
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
                "bookName": {"$arrayElemAt": ["$bookInfo.name",   0]},
                "author":   {"$arrayElemAt": ["$bookInfo.author", 0]},
                "genre":    {"$arrayElemAt": ["$bookInfo.genre",  0]},
                "bookId":   {"$arrayElemAt": ["$bookInfo._id",    0]}
            }
        },
        {"$project": {"bookInfo": 0}},
        {"$sort": {"borrowedAt": -1}}
    ]
    result = list(borrows.aggregate(pipeline))
    return jsonify(serialize(result))


@users_bp.route("/borrow/<book_id>", methods=["POST"])
@require_user
def borrow_book(book_id):
    try:
        book_obj_id = ObjectId(book_id)
    except Exception:
        return jsonify({"error": "Invalid book id"}), 400

    user_obj_id = ObjectId(session["user_id"])
    user        = users.find_one({"_id": user_obj_id})

    if user.get("blacklisted"):
        return jsonify({"error": "Your account has been blacklisted"}), 403

    if book_obj_id in user.get("borrowedBooks", []):
        return jsonify({"error": "You already borrowed this book"}), 400

    copy = book_copies.find_one({"book": book_obj_id})
    if not copy:
        return jsonify({"error": "Book not found in library"}), 404
    if copy["left"] <= 0:
        return jsonify({"error": "No copies available"}), 400

    book_copies.update_one(
        {"book": book_obj_id},
        {"$inc": {"borrowed": 1, "left": -1}}
    )
    users.update_one(
        {"_id": user_obj_id},
        {"$push": {"borrowedBooks": book_obj_id}}
    )
    borrows.insert_one({
        "user":        user_obj_id,
        "book":        book_obj_id,
        "borrowedAt":  datetime.now(timezone.utc),
        "returnedAt":  None,
        "forcedReturn": False
    })
    return jsonify({"message": "Book borrowed successfully"})


@users_bp.route("/return/<book_id>", methods=["POST"])
@require_user
def return_book(book_id):
    try:
        book_obj_id = ObjectId(book_id)
    except Exception:
        return jsonify({"error": "Invalid book id"}), 400

    user_obj_id = ObjectId(session["user_id"])
    user        = users.find_one({"_id": user_obj_id})

    if book_obj_id not in user.get("borrowedBooks", []):
        return jsonify({"error": "You have not borrowed this book"}), 400

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
        {"$set": {"returnedAt": datetime.now(timezone.utc)}}
    )
    return jsonify({"message": "Book returned successfully"})
