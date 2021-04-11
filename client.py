import os
import socket
import sys
import threading
import pickle
import database as db
from ansimarkup import ansiprint as print

isLogin = False
username = ""
error = "\n<bold,,red><fg #FFFFFF>\U0000274CERROR</fg #FFFFFF></bold,,red>"
success = "\n<bold,,green><fg #000000>\U00002705SUCCESS</fg #000000></bold,,green>"
connect = "\n<bold,,green><fg #000000>\U00002705CONNECTED</fg #000000></bold,,green>"
disconnect = "\n<bold,,red><fg #000000>\U0000274CDISCONNECTED</fg #000000></bold,,red>"
tips = "\n<bold><fg #000000><bg #F4D03F>\U0001F4A1TIPS</bg #F4D03F></fg #000000></bold>"

def handle_messages(connection: socket.socket):
    #Receive messages sent by the server and display them to user
    global isLogin
    global username
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
                            isLogin = False
                            connection.close()

                    elif decode_msg['type'] == 'success':
                        send_msg = decode_msg['msg']
                        print(success + " " + send_msg)
                        if decode_msg['msg'] == 'Login Successfully.':
                            os.system('cls' if os.name == 'nt' else 'clear')
                            print('<bold><fg #ffffff><bg #000000>'+'\n\U0001F44BHi, '+username.upper()+'! are you hungry?\n'+'</bg #000000></fg #ffffff></bold>')
                            print(tips + " " + "Type `/exit` to terminate program.")
                            print(tips + " " + "Type `/help` to see all commands.")
                            print()
                            isLogin = True

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
            #print(disconnect+' by server.')
            connection.close()
            break


def main() -> None:
    customPort = int(input('Input port number(4 digits): '))
    host = "127.0.0.1"
    port = customPort
    global isLogin
    global connect
    global disconnect
    global username
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

        while True:
            if isLogin:
                msg = input(username.upper() + '> ')
                if msg.lower() == '/exit':
                    break
                elif msg.lower() == '/help':
                    get_commands()
                elif msg.lower() == '/help rest':
                    get_rest_commands()
                elif msg.lower()[:6] == '/rest ':
                    rest_command(msg, socket_instance)
                else:
                    print(f'<red>Unknown the `{msg}` command.</red>')

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


def get_commands():
    cmd = [
        {'command': '/help', 'desc': 'see all commands.'},
        {'command': '/exit', 'desc': 'disconnect from server & exit program'},
        {'command': '/rest', 'desc': 'the commands for restaurant.\n\tusing `<b><fg #1BF4FF>/help rest</fg #1BF4FF></b>` to see more restaurant commands.'},
        {'command': '/user', 'desc': 'the commands for user.\n\tusing `<b><fg #1BF4FF>/help user</fg #1BF4FF></b>` to see more user commands.'}
    ]
    for c in cmd:
        print('<b><fg #1BF4FF>' + c['command'] + '</fg #1BF4FF></b>' + "\t" + c['desc'])


def get_rest_commands():
    cmd = [
        {'command': '/rest setup', 'desc': 'add restaurant into system. (for first time only)'},
        {'command': '/rest edit <name/phone/rest_type> <value>', 'desc': 'edit restaurant information.'},
        {'command': '/rest open', 'desc': 'open restaurant'},
        {'command': '/rest close', 'desc': 'close restaurant.'}
    ]
    for c in cmd:
        print('<b><fg #1BF4FF>' + c['command'] + '</fg #1BF4FF></b>' + "\t" + c['desc'])


def rest_command(cmd: str, connection: socket.socket):
    global username
    if cmd.lower() == '/rest setup':
        AddRestaurantData(connection)
    elif cmd[:11].lower() == '/rest edit ':
        data = {}
        data['username'] = username
        _cmd = cmd.split()
        if _cmd[2].lower() == 'name':
            data['type'] = 'edit-rest-name'
            data['value'] = _cmd[3]
            connection.send(pickle.dumps(data))
        elif _cmd[2].lower() == 'phone':
            data['type'] = 'edit-rest-phone'
            data['value'] = _cmd[3]
            connection.send(pickle.dumps(data))
        elif _cmd[2].lower() == 'rest_type':
            data['type'] = 'edit-rest-type'
            data['value'] = _cmd[3]
            connection.send(pickle.dumps(data))
        else:
            print(f'<red>Unknown the `{_cmd[2]}` field.</red>')
    elif cmd.lower() == '/rest open':
        rest_open(connection)
    elif cmd.lower() == '/rest close':
        rest_close(connection)
    else:
        print(f'<red>Unknown the `{cmd}` command.</red>')


def rest_open(connection: socket.socket):
    global username
    data = {}
    data['username'] = username
    data['type'] = 'open-rest'
    connection.send(pickle.dumps(data))


def rest_close(connection: socket.socket):
    global username
    data = {}
    data['username'] = username
    data['type'] = 'close-rest'
    connection.send(pickle.dumps(data))


if __name__ == "__main__":
    main()
