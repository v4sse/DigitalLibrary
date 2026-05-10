from flask import Blueprint, request, jsonify, session
from bson import ObjectId
from db import books, reviews
from utils import serialize

reviews_bp = Blueprint("reviews", __name__, url_prefix="/reviews")


@reviews_bp.route("/<book_id>", methods=["GET"])
def book_reviews(book_id):
    try:
        book_obj_id = ObjectId(book_id)
    except Exception:
        return jsonify({"error": "Invalid book id"}), 400

    if not books.find_one({"_id": book_obj_id}):
        return jsonify({"error": "Book not found"}), 404

    reviews_pipeline = [
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
        {"$project": {"userInfo": 0, "user": 0, "book": 0}},
        {"$sort": {"rating": -1}}
    ]

    summary_pipeline = [
        {"$match": {"book": book_obj_id}},
        {
            "$group": {
                "_id": None,
                "avgRating":   {"$avg": "$rating"},
                "reviewCount": {"$sum": 1},
                "ratings":     {"$push": "$rating"}
            }
        },
        {
            "$addFields": {
                "fiveStars":  {"$size": {"$filter": {"input": "$ratings", "cond": {"$eq": ["$$this", 5]}}}},
                "fourStars":  {"$size": {"$filter": {"input": "$ratings", "cond": {"$eq": ["$$this", 4]}}}},
                "threeStars": {"$size": {"$filter": {"input": "$ratings", "cond": {"$eq": ["$$this", 3]}}}},
                "twoStars":   {"$size": {"$filter": {"input": "$ratings", "cond": {"$eq": ["$$this", 2]}}}},
                "oneStar":    {"$size": {"$filter": {"input": "$ratings", "cond": {"$eq": ["$$this", 1]}}}}
            }
        },
        {"$project": {"_id": 0, "ratings": 0}}
    ]

    summary_result = list(reviews.aggregate(summary_pipeline))
    return jsonify(serialize({
        "summary": summary_result[0] if summary_result else {"avgRating": None, "reviewCount": 0},
        "reviews": list(reviews.aggregate(reviews_pipeline))
    }))


@reviews_bp.route("/<book_id>", methods=["POST"])
def add_review(book_id):
    if session.get("role") != "user":
        return jsonify({"error": "Login as user to review"}), 401

    try:
        book_obj_id = ObjectId(book_id)
    except Exception:
        return jsonify({"error": "Invalid book id"}), 400

    if not books.find_one({"_id": book_obj_id}):
        return jsonify({"error": "Book not found"}), 404

    data   = request.json
    rating = data.get("rating")
    if rating is None or not (1 <= int(rating) <= 5):
        return jsonify({"error": "Rating must be 1–5"}), 400

    user_obj_id = ObjectId(session["user_id"])
    if reviews.find_one({"book": book_obj_id, "user": user_obj_id}):
        return jsonify({"error": "You already reviewed this book"}), 400

    reviews.insert_one({
        "book":    book_obj_id,
        "user":    user_obj_id,
        "rating":  int(rating),
        "comment": data.get("comment", "")
    })
    return jsonify({"message": "Review added"}), 201
