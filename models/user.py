
# ...existing code...
def create_user(db, user_data):
    # ...existing code...
    db.users.insert_one(user_data)

def find_user_by_email(db, email):
    return db.users.find_one({"email": email})

def update_password(db, email, hashed_password):
    db.users.update_one({"email": email}, {"$set": {"password": hashed_password}})
# ...existing code...