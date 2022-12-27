from pymongo import MongoClient, DESCENDING
from werkzeug.security import generate_password_hash
from .user import User
from datetime import datetime
from bson import ObjectId
from chat_app import login_manager


client = MongoClient("mongodb+srv://urvesh:368viqzI268ZHSN2@cluster0.jp1c8nu.mongodb.net/?retryWrites=true&w=majority")

chat_db = client.get_database("chatDB")
users_collection = chat_db.get_collection("users")
rooms_collection = chat_db.get_collection("rooms")
room_members_collection = chat_db.get_collection("room_members")
messages_collection = chat_db.get_collection("message")

#user

def save_user(username, email, password):
    password_hash = generate_password_hash(password)
    users_collection.insert_one({'_id': username, 'email': email, 'password': password_hash})

def get_user(username):
    user_data = users_collection.find_one({'_id':username})
    return User(user_data['_id'], user_data['email'], user_data['password']) if user_data else None

def get_all_user():
    list = []
    for user in users_collection.find():
        list.append(user['_id'])
    return list

def get_user_email(email):
    user_data = users_collection.find_one({'email':email})
    return User(user_data['_id'], user_data['email'], user_data['password']) if user_data else None

def get_user_username(username):
    user_data = users_collection.find_one({'_id':username})
    return User(user_data['_id'], user_data['email'], user_data['password']) if user_data else None

@login_manager.user_loader
def load_user(username):
    user_data = users_collection.find_one({'_id':username})
    return User(user_data['_id'], user_data['email'], user_data['password']) if user_data else None


#rooms

def save_room(room_name, created_by):
    room_id = rooms_collection.insert_one({'name':room_name, 'created_by':created_by, 'created_at':datetime.now()}).inserted_id
    add_room_member(room_id, room_name, created_by, created_by, is_room_admin=True)
    return room_id

def update_room(room_id, room_name):
    rooms_collection.update_one({'_id':ObjectId(room_id)}, {'$set':{'name':room_name}})
    room_members_collection.update_many({'_id.room_id':ObjectId(room_id)},{'$set':{'room_name':room_name}})

def get_room(room_id):
    return rooms_collection.find_one({'_id': ObjectId(room_id)})

def delete_room(room_id):
    rooms_collection.delete_one({'_id':ObjectId(room_id)})
    room_members_collection.delete_many({'_id.room_id':ObjectId(room_id)})
    messages_collection.delete_many({'room_id':room_id})

def get_room_id_username(room_id,username):
    return rooms_collection.find_one({'_id':room_id,'created_by':username})

def add_room_member(room_id, room_name, username, added_by,  is_room_admin=False):
    room_members_collection.insert_one(
        {'_id': {'room_id': ObjectId(room_id), 'username': username}, 'room_name': room_name, 'added_by': added_by,
         'added_at': datetime.now(), 'is_room_admin': is_room_admin})

def add_room_members(room_id, room_name, usernames, added_by):
    room_members_collection.insert_many(
        [{'_id': {'room_id': ObjectId(room_id), 'username': username}, 'room_name': room_name, 'added_by': added_by,
          'added_at': datetime.now(), 'is_room_admin': False} for username in usernames])

def is_room_name_exist(room_name , usernames):
    list_of_user = []
    for username in usernames:
        if room_members_collection.find_one({'_id.username':username,'room_name':room_name}) is not None:
            list_of_user.append(username)
    return list_of_user

def remove_room_members(room_id, usernames):
    room_members_collection.delete_many(
        {'_id': {'$in': [{'room_id': ObjectId(room_id), 'username': username} for username in usernames]}})

def get_room_members(room_id):
    return list(room_members_collection.find({'_id.room_id': ObjectId(room_id)}))

def get_rooms_for_user(username):
    return list(room_members_collection.find({'_id.username': username}))

def is_room_member(room_id, username):
    return room_members_collection.count_documents({'_id': {'room_id': ObjectId(room_id), 'username': username}})

def is_room_admin(room_id, username):
    return room_members_collection.count_documents(
        {'_id': {'room_id': ObjectId(room_id), 'username': username}, 'is_room_admin': True})

#chat

def save_message(room_id, text, sender):
    messages_collection.insert_one({'room_id':room_id, 'text': text, 'sender': sender, 'created_at':datetime.now()})

def get_messages(room_id, page=0):
    MESSAGE_FETCH_LIMIT = 3
    offset = MESSAGE_FETCH_LIMIT * page
    messages = list(messages_collection.find({'room_id':room_id}).sort('_id',DESCENDING).limit(MESSAGE_FETCH_LIMIT).skip(offset))
    for message in messages:
        message['created_at'] = message['created_at'].strftime("%d %b, %H:%M")
    return messages[::-1]






