import logging
import os
import sys
from PyInquirer import Separator
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
category = db.category
menu = db.menu


def encrypt_password(str_pwd):
    return bcrypt.hashpw(str_pwd.encode('utf-8'), bcrypt.gensalt())


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
                logging.info(f"New user created with id: ({user_id}), type = restaurant")
            else:
                logging.info(f"New user created with id: ({user_id}), type = user")
            return True
        except Exception as e:
            logging.error(f'Create account failed: because {e}')
            return False

    else:
        logging.error('Create account failed, because duplicate account!')
        return False


def login(data):
    userdata = user.find_one({'username': data['username']})
    if userdata is not None:
        if bcrypt.checkpw(data['password'].encode(), userdata['password']):
            print('Hello2')
            logging.info(f'{data["username"]} logged in.')
            return True
    else:
        logging.error(f'Failed to logged in with username: {data["username"]}.')
        return False


def check_restaurant_account(data):
    userdata = user.find_one({'username': data})
    if userdata['restaurant']:
        return True
    else:
        return False


def get_restaurant_type():
    for type in restaurant_type.find():
        logging.info(f'ID: {type["type_id"]}, Name: {type["name"]}')


def add_restaurant_data(data):
    try:
        username = data['username']
        del data['username']
        data['rating'] = 0
        data['open'] = False
        if not restaurant.find_one({'name': data['name']}):
            _id = restaurant.insert(data)
            rest = user.find_one_and_update({'username': username},
                                       {'$set': {'ownerOf': _id}},
                                        return_document = ReturnDocument.AFTER)
            logging.info(f"New restaurant created with id: ({rest['_id']}), owner: ({username})")
            return 'success_rest'
        else:
            logging.error('Create restaurant failed, because the restaurant name is duplicated.')
            return 'err_rest'
    except Exception as e:
        logging.error(f'Create restaurant failed, because {e}')
        return False


def open_close_restaurant(data):
    try:
        user_data = user.find_one({'username': data['username']})
        if user_data and data['type'] == 'open-rest':
            rest = restaurant.find_one_and_update({'_id': user_data['ownerOf']},
                                            {'$set': {'open': True}},
                                            return_document=ReturnDocument.AFTER)
            logging.info(f"Restaurant id: ({rest['_id']}) opened by owner: ({data['username']})")
            return 'success_open'
        elif user_data and data['type'] == 'close-rest':
            rest = restaurant.find_one_and_update({'_id': user_data['ownerOf']},
                                            {'$set': {'open': False}},
                                            return_document=ReturnDocument.AFTER)
            logging.info(f"Restaurant id: ({rest['_id']}) closed by owner: ({data['username']})")
            return 'success_close'
        else:
            logging.error('Open or close restaurant failed, because user not found.')
            return 'err_user_not_found'

    except Exception as e:
        logging.error(f'Open or close restaurant failed, because {e}')
        return False


def update_restaurant(data):
    try:
        user_data = user.find_one({'username': data['username']})
        if user_data and data['type'] == 'edit-rest-name':
            rest = restaurant.find_one_and_update({'_id': user_data['ownerOf']},
                                                  {'$set': {'name': data['value']}},
                                                  return_document=ReturnDocument.AFTER)
            logging.info(f"Restaurant id: ({rest['_id']}) name updated by owner: ({data['username']})")
            return 'success_rest_name'
        elif user_data and data['type'] == 'edit-rest-phone':
            rest = restaurant.find_one_and_update({'_id': user_data['ownerOf']},
                                                  {'$set': {'phone': data['value']}},
                                                  return_document=ReturnDocument.AFTER)
            logging.info(f"Restaurant id: ({rest['_id']}) phone updated by owner: ({data['username']})")
            return 'success_rest_phone'
        elif user_data and data['type'] == 'edit-rest-type':
            rest = restaurant.find_one_and_update({'_id': user_data['ownerOf']},
                                                  {'$set': {'rest_type': data['value']}},
                                                  return_document=ReturnDocument.AFTER)
            logging.info(f"Restaurant id: ({rest['_id']}) type updated by owner: ({data['username']})")
            return 'success_rest_type'
        else:
            logging.error('Restaurant update failed, because user not found.')
            return 'err_user_not_found'

    except Exception as e:
        logging.error(f'Restaurant update failed, because {e}')
        return False


def update_user(data):
    try:
        _user = user.find_one_and_update({'username': data['username']},
                                        {'$set': {'phone': data['value']}},
                                        return_document=ReturnDocument.AFTER)
        logging.info(f"User id: ({_user['_id']}) phone number updated.")
        return True
    except Exception as e:
        logging.error(f'User phone number update failed, because {e}')
        return False


def update_user_favrest(data):
    try:
        rest_data = restaurant.find_one({'name': data['value']})
        if data['type'] == 'remove-fav-rest':
            query = {"$pull": {"favRest": rest_data['_id']}}
        elif data['type'] == 'add-fav-rest':
            query = {'$push': {'favRest': rest_data['_id']}}
        _user = user.find_one_and_update({'username': data['username']},
                                         query, return_document=ReturnDocument.AFTER)
        logging.info(f"User id: ({_user['_id']}) favourite restaurant updated.")
        return True
    except Exception as e:
        logging.error(f'User favourite restaurant update failed, because {e}')
        return False


def add_category(data):
    try:
        username = data['username']
        del data['username']
        user_data = user.find_one({'username': username})
        if user_data:
            data['rest_id'] = user_data['ownerOf']
            cate_id = category.insert(data)
            logging.info(f"New category ({cate_id}) created in restaurant that owned by ({username}))")
            return 'success_add_cate'
        else:
            logging.error('Create category failed, because user not owner of restaurant.')
            return 'err_add_cate'
    except Exception as e:
        logging.error(f'Create category failed, because {e}')
        return False


def remove_category(data):
    try:
        username = data['username']
        del data['username']
        user_data = user.find_one({'username': username})
        if user_data:
            result = category.delete_one({"rest_id": user_data['ownerOf'], "category_id": data['category_id']})
            if result.deleted_count > 0:
                logging.info(f"Category removed in restaurant that owned by ({username}))")
                return 'success_remove_cate'
            else:
                logging.error("Remove category failed, because category not found.")
                return 'err_remove_cate'

        else:
            logging.error('Remove category failed, because user not owner of restaurant.')
            return 'err_remove_cate'
    except Exception as e:
        logging.error(f'Remove category failed, because {e}')
        return False


def update_category(data):
    try:
        username = data['username']
        del data['username']
        user_data = user.find_one({'username': username})
        if user_data:
            result = category.find_one_and_update({"rest_id": user_data['ownerOf'], "category_id": data['category_id']},
                                        {'$set': {data['field']: data['value']}},
                                        return_document=ReturnDocument.AFTER)
            logging.info(f"Category ({result['category_id']}) updated in restaurant that owned by ({username}))")
            return 'success_edit_cate'
    except Exception as e:
        logging.error(f'Update category failed, because {e}')
        return False


def add_menu(data):
    try:
        username = data['username']
        del data['username']
        user_data = user.find_one({'username': username})
        if user_data:
            data['status'] = False
            data['rest_id'] = user_data['ownerOf']
            menu_id = menu.insert(data)
            logging.info(f"New menu ({menu_id}) created in restaurant that owned by ({username}))")
            return 'success_add_menu'
        else:
            logging.error('Create menu failed, because user not owner of restaurant.')
            return 'err_add_menu'
    except Exception as e:
        logging.error(f'Create menu failed, because {e}')
        return False


def remove_menu(data):
    try:
        username = data['username']
        del data['username']
        user_data = user.find_one({'username': username})
        if user_data:
            result = menu.delete_one({"rest_id": user_data['ownerOf'], "name": data['name']})
            if result.deleted_count > 0:
                logging.info(f"{result.deleted_count} Menu removed in restaurant that owned by ({username}))")
                return 'success_remove_menu'
            else:
                logging.error("Remove menu failed, because category not found.")
                return 'err_remove_menu'

        else:
            logging.error('Remove menu failed, because user not owner of restaurant.')
            return 'err_remove_menu'
    except Exception as e:
        logging.error(f'Remove menu failed, because {e}')
        return False


def update_menu(data):
    try:
        username = data['username']
        del data['username']
        user_data = user.find_one({'username': username})
        if user_data:
            if data['name'] == 'all':
                result = menu.update_many({"rest_id": user_data['ownerOf']}, {'$set': {data['field']: data['value']}})

                logging.info(f"{result.modified_count} menu(s) updated in restaurant that owned by ({username}))")
                return 'success_edit_menu'
            else:
                result = menu.find_one_and_update({"rest_id": user_data['ownerOf'], "name": data['name']},
                                            {'$set': {data['field']: data['value']}},
                                            return_document=ReturnDocument.AFTER)
                logging.info(f"Menu ({result['category_id']}) updated in restaurant that owned by ({username}))")
                return 'success_edit_menu'
        else:
            logging.error('Update menu failed, because user not owner of restaurant.')
            return 'err_edit_menu'
    except Exception as e:
        logging.error(f'Update menu failed, because {e}')
        return False


def rest_info(data):
    try:
        username = data['username']
        del data['username']
        user_data = user.find_one({'username': username})
        if user_data:
            result = restaurant.find_one(user_data['ownerOf'])
            result['type'] = 'rest-info'
            rest_type = restaurant_type.find_one({'type_id': result['rest_type']})
            result['rest_type'] = "(" + result['rest_type'] + ") " + rest_type['name']
            result['rating'] = "★ " + "{:.1f}".format(result['rating'])
            logging.info(f"Send restaurant ({result['_id']}) info to user ({username})")
            return result
        else:
            logging.error('Get restaurant info failed, because user not owner of restaurant.')
            return 'err_rest_info'
    except Exception as e:
        logging.error(f'Get restaurant info failed, because {e}')
        return False


def rest_category(data):
    try:
        username = data['username']
        del data['username']
        user_data = user.find_one({'username': username})
        if user_data:
            data = ['rest-category']
            for x in category.find({'rest_id': user_data['ownerOf']}):
                data.append(list([x['category_id'], x['name']]))
            logging.info(f"Send restaurant ({user_data['ownerOf']}) category to user ({username})")
            return data
        else:
            logging.error('Get restaurant category failed, because user not owner of restaurant.')
            return 'err_rest_category'
    except Exception as e:
        logging.error(f'Get restaurant category failed, because {e}')
        return False


def rest_menu(data):
    try:
        username = data['username']
        del data['username']
        user_data = user.find_one({'username': username})
        if user_data:
            data = ['rest-menu']
            for x in menu.find({'rest_id': user_data['ownerOf']}):
                del x['_id']
                del x['rest_id']
                data.append(list(x.values()))
            logging.info(f"Send restaurant ({user_data['ownerOf']}) menu to user ({username})")
            return data
        else:
            logging.error('Get restaurant menu failed, because user not owner of restaurant.')
            return 'err_rest_menu'
    except Exception as e:
        logging.error(f'Get restaurant menu failed, because {e}')
        return False


def get_all_restaurants():
    try:
        result = restaurant.find().sort([('open', pymongo.DESCENDING)])
        data = ['all-rest', Separator('= Restaurant List =')]
        for x in result:
            if not x['open']:
                x['disabled'] = 'closed'
            data.append(x)
        return data
    except Exception as e:
        logging.error(f'Get restaurant failed, because {e}')
        return False


def get_restaurants_by_condition(data):
    try:
        result = []
        if data['type'] == 'get-rest-by-name':
            del data['type']
            result = restaurant.find({'name': {'$regex': data['value'], '$options': 'i'}}).sort([('open', pymongo.DESCENDING)])

        elif data['type'] == 'get-rest-by-menu':
            del data['type']
            result_menu = menu.find({'name': {'$regex': data['value'], '$options': 'i'}})
            list_result = []
            for x in result_menu:
                list_result.append(x['rest_id'])
            result = restaurant.find({'_id': {'$in': list_result}}).sort([('open', pymongo.DESCENDING)])

        elif data['type'] == 'get-rest-by-fav':
            del data['type']
            result_user = user.find_one({'username': data['username']})
            list_result = result_user['favRest']
            result = restaurant.find({'_id': {'$in': list_result}}).sort([('open', pymongo.DESCENDING)])

        data = ['all-rest', Separator('= Restaurant List ='), {'name': 'Select to exit restaurant or Press (ctrl+c)'}]
        for x in result:
            if not x['open']:
                x['disabled'] = 'closed'
            data.append(x)

        if len(data) <= 3:
            return []
        else:
            return data
    except Exception as e:
        logging.error(f'Get restaurant failed, because {e}')
        return False