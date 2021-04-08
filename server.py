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
    global testmenu
    global testacc
    while True:
        try:
            # Get client message
            msg = connection.recv(1024)
            # If no message is received, there is a chance that connection has ended
            # so in this case, we need to close connection and remove it from connections list.
            if msg:
                while not login:
                    account = pickle.loads(msg)

                    if account['type'] == 'login':
                        del account['type']
                        if(db.login(account) == True):
                            connection.send(pickle.dumps('ok'))
                            login = True
                        else:
                            connection.send(pickle.dumps('failed'))
                    elif account['type'] == 'reg':
                        del account['type']
                        if (db.register(account) == True):
                            connection.send(pickle.dumps('ok'))
                            login = True
                        else:
                            connection.send(pickle.dumps('failed'))
                    else:
                        connection.send(pickle.dumps('failed'))

                if isinstance(pickle.loads(msg), str):
                    if pickle.loads(msg)[:6] == '--menu':
                        print(f'Sending menu to ({address[0]}:{address[1]})')
                        connection.send(pickle.dumps(testmenu))
                    else:
                        if pickle.loads(msg) != "":
                            # Log message sent by user
                            print(f'({address[0]}:{address[1]}) - {pickle.loads(msg)}')

                            # Build message format and broadcast to users connected on server
                            msg_to_send = f'From ({address[0]}:{address[1]}) - {pickle.loads(msg)}'
                            broadcast(msg_to_send, connection)

            # Close connection if no message was sent
            else:
                remove_connection(connection)
                break

        except Exception as e:
            #print(f'Error to handle user connection: {e}')
            print(f'({address[0]}:{address[1]} disconnected)')
            remove_connection(connection)
            break


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
        socket_instance.bind(('127.0.0.1', LISTENING_PORT))
        socket_instance.listen(4)

        print('Server running!')

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
        #print(f'An error has occurred when instancing socket: {e}')
    finally:
        # In case of any problem we clean all connections and close the server connection
        if len(connections) > 0:
            for conn in connections:
                remove_connection(conn)

        socket_instance.close()


if __name__ == "__main__":
    main()
