import socket
import threading
import sys
import os
import time


class User():
    """
    Holds the chatclient's client socket information. Used for interacting
    with the connected server.
    Status: Given
    """

    def __init__(self, username):
        """
        Initialise the user with a given username.
        Args:
            username (string): name of the client.
        """
        self.username = username
        self.maxBuffer = 1024

    def connect(self, port):
        """
        Initialise the socket connection as a TCP socket on localhost.
        Args:
            port (int): channel port to connect to.
        """
        # Connect to the port passed as a client
        self.port = port
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.soc.connect(("localhost", self.port))

    def disconnect(self):
        """
        Close the socket connection.
        """
        self.soc.close()

    def send(self, data):
        """
        Send the string to the socket encoded.
        Args:
            data (string): string to be sent to server.
        Returns: False if a connection reset error occurred, or true on a successful send.
        """
        try:
            self.soc.send(data.encode())
            return True
        except (ConnectionResetError, OSError):
            return False

    def receive(self):
        """
        Receive a string from the server. Keeps increasing the
        size of the buffer holding the data until all data has
        been received.
        Returns:
            string: message from the server.
        """
        buffer = bytearray()
        while True:
            try:
                data = self.soc.recv(self.maxBuffer)
            except (ConnectionResetError, OSError):  # Connection Reset
                return None
            buffer.extend(data)
            size = sys.getsizeof(buffer)
            if size > self.maxBuffer:
                self.maxBuffer *= 2
            else:
                break
        # Reset buffer limit
        self.maxBuffer = 1024
        return buffer.decode()

    def get_username(self):
        """
        Get the username of this user.
        Returns:
            string: the username of this user.
        """
        return self.username


def input_thread(quitEvent, user):
    """
    The input thread for the client, constantly takes in user input
    from stdin and sends it to the server.
    Status: Given
    Args:
        quitEvent (threading.Event): Event on which the user must exit.
        user (User): the user object used by this chatclient.
    """
    while not quitEvent.is_set():
        try:
            message = input().strip()
        except EOFError:
            continue
        if not user.send(message):  # ConnectionResetError occured
            quitEvent.set()


def output_thread(quitEvent, user):
    """
    The output thread handling responses from the server. Receives server
    messages and handles them accordingly.
    Status: TODO
    Args:
        quitEvent (threading.Event): Event on which the user must exit.
        user (User): the user object used by this chatclient.
    """
    is_receiving_file = False
    file_data = b''
    file_name = ''

    while not quitEvent.is_set():
        output = user.receive()
        if not output or output is None:  # Server has exited
            quitEvent.set()
            continue
        # Write your code here...

        elif "You have successfully quit" in output or "You went AFK" in output or "You are kicked" in output:
            print(output, flush=True)
            user.disconnect()
            quitEvent.set()

        elif is_receiving_file:
            if "You successfully received" not in output:
                if type(output) is str:
                    file_data = bytes(output, 'utf-8')
                else:
                    file_data = output

            else:
                is_receiving_file = False
                with open(file_name, 'wb') as f:
                    if isinstance(file_data, str):
                        file_data = file_data.encode()
                    f.write(file_data)
                file_data = b''
                file_name = ''

        elif "You are receiving" in output:
            start = output.find("'")
            end = output.find("'", start + 1)
            file_name = output[start + 1:end]
            is_receiving_file = True

        elif "You can now switching to" in output:
            port = int(output.split()[-1])
            user.disconnect()
            user.connect(port)
            user.send(user.get_username())

        else:
            print(output, flush=True)  # Send output to stdout


def validate_input(port, username):
    """
    Validate port and username properties, exit else.
    Status: Given
    Returns:
        port (int): the port number to connect to.
        username (string): the username of the client.
    """
    try:
        port = int(port)
        if (port < 1 or port > 65535):
            sys.exit(1)
    except ValueError:
        sys.exit(1)

    return port, username


if __name__ == '__main__':
    """
    Main function processing of the chatclient. Creates user object and
    threads and waits for them to finish.
    """
    try:
        if len(sys.argv) != 3:
            print("Usage: python mchatclient.py <port> <username>")
            sys.exit(1)

        port = sys.argv[1]
        username = sys.argv[2]

        port, username = validate_input(port, username)

        # Create and connect the user
        user = User(username)
        try:
            user.connect(int(port))
            if not user.send(user.get_username()):
                sys.exit(1)  # ConnectionResetError happened
        except:
            sys.exit(1)
        # Event for when user types /quit
        quitEvent = threading.Event()

        # Initialize and begin reading and writing threads
        inputThread = threading.Thread(
            target=input_thread, args=(quitEvent, user,))
        outputThread = threading.Thread(
            target=output_thread, args=(quitEvent, user,))
        inputThread.daemon = True
        outputThread.daemon = True
        try:
            inputThread.start()
            outputThread.start()

        except:  # exit if threads can't be created
            sys.exit(1)

        # Wait for threads to complete before exiting the program
        while not quitEvent.is_set():
            continue
        sys.exit(0)  # input thread is daemon and will exit itself
    except KeyboardInterrupt:
        print("Crlt + C Pressed. Exiting...")
        os._exit(0)
