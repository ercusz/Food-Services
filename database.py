from datetime import datetime, timezone
import pytz
import pymongo
import bcrypt
from pymongo import ReturnDocument

client = pymongo.MongoClient("mongodb://localhost:27017/?readPreference=primary&appname=MongoDB%20Compass&ssl=false")
db = client.FoodServices
user = db.user
restaurant = db.restaurant
restaurant_type = db.restaurantType
salt = b'$2b$12$.oAv5kYzQ/bLcPlRVhtnHe'


def encrypt_password(str_pwd):
    return bcrypt.hashpw(str_pwd.encode('utf-8'), salt)


def is_account_exists(acc):
    username = acc['username']
    if user.find_one({'username': username}) is None:
        return False
    else:
        return True


def register(user_data):
    if not is_account_exists(user_data):
        try:
            th = pytz.timezone('Asia/Bangkok')
            date = datetime.now()
            if user_data['restaurant']:
                user_data
            else:
                user_data['isNewUser'] = True
                user_data['favRest'] = []

            user_data['password'] = encrypt_password(user_data['password'])
            user_data['createDate'] = date.astimezone(th)

            user_id = user.insert_one(user_data).inserted_id
            if user_data['restaurant']:
                print(f"New user created with id: ({user_id}), type = restaurant")
            else:
                print(f"New user created with id: ({user_id}), type = user")
            return True
        except Exception as e:
            print(f'Create account failed: because {e}')
            return False

    else:
        print('Create account failed, because duplicate account!')
        return False


def login(data):
    data['password'] = encrypt_password(data['password'])
    userdata = user.find_one(data)
    if userdata is not None and userdata['password'] == data['password']:
        print(f'{data["username"]} Logged in')
        return True
    else:
        print(f'Failed to logged in with username: {data["username"]}')
        return False


def check_restaurant_account(data):
    userdata = user.find_one({'username': data})
    if userdata['restaurant']:
        return True
    else:
        return False


def get_restaurant_type():
    for type in restaurant_type.find():
        print(f'ID: {type["type_id"]}, Name: {type["name"]}')


def add_restaurant_data(data):
    try:
        username = data['username']
        del data['username']
        data['rating'] = 0
        if not restaurant.find_one({'name': data['name']}):
            _id = restaurant.insert(data)
            rest = user.find_one_and_update({'username': username},
                                       {'$set': {'ownerOf': _id}},
                                        return_document = ReturnDocument.AFTER)
            print(f"New restaurant created with id: ({rest['_id']}), owner: ({username})")
            return 'success_rest'
        else:
            print('Create restaurant failed, because the restaurant name is duplicated.')
            return 'err_rest'
    except Exception as e:
        print(f'Create restaurant failed, because {e}')
        return False


