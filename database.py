from datetime import datetime, timezone
import pytz
import pymongo
import bcrypt

client = pymongo.MongoClient("mongodb://localhost:27017/?readPreference=primary&appname=MongoDB%20Compass&ssl=false")
db = client.FoodServices
user = db.user
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
            user_data['password'] = encrypt_password(user_data['password'])
            user_data['createDate'] = date.astimezone(th)
            user_data['isNewUser'] = True
            user_data['favRest'] = []
            user_id = user.insert_one(user_data).inserted_id
            print(f"New user created with id: ({user_id})")
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
