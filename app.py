import os
from flask import Flask, redirect, render_template
from dotenv import load_dotenv
from db import create_indexes
from routes.auth    import auth_bp
from routes.books   import books_bp
from routes.users   import users_bp
from routes.admin   import admin_bp
from routes.reviews import reviews_bp

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

app.register_blueprint(auth_bp)
app.register_blueprint(books_bp)
app.register_blueprint(users_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(reviews_bp)


@app.route("/")
def index():
    return redirect("/home")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/home")
def home_page():
    return render_template("home.html")

@app.route("/book/<book_id>")
def book_page(book_id):
    return render_template("book.html", book_id=book_id)

@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")

@app.route("/admin-panel")
def admin_page():
    return render_template("admin.html")


if __name__ == "__main__":
    create_indexes()
    app.run(host="0.0.0.0", port=5000, debug=True)
