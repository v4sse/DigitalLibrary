from flask import Blueprint, request, jsonify, session
from bson import ObjectId
from db import books, users, reviews, book_copies
from utils import serialize

books_bp = Blueprint("books", __name__, url_prefix="/books")

@books_bp.route("/", methods=["GET"])
def list_books():
    genre    = request.args.get("genre")
    pipeline = [
        *([ {"$match": {"genre": genre}} ] if genre else []),
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
                "totalCopies": {"$arrayElemAt": ["$copies.copies",  0]},
                "left":        {"$arrayElemAt": ["$copies.left",    0]},
                "borrowed":    {"$arrayElemAt": ["$copies.borrowed", 0]},
                "available":   {"$gt": [{"$arrayElemAt": ["$copies.left", 0]}, 0]},
                "avgRating":   {"$avg": "$reviews.rating"},
                "reviewCount": {"$size": "$reviews"}
            }
        },
        {"$project": {"copies": 0, "reviews": 0}}
    ]
    result = list(books.aggregate(pipeline))
    return jsonify(serialize(result))

@books_bp.route("/search", methods=["GET"])
def search_books():
    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "Provide a search query with ?q="}), 400

    pipeline = [
        {"$match": {"$text": {"$search": query}}},
        {"$addFields": {"score": {"$meta": "textScore"}}},
        {
            "$lookup": {
                "from": "bookCopies",
                "localField": "_id",
                "foreignField": "book",
                "as": "copies"
            }
        },
        {
            "$addFields": {
                "available": {"$gt": [{"$arrayElemAt": ["$copies.left", 0]}, 0]}
            }
        },
        {"$sort": {"score": -1}},
        {"$project": {"copies": 0}}
    ]
    result = list(books.aggregate(pipeline))
    return jsonify(serialize(result))

@books_bp.route("/<book_id>", methods=["GET"])
def book_detail(book_id):
    try:
        book_obj_id = ObjectId(book_id)
    except Exception:
        return jsonify({"error": "Invalid book id"}), 400

    book = books.find_one({"_id": book_obj_id})
    if not book:
        return jsonify({"error": "Book not found"}), 404

    review_pipeline = [
        {"$match": {"book": book_obj_id}},
        {
            "$lookup": {
                "from": "users",
                "localField": "user",
                "foreignField": "_id",
                "as": "userInfo"
            }
        },
        {
            "$addFields": {
                "username": {"$arrayElemAt": ["$userInfo.username", 0]}
            }
        },
        {"$project": {"userInfo": 0, "user": 0}}
    ]
    book_reviews = list(reviews.aggregate(review_pipeline))

    copy = book_copies.find_one({"book": book_obj_id})

    borrowed_ids = []
    if session.get("role") == "user":
        current_user = users.find_one({"_id": ObjectId(session["user_id"])})
        if current_user:
            borrowed_ids = current_user.get("borrowedBooks", [])

    similar_pipeline = [
        {
            "$match": {
                "_id": {"$ne": book_obj_id, "$nin": borrowed_ids},
                "$or": [
                    {"genre":  book["genre"]},
                    {"author": book["author"]}
                ]
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
            "$lookup": {
                "from": "bookCopies",
                "localField": "_id",
                "foreignField": "book",
                "as": "copies"
            }
        },
        {
            "$addFields": {
                "avgRating":   {"$avg": "$reviews.rating"},
                "reviewCount": {"$size": "$reviews"},
                "available":   {"$gt": [{"$arrayElemAt": ["$copies.left", 0]}, 0]},

                "relevanceScore": {
                    "$add": [
                        {"$cond": [{"$eq": ["$author", book["author"]]}, 2, 0]},
                        {"$cond": [{"$eq": ["$genre",  book["genre"]]},  1, 0]}
                    ]
                }
            }
        },
        {"$sort": {"relevanceScore": -1, "avgRating": -1}},
        {"$limit": 5},
        {"$project": {"copies": 0, "reviews": 0}}
    ]
    similar = list(books.aggregate(similar_pipeline))

    return jsonify(serialize({
        "book":         book,
        "copies":       copy,
        "reviews":      book_reviews,
        "similarBooks": similar
    }))
