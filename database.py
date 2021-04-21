import itertools
import logging
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
discount = db.discount
order = db.order


def encrypt_password(str_pwd):
    return bcrypt.hashpw(str_pwd.encode('utf-8'), bcrypt.gensalt())


def is_account_exists(acc):
    username = acc['username']
    if user.find_one({'username': username}) is None:
        return False
    else:
        return True


def cal_rest_rating(rating):
    sum_rating = sum(rating.values())
    if sum_rating > 0:
        return (5*rating['five'] + 4*rating['four'] + 3*rating['three'] + 2*rating['two'] + 1*rating['one']) / sum_rating
    else:
        return 0

def register(user_data):
    if not is_account_exists(user_data):
        try:
            date = datetime.now()
            if user_data['restaurant']:
                user_data
            else:
                user_data['isNewUser'] = True
                user_data['favRest'] = []

            user_data['password'] = encrypt_password(user_data['password'])
            user_data['createDate'] = date

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
    if userdata and data['username'] == userdata['username']:
        if bcrypt.checkpw(data['password'].encode(), userdata['password']):
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
        data['rating'] = {
            "five": 0,
            "four": 0,
            "three": 0,
            "two": 0,
            "one": 0
        }
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
            result['rating'] = "★ " + "{:.1f}".format(cal_rest_rating(result['rating']))
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
            x['rating'] = cal_rest_rating(x['rating'])
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


def user_rest_menu(data):
    try:
        rest_data = restaurant.find_one({'name': data['rest_name']})
        if rest_data:
            rest_category = category.find({'rest_id': rest_data['_id']})
            rest_cate = {}
            for c in rest_category:
                del c['_id']
                del c['rest_id']
                rest_cate.update({c.get('category_id'): c.get('name')})

            result = menu.find({'rest_id': rest_data['_id']}).sort([('status', pymongo.DESCENDING)])

            category_menu = []

            for _, _category in itertools.groupby(result, key=lambda item: item['category_id']):
                category_menu.append(list(_category))
            all_data = ['user-rest-menu']

            for cate in category_menu:
                all_data.append(Separator('[' + str(rest_cate.get(cate[0]['category_id'])) + ']'))
                for _menu in cate:
                    if not _menu['status']:
                        _menu['disabled'] = 'unavailable'
                    _menu['name'] = _menu['name'] + " (฿" + str(_menu['price']) + ")"
                    all_data.append(_menu)

            return all_data
        else:
            logging.error('Get restaurant menu failed, because restaurant not found.')
            return 'err_rest_menu'
    except Exception as e:
        logging.error(f'Get restaurant menu failed, because {e}')
        return False


def apply_promo_code(data):
    try:
        user_data = user.find_one({'username': data['username']})
        discount_data = discount.find_one({'code': data['code']})
        if discount_data['status']:
            if discount_data['newuser']:
                is_new_user = user_data['isNewUser']
                if is_new_user:
                    _data = {}
                    _data['promo-type'] = discount_data['type']
                    _data['value'] = discount_data['value']
                    logging.info(f"User ({user_data['_id']}) using promo code ({discount_data['code']})")
                    return _data
                else:
                    return False
            else:
                _data = {}
                _data['promo-type'] = discount_data['type']
                _data['value'] = discount_data['value']
                logging.info(f"User ({user_data['_id']}) using promo code ({discount_data['code']})")
                return _data
        else:
            return False

    except Exception as e:
        logging.error(f'Apply promo code failed, because {e}')
        return False


def order_confirm(data):
    try:
        user_data = user.find_one_and_update({"username": data['username'], "isNewUser": True},
                                        {'$set': {'isNewUser': False}},
                                        return_document=ReturnDocument.AFTER)
        date = datetime.now()

        data['createDate'] = date
        data['status'] = 0
        data['rated'] = False
        order_id = order.insert_one(data).inserted_id
        if order_id:
            if user_data:
                logging.info(f"set user ({data['username']}) status to old user.")
            logging.info(f"New order created with id: ({order_id}), by user ({data['username']})")
            return True
    except Exception as e:
        logging.error(f'Order create failed: because {e}')
        return False


def order_history(data):
    try:
        user_data = user.find_one({'username': data['username']})
        if user_data:
            _data = []
            _data.append('user-order-list')
            for _order in order.find({'username': data['username']}).sort([('status', pymongo.ASCENDING)]):
                del _order['username']

                _order['_id'] = _order['_id']

                if _order['status'] == 0:
                    _order['status'] = 'waiting⏳'
                elif _order['status'] == 1:
                    _order['status'] = 'cooking👨‍🍳'
                elif _order['status'] == 2:
                    _order['status'] = 'finish✅'
                elif _order['status'] == 3:
                    _order['status'] = 'cancel❌'

                menu = ""
                for _o in _order['menu']:
                    menu = menu + _o + "\n"
                _order['menu'] = menu

                _order['createDate'] = _order['createDate'].strftime("%d/%m/%Y\n%H:%M:%S")
                #_data.append(list(_order.values()))

                _order['RESTAURANT'] = _order.pop('rest_name')
                _order['MENU LIST'] = _order.pop('menu')
                _order['PRICE'] = _order.pop('price')
                _order['COMMENT'] = _order.pop('comment')
                _order['CREATE AT'] = _order.pop('createDate')
                _order['ORDER STATUS'] = _order.pop('status')


                temp = []
                for k, i in _order.items():
                    temp.append([k, i])

                _data.append(temp)

            logging.info(f"Send orders list to user ({data['username']})")
            if len(_data) > 1:
                return _data
            else:
                return False
        else:
            logging.error('Get order failed, because order not found.')
            return False
    except Exception as e:
        logging.error(f'Get order failed, because {e}')
        return False


def cancel_order(data):
    try:
        result = order.find_one_and_update({"_id": data['order_id'], "username": data['username'], "status": 0},
                                        {'$set': {'status': 3}},
                                        return_document=ReturnDocument.AFTER)
        if result:
            return True
        else:
            logging.error(f'Cancel order failed, because order not found.')
            return False
    except Exception as e:
        logging.error(f'Cancel order failed, because {e}')
        return False


def view_order(data):
    try:
        user_data = user.find_one({'username': data['username']})
        if user_data:
            _data = []
            _data.append('user-order')
            for _order in order.find({'username': data['username'], '_id': data['order_id']}).sort([('status', pymongo.ASCENDING)]):
                del _order['username']

                _order['_id'] = _order['_id']

                if _order['status'] == 0:
                    _order['status'] = 'waiting⏳'
                elif _order['status'] == 1:
                    _order['status'] = 'cooking👨‍🍳'
                elif _order['status'] == 2:
                    _order['status'] = 'finish✅'
                elif _order['status'] == 3:
                    _order['status'] = 'cancel❌'

                menu = ""
                for _o in _order['menu']:
                    menu = menu + _o + "\n"
                _order['menu'] = menu

                _order['createDate'] = _order['createDate'].strftime("%d/%m/%Y\n%H:%M:%S")
                #_data.append(list(_order.values()))

                _order['RESTAURANT'] = _order.pop('rest_name')
                _order['MENU LIST'] = _order.pop('menu')
                _order['PRICE'] = _order.pop('price')
                _order['COMMENT'] = _order.pop('comment')
                _order['CREATE AT'] = _order.pop('createDate')
                _order['ORDER STATUS'] = _order.pop('status')


                temp = []
                for k, i in _order.items():
                    temp.append([k, i])

                _data.append(temp)

            logging.info(f"Send order to user ({data['username']})")
            if len(_data) > 1:
                return _data
            else:
                return False
        else:
            logging.error('Get order failed, because order not found.')
            return False
    except Exception as e:
        logging.error(f'Get order failed, because {e}')
        return False


def rate_order(data):
    try:
        dict_number = {1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five'}
        rating_field = "rating." + dict_number.get(data['rating'])
        result = order.find_one_and_update({"_id": data['order_id'], "username": data['username'], "rated": False, "status": 2},
                                        {'$set': {'rated': True}},
                                        return_document=ReturnDocument.AFTER)
        if result:
            _result = restaurant.find_one_and_update({"name": result['rest_name']},
                                        {'$inc': {rating_field: 1}},
                                        return_document=ReturnDocument.AFTER)
            if _result:
                logging.info(f"The user ({data['username']}) rated a restaurant.")
                return True
            else:
                logging.error(f'Rate order failed, because restaurant not found.')
                return False
        else:
            logging.error(f'Rate order failed, because order not found.')
            return False
    except Exception as e:
        logging.error(f'Rate order failed, because {e}')
        return False


