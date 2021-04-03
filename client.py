import socket
import sys
import threading


def handle_messages(connection: socket.socket):
#Receive messages sent by the server and display them to user
    while True:
        try:
            msg = connection.recv(1024)

            # If there is no message, there is a chance that connection has closed
            # so the connection will be closed and an error will be displayed.
            # If not, it will try to decode message in order to show to user.
            if msg:
                print(msg.decode())
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

    try:
        socket_instance = socket.socket()
        socket_instance.connect((host, port))
        threading.Thread(target=handle_messages, args=[socket_instance]).start()
        print('!Connected')
        print("Client start with " + host + ":" + str(port))

        name = ""
        while name == "":
            print("Please enter your name.")
            name = "--name " + input(">> ")
            socket_instance.send(name.encode())

        print("TIPS: Enter 'exit' to terminate program.")

        while True:
            msg = input(name[7:].upper()+">> ")

            if msg.lower() == 'exit':
                break

            socket_instance.send(msg.encode())

        socket_instance.close()

    except:
        print('Error, Can\'t connect to server!')
        socket_instance.close()
        sys.exit()


if __name__ == "__main__":
    main()
