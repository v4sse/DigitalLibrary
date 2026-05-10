from flask import Blueprint, request, jsonify, session
from db import users, admins
from utils import serialize

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.json
    if not data.get("username") or not data.get("password"):
        return jsonify({"error": "Username and password required"}), 400
    if users.find_one({"username": data["username"]}):
        return jsonify({"error": "Username already taken"}), 400
    users.insert_one({
        "username":      data["username"],
        "password":      data["password"],
        "borrowedBooks": []
    })
    return jsonify({"message": "User registered"}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    user = users.find_one({"username": data.get("username"), "password": data.get("password")})
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401
    session["user_id"]  = str(user["_id"])
    session["role"]     = "user"
    session["username"] = user["username"]
    return jsonify({"message": "Logged in", "username": user["username"]})


@auth_bp.route("/admin/login", methods=["POST"])
def admin_login():
    data  = request.json
    admin = admins.find_one({"username": data.get("username"), "password": data.get("password")})
    if not admin:
        return jsonify({"error": "Invalid credentials"}), 401
    session["user_id"]  = str(admin["_id"])
    session["role"]     = "admin"
    session["username"] = admin["username"]
    return jsonify({"message": "Admin logged in", "username": admin["username"]})


@auth_bp.route("/unified-login", methods=["POST"])
def unified_login():
    """Search users collection first, then admins — returns role on success."""
    data     = request.json
    username = data.get("username", "")
    password = data.get("password", "")

    user = users.find_one({"username": username, "password": password})
    if user:
        session["user_id"]  = str(user["_id"])
        session["role"]     = "user"
        session["username"] = user["username"]
        return jsonify({"role": "user", "username": user["username"]})

    admin = admins.find_one({"username": username, "password": password})
    if admin:
        session["user_id"]  = str(admin["_id"])
        session["role"]     = "admin"
        session["username"] = admin["username"]
        return jsonify({"role": "admin", "username": admin["username"]})

    return jsonify({"error": "Invalid credentials"}), 401


@auth_bp.route("/me", methods=["GET"])
def me():
    if "user_id" not in session:
        return jsonify({"role": None})
    return jsonify({
        "role":     session.get("role"),
        "username": session.get("username"),
        "user_id":  session.get("user_id")
    })


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})
