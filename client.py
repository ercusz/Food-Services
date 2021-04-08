import socket
import sys
import threading
import pickle

login = False

def handle_messages(connection: socket.socket):
    #Receive messages sent by the server and display them to user
    global login
    while True:
        try:
            msg = connection.recv(1024)

            # If there is no message, there is a chance that connection has closed
            # so the connection will be closed and an error will be displayed.
            # If not, it will try to decode message in order to show to user.
            if msg:

                if pickle.loads(msg) =='ok':
                    login = True
                    print('Process Successfully')
                    print()
                else:
                    if pickle.loads(msg) =='failed':
                        print('Login Fail')
                        connection.close()

                if isinstance(pickle.loads(msg), list):
                    if 'menuId' in pickle.loads(msg)[0].keys():
                        for menu in pickle.loads(msg):
                            for title, value in menu.items():
                                print(f'{title}: {value}')

            else:
                connection.close()
                break

        except Exception as e:
            #print(f'Error handling message from server: {e}')
            print("!Disconnected")
            connection.close()
            break


def main() -> None:
    customPort = int(input('Input port number(4 digits): '))
    host = "127.0.0.1"
    port = customPort
    global login
    try:
        socket_instance = socket.socket()
        socket_instance.connect((host, port))
        threading.Thread(target=handle_messages, args=[socket_instance]).start()
        print('!Connected')
        print("Client start with " + host + ":" + str(port))

        chk = input("Do you have an account? (y/N): ")
        if chk.lower() == 'y':
            Login(socket_instance)
        else:
            Register(socket_instance)

        while Login:
            print("TIPS: Type 'exit' to terminate program.")

            while True:
                msg = input('>> ')
                if msg.lower() == 'exit':
                    break

                socket_instance.send(pickle.dumps(msg))

            socket_instance.close()

    except:
        #print('Error, Can\'t connect to server!')
        socket_instance.close()
        sys.exit()


def Register(socket_instance):
    print('Register')
    account = {}
    account['type'] = 'reg'
    account['username'] = input('username: ')
    account['password'] = input('password: ')
    confirmpassword = input('confirm password: ')
    account['phone'] = input('phone: ')
    if account['password'] == confirmpassword:
        socket_instance.send(pickle.dumps(account))
    else:
        print('Password doesn\'t match')
        Register(socket_instance)


def Login(socket_instance):
    print('>> Login')
    account = {}
    account['type'] = 'login'
    account['username'] = input('username: ')
    account['password'] = input('password: ')
    socket_instance.send(pickle.dumps(account))

if __name__ == "__main__":
    main()
