import socket
import threading
import database as db
import pickle

# Global variable that mantain client's connections
connections = []
connections_info = {}
login = False
account = {}


def handle_user_connection(connection: socket.socket, address: str) -> None:
    '''
        Get user connection in order to keep receiving their messages and
        sent to others users/connections.
    '''
    global login
    while True:
        try:
            # Get client message
            msg = connection.recv(1024)
            # If no message is received, there is a chance that connection has ended
            # so in this case, we need to close connection and remove it from connections list.
            if msg:
                while not login:
                    account = pickle.loads(msg)

                    if type(account) == dict:
                        if account['type'] == 'login':
                            del account['type']
                            if db.login(account):
                                res = packed_respond('success', 'Login Successfully.')
                                connection.send(pickle.dumps(res))
                                login = True
                            else:
                                res = packed_respond('err', 'Login Fail.')
                                connection.send(pickle.dumps(res))
                        elif account['type'] == 'reg':
                            del account['type']
                            if db.register(account):
                                res = packed_respond('success', 'Register Successfully.')
                                connection.send(pickle.dumps(res))
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
            print(f'Error to handle user connection: {e}')
            print(f'({address[0]}:{address[1]} disconnected)')
            remove_connection(connection)
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
    for client_conn in connections:
        if client_conn != connection:
            try:
                # Sending message to client connection
                client_conn.send(pickle.dumps(message))

            # if it fails, there is a chance of socket has died
            except Exception as e:
                print('Error broadcasting message: {e}')
                remove_connection(client_conn)


def remove_connection(conn: socket.socket) -> None:
    '''
        Remove specified connection from connections list
    '''

    # Check if connection exists on connections list
    if conn in connections:
        # Close socket connection and remove connection from connections list
        conn.close()
        connections.remove(conn)


def main() -> None:
    '''
        Main process that receive client's connections and start a new thread
        to handle their messages
    '''
    global login
    global account

    useCustomPort = input('Do you want to setup port manually? (y/N): ')
    if (useCustomPort.lower() == 'y'):
        LISTENING_PORT = int(input('Input port number(4 digits): '))
    else:
        LISTENING_PORT = 6789  # default port

    try:
        # Create server and specifying that it can only handle 4 connections by time!
        socket_instance = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_instance.bind(('', LISTENING_PORT))
        socket_instance.listen(4)

        print(f'Server running with port {LISTENING_PORT}')

        while True:
            # Accept client connection
            socket_connection, address = socket_instance.accept()
            # Add client connection to connections list
            connections.append(socket_connection)
            print(f'({address[0]}:{address[1]} connected)')
            login = False
            account = {}
            # Start a new thread to handle client connection and receive it's messages
            # in order to send to others connections
            threading.Thread(target=handle_user_connection, args=[socket_connection, address]).start()


    except Exception as e:
        print(f'({address[0]}:{address[1]} disconnected.)')
        print(f'An error has occurred when instancing socket: {e}')
    finally:
        # In case of any problem we clean all connections and close the server connection
        if len(connections) > 0:
            for conn in connections:
                remove_connection(conn)

        socket_instance.close()


if __name__ == "__main__":
    main()
