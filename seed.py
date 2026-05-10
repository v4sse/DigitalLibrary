from db import db, books, users, admins, reviews, book_copies, create_indexes
from bson import ObjectId

def seed():
    if books.count_documents({}) > 0:
        print("Database already seeded — skipping.")
        return

    admins.insert_many([
        {"username": "admin", "password": "admin123"},
        {"username": "librarian", "password": "lib456"},
    ])

    user_ids = {}
    user_data = [
        ("Gosho", "Gosho1234"),
        ("Tosho", "Tosho1234"),
        ("Pesho", "Pesho1234"),
        ("Tisho", "Tisho1234"),
    ]
    for name, pwd in user_data:
        result = users.insert_one({
            "username": name,
            "password": pwd,
            "borrowedBooks": []
        })
        user_ids[name] = result.inserted_id

    book_data = [
        {"name": "The Name of the Wind", "genre": "Fantasy", "author": "Patrick Rothfuss"},
        {"name": "The Wise Man's Fear", "genre": "Fantasy", "author": "Patrick Rothfuss"},
        {"name": "The Way of Kings", "genre": "Fantasy", "author": "Brandon Sanderson"},
        {"name": "Words of Radiance", "genre": "Fantasy", "author": "Brandon Sanderson"},
        {"name": "The Final Empire", "genre": "Fantasy", "author": "Brandon Sanderson"},

        {"name": "Dune", "genre": "Sci-Fi", "author": "Frank Herbert"},
        {"name": "Dune Messiah", "genre": "Sci-Fi", "author": "Frank Herbert"},
        {"name": "Foundation", "genre": "Sci-Fi", "author": "Isaac Asimov"},
        {"name": "I, Robot", "genre": "Sci-Fi", "author": "Isaac Asimov"},
        {"name": "The Martian", "genre": "Sci-Fi", "author": "Andy Weir"},

        {"name": "The Hound of the Baskervilles", "genre": "Mystery", "author": "Arthur Conan Doyle"},
        {"name": "A Study in Scarlet", "genre": "Mystery", "author": "Arthur Conan Doyle"},
        {"name": "And Then There Were None", "genre": "Mystery", "author": "Agatha Christie"},
        {"name": "Murder on the Orient Express", "genre": "Mystery", "author": "Agatha Christie"},

        {"name": "1984", "genre": "Classic", "author": "George Orwell"},
        {"name": "Animal Farm", "genre": "Classic", "author": "George Orwell"},
        {"name": "Brave New World", "genre": "Classic", "author": "Aldous Huxley"},
        {"name": "To Kill a Mockingbird", "genre": "Classic", "author": "Harper Lee"},

        {"name": "Sherlock Holmes", "genre": "Crime fiction", "author": "Arthur Conan Doyle"},

        {"name": "The Hobbit", "genre": "Fantasy", "author": "J.R.R. Tolkien"},
        {"name": "The Fellowship of the Ring", "genre": "Fantasy", "author": "J.R.R. Tolkien"},
        {"name": "The Two Towers", "genre": "Fantasy", "author": "J.R.R. Tolkien"},
        {"name": "The Return of the King", "genre": "Fantasy", "author": "J.R.R. Tolkien"},
        {"name": "The Silmarillion", "genre": "Fantasy", "author": "J.R.R. Tolkien"},

        {"name": "The Republic", "genre": "Philosophy", "author": "Plato"},
        {"name": "Candide", "genre": "Philosophy", "author": "Voltaire"},
        {"name": "Meditations", "genre": "Philosophy", "author": "Marcus Aurelius"},

        {"name": "Хобитът", "genre": "Fantasy", "author": "J.R.R. Tolkien"},
        {"name": "Властелинът на пръстените: Задругата на пръстена", "genre": "Fantasy", "author": "J.R.R. Tolkien"},
        {"name": "Властелинът на пръстените: Двете кули", "genre": "Fantasy", "author": "J.R.R. Tolkien"},
        {"name": "Властелинът на пръстените: Завръщането на краля", "genre": "Fantasy", "author": "J.R.R. Tolkien"},
        {"name": "Размисли", "genre": "Philosophy", "author": "Marcus Aurelius"},
        {"name": "Държавата", "genre": "Philosophy", "author": "Plato"},
        {"name": "Кандид", "genre": "Philosophy", "author": "Voltaire"},
        {"name": "Шерлок Холмс", "genre": "Crime fiction", "author": "Arthur Conan Doyle"},

        {"name": "Под игото", "genre": "Classic", "author": "Иван Вазов"},
        {"name": "Немили-недраги", "genre": "Classic", "author": "Иван Вазов"},
        {"name": "Чичовци", "genre": "Classic", "author": "Иван Вазов"},
        {"name": "Тютюн", "genre": "Classic", "author": "Димитър Талев"},
        {"name": "Железният светилник", "genre": "Classic", "author": "Димитър Талев"},
        {"name": "Ние, врабчетата", "genre": "Classic", "author": "Йордан Радичков"},
        {"name": "Ноев ковчег", "genre": "Philosophy", "author": "Йордан Радичков"}
    ]

    book_ids = books.insert_many(book_data).inserted_ids

    copies_data = [
        3,2,4,3,2,
        5,3,4,3,2,
        2,2,3,3,
        4,3,2,2,
        3,
        4,3,3,3,2,
        2,2,3,
        3,3,3,3,2,2,2,3,
        3,2,2,3,3,2,2
    ]

    book_copies.insert_many([
        {"book": bid, "copies": c, "borrowed": 0, "left": c}
        for bid, c in zip(book_ids, copies_data)
    ])

    borrows = [
        ("Gosho", 0),
        ("Gosho", 5),
        ("Tosho", 2),
        ("Tosho", 7),
        ("Pesho", 10),
        ("Pesho", 14),
        ("Tisho", 5),
        ("Tisho", 8),
    ]

    for username, book_idx in borrows:
        bid = book_ids[book_idx]
        users.update_one({"_id": user_ids[username]}, {"$push": {"borrowedBooks": bid}})
        book_copies.update_one({"book": bid}, {"$inc": {"borrowed": 1, "left": -1}})

    reviews.insert_many([
        {"book": book_ids[0], "user": user_ids["Gosho"], "rating": 5, "comment": "Absolutely enchanting prose."},
        {"book": book_ids[5], "user": user_ids["Gosho"], "rating": 4, "comment": "Epic world-building, slow start."},
        {"book": book_ids[2], "user": user_ids["Tosho"], "rating": 5, "comment": "One of the best fantasy epics ever."},
        {"book": book_ids[7], "user": user_ids["Tosho"], "rating": 4, "comment": "A classic, though a bit dated."},
        {"book": book_ids[0], "user": user_ids["Tosho"], "rating": 4, "comment": "Loved the magic system."},
        {"book": book_ids[10], "user": user_ids["Pesho"], "rating": 3, "comment": "Good but predictable."},
        {"book": book_ids[14], "user": user_ids["Pesho"], "rating": 5, "comment": "Terrifying and relevant."},
        {"book": book_ids[5], "user": user_ids["Pesho"], "rating": 5, "comment": "A masterpiece of science fiction."},
        {"book": book_ids[8], "user": user_ids["Tisho"], "rating": 4, "comment": "Thought-provoking short stories."},
        {"book": book_ids[14], "user": user_ids["Tisho"], "rating": 4, "comment": "Chilling. Orwell was a prophet."},
        {"book": book_ids[12], "user": user_ids["Gosho"], "rating": 5, "comment": "Christie at her absolute best."},
        {"book": book_ids[15], "user": user_ids["Tosho"], "rating": 3, "comment": "Decent allegory, short read."},

        {"book": book_ids[35], "user": user_ids["Gosho"], "rating": 5, "comment": "Много силен роман и много важен за българската литература."},
        {"book": book_ids[36], "user": user_ids["Tosho"], "rating": 4, "comment": "Кратка, но много въздействаща книга."},
        {"book": book_ids[37], "user": user_ids["Pesho"], "rating": 4, "comment": "Иронична и доста забавна!"},
        {"book": book_ids[38], "user": user_ids["Tisho"], "rating": 5, "comment": "Тежък роман."},
        {"book": book_ids[39], "user": user_ids["Gosho"], "rating": 5, "comment": "Много добра история"},
        {"book": book_ids[40], "user": user_ids["Tosho"], "rating": 5, "comment": "Уж детска книга, но всъщност е умна и забавна."},
        {"book": book_ids[41], "user": user_ids["Pesho"], "rating": 4, "comment": "Странна и интересна книга."},
        {"book": book_ids[31], "user": user_ids["Tisho"], "rating": 5, "comment": "Добра храна за размисъл."},
        {"book": book_ids[32], "user": user_ids["Gosho"], "rating": 4, "comment": "Доста добре описва действителността"},
        {"book": book_ids[33], "user": user_ids["Pesho"], "rating": 4, "comment": "Кратка, иронична и доста остра книга."}
    ])

    create_indexes()

    print("\nDone! Test credentials:")
    print("  Users  — Gosho/Gosho1234, Tosho/Tosho1234, Pesho/Pesho1234, Tisho/Tisho1234")
    print("  Admins — admin/admin123, librarian/lib456")
    print(f"  Books inserted: {len(book_ids)}")
