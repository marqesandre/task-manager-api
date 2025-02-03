
def create_task(db, task_data):
    db.tasks.insert_one(task_data)

def get_tasks(db, user_id):
    return list(db.tasks.find({"user_id": user_id}))

def update_task(db, task_id, updates):
    db.tasks.update_one({"_id": task_id}, {"$set": updates})

def delete_task(db, task_id):
    db.tasks.delete_one({"_id": task_id})