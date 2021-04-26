import os
import socket
import threading
import pickle
import logging
import sys



# Global variable that mantain client's connections
connections = []
login = False


def handle_user_connection(server: socket.socket, connection: socket.socket, address: str) -> None:
    '''
        Get user connection in order to keep receiving their messages and
        sent to others users/connections.
    '''
    global login
    while True:
        try:
            # Get client message
            msg = connection.recv(4096)
            # If no message is received, there is a chance that connection has ended
            # so in this case, we need to close connection and remove it from connections list.
            if msg:

                if pickle.loads(msg) != "":
                    #Log message sent by user
                    print(f'({address[0]}:{address[1]}) - {pickle.loads(msg)}')

                    #Build message format and broadcast to users connected on server
                    msg_to_send = f'From ({address[0]}:{address[1]}) - {pickle.loads(msg)}'
                    broadcast(msg_to_send, connection)

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
                logging.error('Error broadcasting message: {e}')
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


def main():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    output_file_handler = logging.FileHandler("irc_server.log")
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

    LISTENING_PORT = int(sys.argv[1])  # default port

    try:
        # Create server and specifying that it can only handle 4 connections by time!
        socket_instance = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_instance.bind(('', LISTENING_PORT))
        socket_instance.listen(2)
        os.system('cls' if os.name == 'nt' else 'clear')
        logging.info(f'Server running with port {LISTENING_PORT}')

        while True:
            # Accept client connection
            socket_connection, address = socket_instance.accept()
            # Add client connection to connections list
            connections.append(socket_connection)
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
        remove_connection(socket_connection)
    finally:
        # In case of any problem we clean all connections and close the server connection
        if len(connections) > 0:
            for conn in connections:
                remove_connection(conn)

        socket_instance.close()


if __name__ == "__main__":
    main()
