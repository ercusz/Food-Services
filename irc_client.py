import datetime
import socket, threading
import sys
import pickle
import time

username = ""

def handle_messages(connection: socket.socket):
    '''
        Receive messages sent by the server and display them to user
    '''

    while True:
        try:
            msg = connection.recv(4096)

            # If there is no message, there is a chance that connection has closed
            # so the connection will be closed and an error will be displayed.
            # If not, it will try to decode message in order to show to user.
            if msg:
                print()
                print(pickle.loads(msg))
                print()
            else:
                connection.close()
                break

        except Exception as e:
            print(f'Error handling message from server: {e}')
            connection.close()
            break

def main() -> None:
    global username
    '''
        Main process that start client connection to the server
        and handle it's input messages
    '''

    SERVER_ADDRESS = '127.0.0.1'
    SERVER_PORT = int(sys.argv[1])
    username = sys.argv[2]

    try:
        # Instantiate socket and start connection with server
        socket_instance = socket.socket()
        socket_instance.connect((SERVER_ADDRESS, SERVER_PORT))
        # Create a thread in order to handle messages sent by server
        threading.Thread(target=handle_messages, args=[socket_instance]).start()

        print('Connected to IRC!')
        print('Enter /exit to exit from IRC.')

        # Read user's input until it quit from chat and close connection
        while True:
            msg = input(f'{username.upper()}> ')

            if msg == '/exit':
                break
            elif msg == "" or msg == " ":
                continue
            else:
                t = time.localtime()
                time_str = time.strftime("%H:%M:%S", t)
                print(f'({time_str}) <ME> ' + msg)

            # Parse message to utf-8
            socket_instance.send(pickle.dumps(f' <{username.upper()}> '+msg))

        # Close connection with the server
        socket_instance.close()

    except Exception as e:
        print(f'Error connecting to server socket {e}')
        #socket_instance.close()


if __name__ == "__main__":
    main()
