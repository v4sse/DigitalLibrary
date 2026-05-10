import os
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING, TEXT

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
db = client[os.getenv("MONGO_DB", "digital_library")]

books       = db["books"]
users       = db["users"]
admins      = db["admins"]
reviews     = db["reviews"]
book_copies = db["bookCopies"]
borrows     = db["borrows"]


def create_indexes():
    books.create_index([("genre", ASCENDING)])
    books.create_index([("author", ASCENDING)])
    books.create_index([("name", TEXT), ("author", TEXT), ("genre", TEXT)])
    users.create_index([("username", ASCENDING)], unique=True)
    admins.create_index([("username", ASCENDING)], unique=True)
    reviews.create_index([("book", ASCENDING)])
    reviews.create_index([("book", ASCENDING), ("user", ASCENDING)], unique=True)
    book_copies.create_index([("book", ASCENDING)], unique=True)
    borrows.create_index([("user", ASCENDING)])
    borrows.create_index([("book", ASCENDING)])
    borrows.create_index([("borrowedAt", ASCENDING)])
