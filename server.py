import os
import socket
import subprocess
import threading
import database as db
import pickle
import logging
import sys

# Global variable that mantain client's connections
connections = {}
login = False
account = {}
irc_list = {}
LISTENING_PORT = 6789


def handle_user_connection(server: socket.socket, connection: socket.socket, address: str) -> None:
    '''
        Get user connection in order to keep receiving their messages and
        sent to others users/connections.
    '''
    global login
    global irc_list
    global LISTENING_PORT
    while True:
        try:
            # Get client message
            msg = connection.recv(4096)
            # If no message is received, there is a chance that connection has ended
            # so in this case, we need to close connection and remove it from connections list.
            if msg:
                while not login:
                    account = pickle.loads(msg)

                    if type(account) == dict:
                        if account['type'] == 'login':
                            del account['type']
                            if db.login(account):
                                if account['username'] in connections.values():
                                    res = packed_respond('err', 'Duplicate login, please logout and try again.')
                                    connection.send(pickle.dumps(res))
                                    remove_connection(connection)
                                else:
                                    res = packed_respond('success', 'Login Successfully.')
                                    res['isAdmin'] = db.is_admin_account(account)
                                    connection.send(pickle.dumps(res))
                                    if connection in connections.keys():
                                        connections[connection] = account['username']
                                        logging.info(f'{connections[connection]} logged in, with {address[0]+":"+str(address[1])}')
                                    login = True
                            else:
                                res = packed_respond('err', 'Login Fail.')
                                connection.send(pickle.dumps(res))
                        elif account['type'] == 'reg':
                            del account['type']
                            if db.register(account):
                                res = packed_respond('success', 'Register Successfully.')
                                res['isAdmin'] = db.is_admin_account(account)
                                connection.send(pickle.dumps(res))
                                if connection in connections.keys():
                                    connections[connection] = account['username']
                                    logging.info(f'{connections[connection]} logged in, with {address[0]+":"+str(address[1])}')
                                login = True
                            else:
                                res = packed_respond('err', 'Register Fail.')
                                connection.send(pickle.dumps(res))
                        else:
                            connection.send(pickle.dumps('failed'))

                msg_decode = pickle.loads(msg)
                #print(msg_decode)
                if type(msg_decode) == dict:
                    if msg_decode['type'] == 'add rest':
                        del msg_decode['type']
                        if db.check_restaurant_account(msg_decode['username']):
                            result = db.add_restaurant_data(msg_decode)
                            if result == 'err_rest':
                                res = packed_respond('err', 'Duplicate restaurant\'s name.')
                                connection.send(pickle.dumps(res))
                            elif result == 'success_rest':
                                res = packed_respond('success', 'Setting up restaurant successfully.')
                                connection.send(pickle.dumps(res))
                        else:
                            res = packed_respond('err', 'Your account type is not restaurant.')
                            connection.send(pickle.dumps(res))
                    elif msg_decode['type'] == 'open-rest' or msg_decode['type'] == 'close-rest':
                        if db.check_restaurant_account(msg_decode['username']):
                            result = db.open_close_restaurant(msg_decode)
                            if result == 'err_user_not_found':
                                res = packed_respond('err', 'Open/close restaurant failed.')
                                connection.send(pickle.dumps(res))
                            elif result == 'success_open':
                                res = packed_respond('success', 'Restaurant opened.')
                                connection.send(pickle.dumps(res))
                            elif result == 'success_close':
                                res = packed_respond('success', 'Restaurant closed.')
                                connection.send(pickle.dumps(res))
                        else:
                            res = packed_respond('err', 'Your account type is not restaurant.')
                            connection.send(pickle.dumps(res))
                    elif msg_decode['type'] == 'edit-rest-name' or msg_decode['type'] == 'edit-rest-phone' or msg_decode['type'] == 'edit-rest-type':
                        if db.check_restaurant_account(msg_decode['username']):
                            result = db.update_restaurant(msg_decode)
                            if result == 'err_user_not_found':
                                res = packed_respond('err', 'Update restaurant failed.')
                                connection.send(pickle.dumps(res))
                            elif result == 'success_rest_name':
                                res = packed_respond('success', 'Restaurant name updated.')
                                connection.send(pickle.dumps(res))
                            elif result == 'success_rest_phone':
                                res = packed_respond('success', 'Restaurant phone updated.')
                                connection.send(pickle.dumps(res))
                            elif result == 'success_rest_type':
                                res = packed_respond('success', 'Restaurant type updated.')
                                connection.send(pickle.dumps(res))
                        else:
                            res = packed_respond('err', 'Your account type is not restaurant.')
                            connection.send(pickle.dumps(res))
                    elif msg_decode['type'] == 'edit-user-phone':
                        if db.update_user(msg_decode):
                            res = packed_respond('success', 'Your account phone number is updated.')
                            connection.send(pickle.dumps(res))
                        else:
                            res = packed_respond('err', 'Update phone number failed.')
                            connection.send(pickle.dumps(res))

                    elif msg_decode['type'] == 'add-category':
                        del msg_decode['type']
                        if db.check_restaurant_account(msg_decode['username']):
                            result = db.add_category(msg_decode)
                            if result == 'err_add_cate':
                                res = packed_respond('err', 'Add category to restaurant failed.')
                                connection.send(pickle.dumps(res))
                            elif result == 'success_add_cate':
                                res = packed_respond('success', 'Category created.')
                                connection.send(pickle.dumps(res))
                        else:
                            res = packed_respond('err', 'Your account type is not restaurant.')
                            connection.send(pickle.dumps(res))

                    elif msg_decode['type'] == 'remove-category':
                        del msg_decode['type']
                        if db.check_restaurant_account(msg_decode['username']):
                            result = db.remove_category(msg_decode)
                            if result == 'err_remove_cate':
                                res = packed_respond('err', 'Remove category failed.')
                                connection.send(pickle.dumps(res))
                            elif result == 'success_remove_cate':
                                res = packed_respond('success', 'Category removed.')
                                connection.send(pickle.dumps(res))
                        else:
                            res = packed_respond('err', 'Your account type is not restaurant.')
                            connection.send(pickle.dumps(res))

                    elif msg_decode['type'] == 'edit-category':
                        del msg_decode['type']
                        if db.check_restaurant_account(msg_decode['username']):
                            result = db.update_category(msg_decode)
                            if result == 'err_edit_cate':
                                res = packed_respond('err', 'Update category failed.')
                                connection.send(pickle.dumps(res))
                            elif result == 'success_edit_cate':
                                res = packed_respond('success', 'Category updated.')
                                connection.send(pickle.dumps(res))
                        else:
                            res = packed_respond('err', 'Your account type is not restaurant.')
                            connection.send(pickle.dumps(res))

                    elif msg_decode['type'] == 'add-menu':
                        del msg_decode['type']
                        if db.check_restaurant_account(msg_decode['username']):
                            result = db.add_menu(msg_decode)
                            if result == 'err_add_menu':
                                res = packed_respond('err', 'Add menu to restaurant failed.')
                                connection.send(pickle.dumps(res))
                            elif result == 'success_add_menu':
                                res = packed_respond('success', 'Menu created.')
                                connection.send(pickle.dumps(res))
                        else:
                            res = packed_respond('err', 'Your account type is not restaurant.')
                            connection.send(pickle.dumps(res))

                    elif msg_decode['type'] == 'remove-menu':
                        del msg_decode['type']
                        if db.check_restaurant_account(msg_decode['username']):
                            result = db.remove_menu(msg_decode)
                            if result == 'err_remove_menu':
                                res = packed_respond('err', 'Remove menu failed.')
                                connection.send(pickle.dumps(res))
                            elif result == 'success_remove_menu':
                                res = packed_respond('success', 'Menu removed.')
                                connection.send(pickle.dumps(res))
                        else:
                            res = packed_respond('err', 'Your account type is not restaurant.')
                            connection.send(pickle.dumps(res))

                    elif msg_decode['type'] == 'edit-menu':
                        del msg_decode['type']
                        if db.check_restaurant_account(msg_decode['username']):
                            result = db.update_menu(msg_decode)
                            if result == 'err_edit_menu':
                                res = packed_respond('err', 'Update menu failed.')
                                connection.send(pickle.dumps(res))
                            elif result == 'success_edit_menu':
                                res = packed_respond('success', 'Menu updated.')
                                connection.send(pickle.dumps(res))
                        else:
                            res = packed_respond('err', 'Your account type is not restaurant.')
                            connection.send(pickle.dumps(res))

                    elif msg_decode['type'] == 'rest-info':
                        del msg_decode['type']
                        if db.check_restaurant_account(msg_decode['username']):
                            result = db.rest_info(msg_decode)
                            if result == 'err_rest_info':
                                res = packed_respond('err', 'Get restaurant info failed.')
                                connection.send(pickle.dumps(res))
                            elif result['type'] == 'rest-info':
                                connection.send(pickle.dumps(result))
                        else:
                            res = packed_respond('err', 'Your account type is not restaurant.')
                            connection.send(pickle.dumps(res))

                    elif msg_decode['type'] == 'rest-category':
                        del msg_decode['type']
                        if db.check_restaurant_account(msg_decode['username']):
                            result = db.rest_category(msg_decode)
                            if result == 'err_rest_category':
                                res = packed_respond('err', 'Get restaurant category failed.')
                                connection.send(pickle.dumps(res))
                            elif result[0] == 'rest-category':
                                connection.send(pickle.dumps(result))
                        else:
                            res = packed_respond('err', 'Your account type is not restaurant.')
                            connection.send(pickle.dumps(res))

                    elif msg_decode['type'] == 'rest-menu':
                        del msg_decode['type']
                        if db.check_restaurant_account(msg_decode['username']):
                            result = db.rest_menu(msg_decode)
                            if result == 'err_rest_menu':
                                res = packed_respond('err', 'Get restaurant menu failed.')
                                connection.send(pickle.dumps(res))
                            elif result[0] == 'rest-menu':
                                connection.send(pickle.dumps(result))
                        else:
                            res = packed_respond('err', 'Your account type is not restaurant.')
                            connection.send(pickle.dumps(res))

                    elif msg_decode['type'] == 'all-rest':
                        del msg_decode['type']
                        result = db.get_all_restaurants()
                        if not result:
                            res = packed_respond('err', 'Get restaurant failed.')
                            connection.send(pickle.dumps(res))
                        elif result[0] == 'all-rest':
                            connection.send(pickle.dumps(result))

                    elif msg_decode['type'] == 'get-rest-by-name' or msg_decode['type'] == 'get-rest-by-menu' or msg_decode['type'] == 'get-rest-by-fav':
                        result = db.get_restaurants_by_condition(msg_decode)
                        if not result:
                            res = packed_respond('err', 'Get restaurant failed.')
                            connection.send(pickle.dumps(res))
                        elif result[0] == 'all-rest':
                            connection.send(pickle.dumps(result))

                    elif msg_decode['type'] == 'remove-fav-rest' or msg_decode['type'] == 'add-fav-rest':
                        result = db.update_user_favrest(msg_decode)
                        if not result:
                            res = packed_respond('err', 'Update favourite restaurant failed.')
                            connection.send(pickle.dumps(res))
                        else:
                            res = packed_respond('success', 'Your favourite restaurant updated.')
                            connection.send(pickle.dumps(res))

                    elif msg_decode['type'] == 'user-rest-menu':
                        del msg_decode['type']
                        result = db.user_rest_menu(msg_decode)
                        if not result:
                            res = packed_respond('err', 'Get restaurant menu failed.')
                            connection.send(pickle.dumps(res))
                        elif result[0] == 'user-rest-menu':
                            connection.send(pickle.dumps(result))

                    elif msg_decode['type'] == 'promo-code':
                        del msg_decode['type']
                        result = db.apply_promo_code(msg_decode)
                        if not result:
                            res = packed_respond('err', 'Can\'t applied promo code.')
                            connection.send(pickle.dumps(res))
                        elif type(result) == dict:
                            result['type'] = 'promo'
                            connection.send(pickle.dumps(result))

                    elif msg_decode['type'] == 'confirm-order':
                        del msg_decode['type']
                        result = db.order_confirm(msg_decode)
                        if not result:
                            res = packed_respond('err', 'Can\'t confirm your order, please try again later.')
                            connection.send(pickle.dumps(res))
                        else:
                            res = packed_respond('success', 'Order confirmed.')
                            connection.send(pickle.dumps(res))

                    elif msg_decode['type'] == 'order-history':
                        del msg_decode['type']
                        result = db.order_history(msg_decode)
                        if not result:
                            res = packed_respond('err', 'Order history not found.')
                            connection.send(pickle.dumps(res))
                        elif result[0] == 'user-order-list':
                            connection.send(pickle.dumps(result))

                    elif msg_decode['type'] == 'order-cancel':
                        del msg_decode['type']
                        result = db.cancel_order(msg_decode)
                        if not result:
                            res = packed_respond('err', 'Order cancel fail.')
                            connection.send(pickle.dumps(res))
                        else:
                            res = packed_respond('success', 'The order has been canceled.')
                            connection.send(pickle.dumps(res))

                    elif msg_decode['type'] == 'order-view':
                        del msg_decode['type']
                        result = db.view_order(msg_decode)
                        if not result:
                            res = packed_respond('err', 'Order not found.')
                            connection.send(pickle.dumps(res))
                        elif result[0] == 'user-order':
                            connection.send(pickle.dumps(result))

                    elif msg_decode['type'] == 'order-rate':
                        del msg_decode['type']
                        result = db.rate_order(msg_decode)
                        if not result:
                            res = packed_respond('err', 'Fail to rate your order.')
                            connection.send(pickle.dumps(res))
                        else:
                            res = packed_respond('success', 'Order rated.')
                            connection.send(pickle.dumps(res))

                    elif msg_decode['type'] == 'rest-order-view':
                        del msg_decode['type']
                        if db.check_restaurant_account(msg_decode['username']):
                            result = db.rest_view_order(msg_decode)
                            if not result:
                                res = packed_respond('err', 'Order not found.')
                                connection.send(pickle.dumps(res))
                            elif result[0] == 'rest-order':
                                connection.send(pickle.dumps(result))
                        else:
                            res = packed_respond('err', 'Your account type is not restaurant.')
                            connection.send(pickle.dumps(res))

                    elif msg_decode['type'] == 'rest-order-edit':
                        del msg_decode['type']
                        if db.check_restaurant_account(msg_decode['username']):
                            result = db.rest_edit_order(msg_decode)
                            if not result:
                                res = packed_respond('err', 'Order status update fail.')
                                connection.send(pickle.dumps(res))
                            else:
                                res = packed_respond('success', 'Order status updated.')
                                connection.send(pickle.dumps(res))
                        else:
                            res = packed_respond('err', 'Your account type is not restaurant.')
                            connection.send(pickle.dumps(res))

                    elif msg_decode['type'] == 'rest-order-sales':
                        if db.check_restaurant_account(msg_decode['username']):
                            result = db.rest_sales(msg_decode)
                            if not result:
                                res = packed_respond('err', 'Get restaurant order sales fail.')
                                connection.send(pickle.dumps(res))
                            else:
                                connection.send(pickle.dumps(result))
                        else:
                            res = packed_respond('err', 'Your account type is not restaurant.')
                            connection.send(pickle.dumps(res))

                    elif msg_decode['type'] == 'server-stop':
                        if db.is_admin_account(msg_decode):
                            broadcast("\n<bold,,red><fg #000000>\U0000274CSERVER STOPPED</fg #000000></bold,,red>",
                                      socket.socket)
                            if len(connections) > 0:
                                for key in list(connections):
                                    remove_connection(key)
                            server.close()
                        else:
                            res = packed_respond('err', 'You don\'t have permission.')
                            connection.send(pickle.dumps(res))

                    elif msg_decode['type'] == 'admin-broadcast':
                        if db.is_admin_account(msg_decode):
                            prefix = "\n<bold><bg #FF8BB2><fg #000000>💬SERVER</fg #000000></bg #FF8BB2></bold>"
                            msg = prefix + " " +msg_decode['msg']
                            broadcast(msg, socket.socket)
                        else:
                            res = packed_respond('err', 'You don\'t have permission.')
                            connection.send(pickle.dumps(res))

                    elif msg_decode['type'] == 'start-irc':
                        if db.is_admin_account(msg_decode):
                            if msg_decode['port'] not in irc_list.keys() and msg_decode['port'] != str(LISTENING_PORT):
                                prefix = "\n<bold><bg #FF8BB2><fg #000000>💬SERVER</fg #000000></bg #FF8BB2></bold>"
                                p = subprocess.Popen(f'python irc_server.py {msg_decode["port"]}',
                                                 creationflags=subprocess.CREATE_NEW_CONSOLE)
                                irc_list[msg_decode["port"]] = p
                                res = packed_respond('success', f'New IRC running with port {msg_decode["port"]}.')
                                connection.send(pickle.dumps(res))
                                if 'client1' in msg_decode.keys() and 'client2' in msg_decode.keys():
                                    for key, values in connections.items():
                                        if msg_decode['client1'] == values:
                                            whisper(f'{prefix} IRC Opened with port {msg_decode["port"]}.\nusing `/join irc <port>` to chat with {msg_decode["client2"]}.', key)
                                        if msg_decode['client2'] == values:
                                            whisper(f'{prefix} IRC Opened with port {msg_decode["port"]}.\nusing `/join irc <port>` to chat with {msg_decode["client1"]}.', key)
                            else:
                                res = packed_respond('err', 'This port is already running.')
                                connection.send(pickle.dumps(res))
                        else:
                            res = packed_respond('err', 'You don\'t have permission.')
                            connection.send(pickle.dumps(res))

                    elif msg_decode['type'] == 'stop-irc':
                        if db.is_admin_account(msg_decode):
                            if msg_decode['port'] in irc_list.keys():
                                irc_list[msg_decode['port']].kill()
                                del irc_list[msg_decode['port']]
                                res = packed_respond('success', f'IRC port {msg_decode["port"]} has stopped.')
                                connection.send(pickle.dumps(res))
                            else:
                                res = packed_respond('err', 'The port was not found in the running irc list.')
                                connection.send(pickle.dumps(res))
                        else:
                            res = packed_respond('err', 'You don\'t have permission.')
                            connection.send(pickle.dumps(res))

                    elif msg_decode['type'] == 'show-users':
                        if db.is_admin_account(msg_decode):
                            users = "Online users: "
                            for user in connections.values():
                                users = users + user + ", "
                            res = packed_respond('success', users[:-2])
                            connection.send(pickle.dumps(res))
                        else:
                            res = packed_respond('err', 'You don\'t have permission.')
                            connection.send(pickle.dumps(res))

                    elif msg_decode['type'] == 'stop-client':
                        if db.is_admin_account(msg_decode):
                            delete_key = None
                            for key, value in connections.items():
                                if value == msg_decode['client']:
                                    delete_key = key

                            if delete_key is not None:
                                remove_connection(delete_key)
                                res = packed_respond('success', f'Client that connected by {msg_decode["client"]} was stopped.')
                                connection.send(pickle.dumps(res))
                            else:
                                res = packed_respond('err', 'Client not found.')
                                connection.send(pickle.dumps(res))
                        else:
                            res = packed_respond('err', 'You don\'t have permission.')
                            connection.send(pickle.dumps(res))


                #if pickle.loads(msg) != "":
                    #Log message sent by user
                    #print(f'({address[0]}:{address[1]}) - {pickle.loads(msg)}')

                    # Build message format and broadcast to users connected on server
                    #msg_to_send = f'From ({address[0]}:{address[1]}) - {pickle.loads(msg)}'
                    #broadcast(msg_to_send, connection)

            # Close connection if no message was sent
            else:
                remove_connection(connection)
                break

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            logging.error(f'Error to handle user connection: {e}')
            logging.info(f'({address[0]}:{address[1]} disconnected)')
            remove_connection(connection)
            change_title()
            break


def packed_respond(restype: str, message: str):
    res = {}
    res['type'] = restype
    res['msg'] = message
    return res


def broadcast(message: str, connection: socket.socket) -> None:
    '''
        Broadcast message to all users connected to the server
    '''

    # Iterate on connections in order to send message to all client's connected
    for key, value in connections.items():
        if key != connection:
            try:
                # Sending message to client connection
                res = packed_respond('broadcast', message)
                key.send(pickle.dumps(res))

            # if it fails, there is a chance of socket has died
            except Exception as e:
                logging.error('Error broadcasting message: {e}')
                change_title()
                remove_connection(key)


def whisper(message: str, connection: socket.socket) -> None:
    '''
        Broadcast message to all users connected to the server
    '''

    # Iterate on connections in order to send message to all client's connected
    for key, value in connections.items():
        if key == connection:
            try:
                # Sending message to client connection
                res = packed_respond('broadcast', message)
                key.send(pickle.dumps(res))

            # if it fails, there is a chance of socket has died
            except Exception as e:
                logging.error('Error broadcasting message: {e}')
                change_title()
                remove_connection(key)


def remove_connection(conn: socket.socket) -> None:
    '''
        Remove specified connection from connections list
    '''

    # Check if connection exists on connections list
    if conn in connections.keys():
        # Close socket connection and remove connection from connections list
        conn.close()
        connections.pop(conn)



def main() -> None:
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    output_file_handler = logging.FileHandler("server.log")
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    output_file_handler.setFormatter(formatter)
    root.addHandler(handler)
    root.addHandler(output_file_handler)

    '''
        Main process that receive client's connections and start a new thread
        to handle their messages
    '''
    global login
    global account
    global connections
    global LISTENING_PORT

    useCustomPort = input('Do you want to setup port manually? (y/N): ')
    if (useCustomPort.lower() == 'y'):
        LISTENING_PORT = int(input('Input port number(4 digits): '))
    else:
        LISTENING_PORT = 6789  # default port

    try:
        # Create server and specifying that it can only handle 4 connections by time!
        socket_instance = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_instance.bind(('', LISTENING_PORT))
        socket_instance.listen(10)

        logging.info(f'Server running with port {LISTENING_PORT}')

        while True:
            # Accept client connection
            socket_connection, address = socket_instance.accept()
            # Add client connection to connections list
            connections[socket_connection] = 'guest'
            change_title()
            logging.info(f'({address[0]}:{address[1]} connected)')
            login = False
            account = {}
            # Start a new thread to handle client connection and receive it's messages
            # in order to send to others connections
            threading.Thread(target=handle_user_connection, args=[socket_instance, socket_connection, address]).start()


    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        logging.info(f'({address[0]}:{address[1]} disconnected.)')
        logging.error(f'An error has occurred when instancing socket: {e}')
        change_title()
        remove_connection(socket_connection)
    finally:
        # In case of any problem we clean all connections and close the server connection
        if len(connections) > 0:
            for key, value in connections.items():
                remove_connection(key)

        socket_instance.close()


def change_title():
    logging.info(str(len(connections)) + " connection(s)")
    os.system("title " + "(SERVER) " + str(len(connections)) + " connection(s)")


if __name__ == "__main__":
    main()
