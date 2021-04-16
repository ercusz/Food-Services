from __future__ import print_function, unicode_literals

import time

from PyInquirer import style_from_dict, Token, prompt, Separator, Validator, ValidationError
from pprint import pprint
import regex
import os
import socket
import sys
import threading
import pickle
import database as db
from ansimarkup import ansiprint as print
from tabulate import tabulate

style = style_from_dict({
    Token.Separator: '#6C6C6C',
    Token.QuestionMark: '#FF9D00 bold',
    Token.Selected: '#5F819D',
    Token.Pointer: '#FF9D00 bold',
    Token.Instruction: '',  # default
    Token.Answer: '#f44336 bold',
    Token.Question: '',
})

all_rest = []
inf = True
isLogin = False
username = ""
error = "\n<bold,,red><fg #FFFFFF>\U0000274CERROR</fg #FFFFFF></bold,,red>"
success = "\n<bold,,green><fg #000000>\U00002705SUCCESS</fg #000000></bold,,green>"
connect = "\n<bold,,green><fg #000000>\U00002705CONNECTED</fg #000000></bold,,green>"
disconnect = "\n<bold,,red><fg #000000>\U0000274CDISCONNECTED</fg #000000></bold,,red>"
tips = "\n<bold><fg #000000><bg #F4D03F>\U0001F4A1TIPS</bg #F4D03F></fg #000000></bold>"


class PhoneNumberValidator(Validator):
    def validate(self, document):
        ok = regex.match(
            '^([01]{1})?[-.\s]?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})\s?((?:#|ext\.?\s?|x\.?\s?){1}(?:\d+)?)?$',
            document.text)
        if not ok:
            raise ValidationError(
                message='Please enter a valid phone number',
                cursor_position=len(document.text))  # Move cursor to end


class NumberValidator(Validator):
    def validate(self, document):
        try:
            int(document.text)
        except ValueError:
            raise ValidationError(
                message='Please enter a number',
                cursor_position=len(document.text))  # Move cursor to end


questions = [
    {
        'type': 'input',
        'qmark': '[ ? ]',
        'message': 'Input port number(4 digits): ',
        'name': 'port',
        'validate': NumberValidator,
        'filter': lambda val: int(val)
    },
    {
        'type': 'confirm',
        'message': 'Do you have an account? ',
        'name': 'acc_choice',
        'default': False
    },
    {
        'type': 'list',
        'name': 'acc_type',
        'message': 'Please select your account type',
        'choices': ['Personal', 'Restaurant'],
        'filter': lambda val: val.lower()
    },
    {
        'type': 'input',
        'message': 'Enter your username',
        'name': 'username'
    },
    {
        'type': 'password',
        'message': 'Enter your password',
        'name': 'password'
    },
    {
        'type': 'password',
        'message': 'Confirm your password',
        'name': 'confirm_password'
    },
    {
        'type': 'input',
        'name': 'phone',
        'message': 'Enter your phone number',
        'validate': PhoneNumberValidator
    },
]


def handle_messages(connection: socket.socket):
    # Receive messages sent by the server and display them to user
    global inf
    global isLogin
    global username
    global error
    global success
    global disconnect
    global tips
    global all_rest
    while True:
        try:
            msg = connection.recv(1024)

            # If there is no message, there is a chance that connection has closed
            # so the connection will be closed and an error will be displayed.
            # If not, it will try to decode message in order to show to user.
            if msg:
                decode_msg = pickle.loads(msg)
                # print(decode_msg)

                if type(decode_msg) == dict:
                    if decode_msg['type'] == 'err':
                        send_msg = decode_msg['msg']
                        print(error + " " + send_msg)
                        print()
                        if decode_msg['msg'] == 'Login Fail.':
                            isLogin = False
                            Login(connection)
                        elif decode_msg['msg'] == 'Get restaurant failed.':
                            all_rest.clear()
                            all_rest.append('err')

                    elif decode_msg['type'] == 'success':
                        send_msg = decode_msg['msg']
                        print(success + " " + send_msg)
                        print()
                        if decode_msg['msg'] == 'Login Successfully.' or decode_msg['msg'] == 'Register Successfully.':
                            os.system('cls' if os.name == 'nt' else 'clear')
                            print(
                                '<bold><fg #ffffff><bg #000000>' + '\n\U0001F44BHi, ' + username.upper() + '! are you hungry?\n' + '</bg #000000></fg #ffffff></bold>')
                            print(
                                tips + " " + "Type `<b><fg #1BF4FF>" + "/exit" + "</fg #1BF4FF></b>` to terminate program.")
                            print(
                                tips + " " + "Type `<b><fg #1BF4FF>" + "/help" + "</fg #1BF4FF></b>` to see all commands.")
                            print()
                            isLogin = True
                            os.system("title " + "(CLIENT) " + username.upper())

                    elif decode_msg['type'] == 'rest-info':
                        del decode_msg['type']
                        del decode_msg['_id']
                        print('Restaurant Information')
                        header = ['RESTAURANT NAME', 'RESTAURANT TYPE', 'RESTAURANT PHONE', 'RATING', 'OPEN']
                        data = [decode_msg.values()]
                        print(
                            tabulate(data, headers=header, stralign='center', numalign='center', tablefmt='fancy_grid'))
                        print()

                if type(decode_msg) == list:
                    if decode_msg[0] == 'rest-category':
                        decode_msg.pop(0)
                        print('Restaurant Category')
                        header = ['CATEGORY ID', 'CATEGORY NAME']
                        print(tabulate(decode_msg, headers=header, stralign='center', numalign='center',
                                       tablefmt='fancy_grid'))
                        print()
                    elif decode_msg[0] == 'rest-menu':
                        decode_msg.pop(0)
                        print('Restaurant Menu')
                        header = ['MENU NAME', 'PRICE', 'CATEGORY ID', 'STATUS']
                        print(tabulate(decode_msg, headers=header, stralign='center', numalign='center',
                                       tablefmt='fancy_grid'))
                        print()
                    elif decode_msg[0] == 'all-rest':
                        decode_msg.pop(0)
                        all_rest = decode_msg

            else:
                connection.close()
                inf = False
                break

        except Exception as e:
            print(f'Error handling message from server: {e}')
            print(disconnect)
            connection.close()
            inf = False
            break


def main() -> None:
    answer = prompt(questions[0], style=style)
    host = "127.0.0.1"
    port = answer['port']
    global inf
    global isLogin
    global connect
    global disconnect
    global username
    global all_rest
    try:
        socket_instance = socket.socket()
        socket_instance.connect((host, port))
        threading.Thread(target=handle_messages, args=[socket_instance]).start()
        print(connect)
        print("Client start with " + host + ":" + str(port))

        chk = prompt(questions[1], style=style)['acc_choice']
        if chk:
            Login(socket_instance)
        else:
            Register(socket_instance)

        while inf:
            if isLogin:
                print(f"\U0001F468<fg #FFB755>{username.upper()}</fg #FFB755>> ", end='')
                msg = input()
                # msg = input(username.upper() + '> ')
                if msg.lower() == '/exit':
                    break
                elif msg.lower() == '/help':
                    get_commands()
                elif msg.lower() == '/help rest':
                    get_rest_commands()
                elif msg.lower() == '/help user':
                    get_user_commands()
                elif msg.lower()[:6] == '/rest ':
                    rest_command(msg, socket_instance)
                elif msg.lower()[:6] == '/user ':
                    user_command(msg, socket_instance)
                elif msg.lower()[:18] == '/select rest from ':
                    all_rest = []
                    cmd = msg.split()
                    if cmd[3] == 'all':
                        data = {'type': 'all-rest'}
                    elif cmd[3] == 'fav':
                        data = {'type': 'get-rest-by-fav', 'username': username}
                    elif cmd[3] == 'name':
                        data = {'type': 'get-rest-by-name', 'value': cmd[4]}
                    elif cmd[3] == 'menu':
                        data = {'type': 'get-rest-by-menu', 'value': cmd[4]}
                    socket_instance.send(pickle.dumps(data))
                    while True:
                        if all_rest and len(all_rest) > 2:
                            print('ctrl+c to exit selection.')
                            rest_list = [
                                {
                                    'type': 'list',
                                    'message': 'Select restaurant',
                                    'name': 'selected_rest',
                                    'choices': all_rest
                                }
                            ]
                            answers = prompt(rest_list, style=style)
                            pprint(answers)
                            break
                        else:
                            if all_rest and all_rest[0] == 'err':
                                break

                elif msg.lower() == '':
                    continue
                else:
                    print(f'<red>Unknown the `{msg}` command.</red>')

            # socket_instance.send(pickle.dumps(msg))
        socket_instance.close(socket_instance)
        sys.exit()


    except:
        # print(f'Error, Can\'t connect to server!: {e}')
        # print(disconnect)
        socket_instance.close()
        sys.exit()


def Register(socket_instance):
    global username
    global questions
    global style
    print('Register')
    account = {}
    account['type'] = 'reg'
    print('Registration')
    answers = prompt([questions[2], questions[3], questions[4], questions[5], questions[6]], style=style)
    if answers['acc_type'] == 'restaurant':
        account['restaurant'] = True
    else:
        account['restaurant'] = False
    account['username'] = answers['username']
    account['phone'] = answers['phone']
    if answers['password'] == answers['confirm_password']:
        account['password'] = answers['password']
        username = answers['username']
        socket_instance.send(pickle.dumps(account))
    else:
        print('Password doesn\'t match')
        Register(socket_instance)


def Login(socket_instance):
    global username
    global style
    print('Login')
    account = {}
    account['type'] = 'login'
    answers = prompt([questions[3], questions[4]], style=style)
    account['username'] = answers['username']
    account['password'] = answers['password']
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
        {'command': '/rest',
         'desc': 'the commands for restaurant.\nusing `/help rest` to see more '
                 'restaurant commands.'},
        {'command': '/user',
         'desc': 'the commands for user.\nusing `/help user` to see more user '
                 'commands.'},
        {'command': '/select rest from <all/fav/name/menu> <value>',
         'desc': 'the commands to select restaurant before ordering.\n'
                 'using `<all>` to find all restaurants.\n'
                 'using `<fav>` to show your favourite restaurants.\n'
                 'using `<name> or <menu>` to find restaurants by keywords.\n'
         },
        {'command': '/order',
         'desc': 'the commands for ordering.\nusing `/help order` to see more order '
                 'commands.'},
    ]
    header = ['COMMAND', 'DESCRIPTION']
    rows = [x.values() for x in cmd]
    print(tabulate(rows, headers=header, tablefmt='fancy_grid'))


def get_rest_commands():
    cmd = [
        {'command': '/rest info', 'desc': 'view restaurant information.'},
        {'command': '/rest setup', 'desc': 'add restaurant into system. (for first time only)'},
        {'command': '/rest edit <name/phone/rest_type> <value>', 'desc': 'edit restaurant information.'},
        {'command': '/rest open', 'desc': 'open restaurant'},
        {'command': '/rest close', 'desc': 'close restaurant.'},
        {'command': '/rest category', 'desc': 'view all categories in your restaurant.'},
        {'command': '/rest category add <category_id> <name>',
         'desc': 'add new category of menu into your restaurant.'},
        {'command': '/rest category remove <category_id>', 'desc': 'remove category of menu into your restaurant.'},
        {'command': '/rest category edit <category_id>\n as <category_id/name> <value>',
         'desc': 'edit category information.'},
        {'command': '/rest menu', 'desc': 'view all menus in your restaurant.'},
        {'command': '/rest menu add <name> <price> <category_id>', 'desc': 'add new menu into your restaurant.'},
        {'command': '/rest menu remove <name>', 'desc': 'remove menu into your restaurant.'},
        {'command': '/rest menu edit <name/all>\n as <name/price/category/status> <value>', 'desc': 'edit menu '
                                                                                                    'information.'}
    ]
    header = ['COMMAND', 'DESCRIPTION']
    rows = [x.values() for x in cmd]
    print(tabulate(rows, headers=header, tablefmt='fancy_grid'))


def get_user_commands():
    cmd = [
        {'command': '/user edit phone <value>', 'desc': 'edit user phone number.'},
    ]
    header = ['COMMAND', 'DESCRIPTION']
    rows = [x.values() for x in cmd]
    print(tabulate(rows, headers=header, tablefmt='fancy_grid'))


def user_command(cmd: str, connection: socket.socket):
    global username
    if cmd[:17].lower() == '/user edit phone ':
        _cmd = cmd.split()
        data = {}
        data['username'] = username
        data['type'] = 'edit-user-phone'
        data['value'] = _cmd[3]
        connection.send(pickle.dumps(data))
    else:
        print(f'<red>Unknown the `{cmd}` command.</red>')


def rest_command(cmd: str, connection: socket.socket):
    global username
    if cmd.lower() == '/rest setup':
        AddRestaurantData(connection)
    elif cmd.lower() == '/rest info':
        data = {}
        data['username'] = username
        data['type'] = 'rest-info'
        connection.send(pickle.dumps(data))
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
    elif cmd.lower() == '/rest category':
        data = {}
        data['username'] = username
        data['type'] = 'rest-category'
        connection.send(pickle.dumps(data))
    elif cmd.lower()[:15] == '/rest category ':
        data = {}
        data['username'] = username
        _cmd = cmd.split()
        if _cmd[2].lower() == 'add':
            data['type'] = 'add-category'
            data['category_id'] = _cmd[3]
            data['name'] = _cmd[4]
            connection.send(pickle.dumps(data))
        elif _cmd[2].lower() == 'remove':
            data['type'] = 'remove-category'
            data['category_id'] = _cmd[3]
            connection.send(pickle.dumps(data))
        elif _cmd[2].lower() == 'edit':
            data['type'] = 'edit-category'
            data['category_id'] = _cmd[3]
            data['field'] = _cmd[5]
            data['value'] = _cmd[6]
            connection.send(pickle.dumps(data))
        else:
            print(f'<red>Unknown the `{_cmd[2]}` field.</red>')
    elif cmd.lower() == '/rest menu':
        data = {}
        data['username'] = username
        data['type'] = 'rest-menu'
        connection.send(pickle.dumps(data))
    elif cmd.lower()[:11] == '/rest menu ':
        data = {}
        data['username'] = username
        _cmd = cmd.split()
        if _cmd[2].lower() == 'add':
            data['type'] = 'add-menu'
            data['name'] = _cmd[3]
            data['price'] = int(_cmd[4])
            data['category_id'] = _cmd[5]
            connection.send(pickle.dumps(data))
        elif _cmd[2].lower() == 'remove':
            data['type'] = 'remove-menu'
            data['name'] = _cmd[3]
            connection.send(pickle.dumps(data))
        elif _cmd[2].lower() == 'edit':
            data['type'] = 'edit-menu'
            data['name'] = _cmd[3]
            data['field'] = _cmd[5]
            if data['field'] == 'price':
                data['value'] = int(_cmd[6])
            else:
                data['value'] = _cmd[6]
            connection.send(pickle.dumps(data))
        else:
            print(f'<red>Unknown the `{_cmd[2]}` field.</red>')
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
