import socket
import sys
import threading
import pickle
import database as db
from ansimarkup import ansiprint as print

login = False
username = ""
error = "\n<bold,black,red>\U0000274CERROR</bold,black,red>"
success = "\n<bold,black,green>\U00002705SUCCESS</bold,black,green>"
connect = "\n<bold,black,green>\U00002705CONNECTED</bold,black,green>"
disconnect = "\n<bold,black,red>\U0000274CDISCONNECTED</bold,black,red>"
tips = "\n<bold,black,><bg #F4D03F>\U0001F4A1TIPS</bg #F4D03F></bold,black,>"

def handle_messages(connection: socket.socket):
    #Receive messages sent by the server and display them to user
    global login
    global error
    global success
    global disconnect
    global tips
    while True:
        try:
            msg = connection.recv(1024)

            # If there is no message, there is a chance that connection has closed
            # so the connection will be closed and an error will be displayed.
            # If not, it will try to decode message in order to show to user.
            if msg:
                decode_msg = pickle.loads(msg)
                #print(decode_msg)

                if type(decode_msg) == dict:
                    if decode_msg['type'] == 'err':
                        send_msg = decode_msg['msg']
                        print(error + " " + send_msg)
                        if decode_msg['msg'] == 'Login Fail.':
                            login = False
                            connection.close()

                    elif decode_msg['type'] == 'success':
                        print()
                        send_msg = decode_msg['msg']
                        print(success + " " + send_msg)
                        if decode_msg['msg'] == 'Login Successfully.':
                            print(tips + " " + "Type 'exit' to terminate program.")
                            login = True

                # if isinstance(pickle.loads(msg), list):
                #     if 'menuId' in pickle.loads(msg)[0].keys():
                #         for menu in pickle.loads(msg):
                #             for title, value in menu.items():
                #                 print(f'{title}: {value}')

            else:
                connection.close()
                break

        except Exception as e:
            print(f'Error handling message from server: {e}')
            print(disconnect)
            connection.close()
            break


def main() -> None:
    customPort = int(input('Input port number(4 digits): '))
    host = "127.0.0.1"
    port = customPort
    global login
    global connect
    global disconnect
    try:
        socket_instance = socket.socket()
        socket_instance.connect((host, port))
        threading.Thread(target=handle_messages, args=[socket_instance]).start()
        print(connect)
        print("Client start with " + host + ":" + str(port))

        chk = input("Do you have an account? (y/N): ")
        if chk.lower() == 'y':
            Login(socket_instance)
        else:
            Register(socket_instance)

        while Login:
            while True:
                msg = input('>> ')
                if msg.lower() == 'exit':
                    break
                if msg.lower() == '--set rest':
                    AddRestaurantData(socket_instance)

                #socket_instance.send(pickle.dumps(msg))


            socket_instance.close(socket_instance)
        sys.exit()
        print(disconnect)

    except:
        #print('Error, Can\'t connect to server!')
        print(disconnect)
        socket_instance.close()
        sys.exit()


def Register(socket_instance):
    print('Register')
    account = {}
    account['type'] = 'reg'
    print('Register account for personal/restaurant?')
    print('Enter (1) for personal | (2) for restaurant')
    choice = int(input('>> '))
    if choice == 2:
        account['restaurant'] = True
    else:
        account['restaurant'] = False

    account['username'] = input('username: ')
    account['password'] = input('password: ')
    confirm_password = input('confirm password: ')
    account['phone'] = input('phone: ')
    if account['password'] == confirm_password:
        socket_instance.send(pickle.dumps(account))
    else:
        print('Password doesn\'t match')
        Register(socket_instance)


def Login(socket_instance):
    global username
    print('Login')
    account = {}
    account['type'] = 'login'
    account['username'] = input('username: ')
    account['password'] = input('password: ')
    username = account['username']
    socket_instance.send(pickle.dumps(account))


def AddRestaurantData(socket_instance):
    global username
    print('Added Restaurant data')
    rest = {}
    rest['type'] = 'add rest'
    rest['name'] = input('restaurant name: ')
    db.get_restaurant_type()
    rest['rest_type'] = input('restaurant type id: ')
    rest['phone'] = input('restaurant phone: ')
    rest['username'] = username
    socket_instance.send(pickle.dumps(rest))

if __name__ == "__main__":
    main()
