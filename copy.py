import socket
import threading
import sys
import time
import queue
import os


class Client:
    def __init__(self, username, connection, address):
        self.username = username
        self.connection = connection
        self.address = address
        self.kicked = False
        self.in_queue = True
        self.remaining_time = 100 # remaining time before AFK
        self.muted = False
        self.mute_duration = 0


class Channel:
    def __init__(self, name, port, capacity):
        self.name = name
        self.port = port
        self.capacity = capacity
        self.queue = queue.Queue()
        self.clients = []

def parse_config(config_file: str) -> list:
    """
    Parses lines from a given configuration file and VALIDATE the format of each line. The 
    function validates each part and if valid returns a list of tuples where each tuple contains
    (channel_name, channel_port, channel_capacity). The function also ensures that there are no 
    duplicate channel names or ports. if not valid, exit with status code 1.
    Status: TODO
    Args:
        config_file (str): The path to the configuration file (e.g, config_01.txt).
    Returns:
        list: A list of tuples where each tuple contains:
        (channel_name, channel_port, and channel_capacity)
    Raises:
        SystemExit: If there is an error in the configuration file format.
    """
    # Write your code here...
    pass

def get_channels_dictionary(parsed_lines) -> dict:
    """
    Creates a dictionary of Channel objects from parsed lines.
    Status: Given
    Args:
        parsed_lines (list): A list of tuples where each tuple contains:
        (channel_name, channel_port, and channel_capacity)
    Returns:
        dict: A dictionary of Channel objects where the key is the channel name.
    """
    channels = {}

    for channel_name, channel_port, channel_capacity in parsed_lines:
        channels[channel_name] = Channel(channel_name, channel_port, channel_capacity)

    return channels

def quit_client(client, channel) -> None:
    """
    Implement client quitting function
    Status: TODO
    """
    # if client is in queue
    if client.in_queue:
        # Write your code here...
        # remove, close connection, and print quit message in the server.

        # broadcast queue update message to all the clients in the queue.
        pass

    # if client is in channel
    else:
        # Write your code here...
        # remove client from the channel, close connection, and broadcast quit message to all clients.
        pass

def send_client(client, channel, msg) -> None:
    """
    Implement file sending function, if args for /send are valid.
    Else print appropriate message and return.
    Status: TODO
    """
    # Write your code here...
    # if in queue, do nothing
    if client.in_queue:
        return
    else:
        # if muted, send mute message to the client
        if client.muted:
            pass

        # if not muted, process the file sending
        else:
            # validate the command structure

            # check for file existence

            # check if receiver is in the channel, and send the file
            pass

def list_clients(client, channels) -> None:
    """
    List all clients in all the channels.
    Status: TODO
    """
    # Write your code here...
    pass

def whisper_client(client, channel, msg) -> None:
    """
    Implement whisper function, if args for /whisper are valid.
    Else print appropriate message and return.
    Status: TODO
    """
    # Write your code here...
    # if in queue, do nothing
    if client.in_queue:
        return
    else:
        # if muted, send mute message to the client
        if client.muted:
            pass
        else:
            # validate the command structure

            # validate if the target user is in the channel
            
            # if target user is in the channel, send the whisper message
            
            # print whisper server message
            pass

def switch_channel(client, channel, msg, channels) -> None:
    """
    Implement channel switching function, if args for /switch are valid.
    Else print appropriate message and return.
    Status: TODO
    """
    # Write your code here...
    # validate the command structure

    # check if the new channel exists

    # check if there is a client with the same username in the new channel

    # if all checks are correct, and client in queue
    if client.in_queue:
        # remove client from current channel queue

        # broadcast queue update message to all clients in the current channel

        # tell client to connect to new channel and close connection
        pass

    # if all checks are correct, and client in channel
    else:
        # remove client from current channel

        # tell client to connect to new channel and close connection
        pass

def broadcast_in_channel(client, channel, msg) -> None:
    """
    Broadcast a message to all clients in the channel.
    Status: TODO
    """
    # Write your code here...
    # if in queue, do nothing

    # if muted, send mute message to the client

    # broadcast message to all clients in the channel
    pass

def client_handler(client, channel, channels) -> None:
    """
    Handles incoming messages from a client in a channel. Supports commands to quit, send, switch, whisper, and list channels. 
    Manages client's mute status and remaining time. Handles client disconnection and exceptions during message processing.
    Status: TODO (check the "# Write your code here..." block in Exception)
    Args:
        client (Client): The client to han        channel (Channel): The channel in which the client is.
        channels (dict): A dictionary of all channels.
dle.
    """
    while True:
        if client.kicked:
            break
        try:
            msg = client.connection.recv(1024).decode()

            # check message for client commands
            if msg.startswith("/quit"):
                quit_client(client, channel)
                break
            elif msg.startswith("/send"):
                print("In send")
                send_client(client, channel, msg)
            elif msg.startswith("/list"):
                print("In list")
                list_clients(client, channels)
            elif msg.startswith("/whisper"):
                whisper_client(client, channel, msg)
            elif msg.startswith("/switch"):
                switch_channel(client, channel, msg, channels)
                break

            # if not a command, broadcast message to all clients in the channel
            else:
                broadcast_in_channel(client, channel, msg)

            # reset remaining time before AFK
            if not client.muted:
                client.remaining_time = 100
        except EOFError:
            continue
        except OSError:
            break
        except Exception as e:
            print(f"Error in client handler: {e}")
            # remove client from the channel, close connection
            # Write your code here...

            break

def check_duplicate_username(username, channel, conn) -> bool:
    """
    Check if a username is already in a channel or its queue.
    Status: TODO
    """
    # Write your code here...
    pass

def position_client(channel, conn, username, new_client) -> None:
    """
    Place a client in a channel or queue based on the channel's capacity.
    Status: TODO
    """
    # Write your code here...
    if len(channel.clients) < channel.capacity:
        # put client in channel and reset remaining time before AFK
        pass
    else:
        # put client in queue
        pass

def channel_handler(channel, channels) -> None:
    """
    Starts a chat server, manage channels, respective queues, and incoming clients.
    This initiates different threads for chanel queue processing and client handling.
    Status: Given
    Args:
        channel (Channel): The channel for which to start the server.
    Raises:
        EOFError: If there is an error in the client-server communication.
    """
    # Initialize server socket, bind, and listen
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("localhost", channel.port))
    server_socket.listen(channel.capacity)

    # launch a thread to process client queue
    queue_thread = threading.Thread(target=process_queue, args=(channel,))
    queue_thread.start()

    while True:
        try:
            # accept a client connection
            conn, addr = server_socket.accept()
            username = conn.recv(1024).decode()

            # check duplicate username in channel and channel's queue
            is_valid = check_duplicate_username(username, channel, conn)
            if not is_valid: continue

            welcome_msg = f"[Server message ({time.strftime('%H:%M:%S')})] Welcome to the {channel.name} channel, {username}."
            conn.send(welcome_msg.encode())
            time.sleep(0.1)
            new_client = Client(username, conn, addr)

            # position client in channel or queue
            position_client(channel, conn, username, new_client)

            # Create a client thread for each connected client, whether they are in the channel or queue
            client_thread = threading.Thread(target=client_handler, args=(new_client, channel, channels))
            client_thread.start()
        except EOFError:
            continue

def remove_item(q, item_to_remove) -> queue.Queue:
    """
    Remove item from queue
    Status: Given
    Args:
        q (queue.Queue): The queue to remove the item from.
        item_to_remove (Client): The item to remove from the queue.
    Returns:
        queue.Queue: The queue with the item removed.
    """
    new_q = queue.Queue()
    while not q.empty():
        current_item = q.get()
        if current_item != item_to_remove:
            new_q.put(current_item)

    return new_q


def process_queue(channel) -> None:
    """
    Processes the queue of clients for a channel in an infinite loop. If the channel is not full, 
    it dequeues a client, adds them to the channel, and updates their status. It then sends updates 
    to all clients in the channel and queue. The function handles EOFError exceptions and sleeps for 
    1 second between iterations.
    Status: TODO
    Args:
        channel (Channel): The channel whose queue to process.
    Returns:
        None
    """
    # Write your code here...
    while True:
        try:
            if not channel.queue.empty() and len(channel.clients) < channel.capacity:
                # Dequeue a client from the queue and add them to the channel

                # Send join message to all clients in the channel

                # Update the queue messages for remaining clients in the queue
                
                # Reset the remaining time to 100 before AFK
                time.sleep(1)
        except EOFError:
            continue

def kick_user(command, channels) -> None:
    """
    Implement /kick function
    Status: TODO
    Args:
        command (str): The command to kick a user from a channel.
        channels (dict): A dictionary of all channels.
    Returns:
        None
    """
    # Write your code here...
    # validate command structure

    # check if the channel exists in the dictionary

    # if channel exists, check if the user is in the channel
    
    # if user is in the channel, kick the user

    # if user is not in the channel, print error message
    pass

def empty(command, channels) -> None:
    """
    Implement /empty function
    Status: TODO
    Args:
        command (str): The command to empty a channel.
        channels (dict): A dictionary of all channels.
    """
    # Write your code here...
    # validate the command structure

    # check if the channel exists in the server

    # if the channel exists, close connections of all clients in the channel
    pass

def mute_user(command, channels) -> None:
    """
    Implement /mute function
    Status: TODO
    Args:
        command (str): The command to mute a channel.
        channel_name (str): The name of the channel to mute the user in.
    Returns:
        None
    """
    # Write your code here...
    # validate the command structure
    
    # check if the mute time is valid

    # check if the channel exists in the server

    # if the channel exists, check if the user is in the channel

    # if user is in the channel, mute it and send messages to all clients

    # if user is not in the channel, print error message
    pass

def shutdown(channels) -> None:
    """
    Implement /shutdown function
    Status: TODO
    Args:
        channels (dict): A dictionary of all channels.
    """
    # Write your code here...
    # close connections of all clients in all channels and exit the server

    # end of code insertion, keep the os._exit(0) as it is
    os._exit(0)

def server_commands(channels) -> None:
    """
    Implement commands to kick a user, empty a channel, mute a user, and shutdown the server.
    Each command has its own validation and error handling. 
    Status: Given
    Args:
        channels (dict): A dictionary of all channels.
    Returns:
        None
    """
    while True:
        try:
            command = input()
            if command.startswith('/kick'):
                kick_user(command, channels)
            elif command.startswith("/empty"):
                empty(command, channels)
            elif command.startswith("/mute"):
                mute_user(command, channels)
            elif command == "/shutdown":
                shutdown(channels)
            else:
                continue
        except EOFError:
            continue
        except Exception as e:
            print(f"{e}")
            sys.exit(1)

def check_inactive_clients(channels) -> None:
    """
    Continuously manages clients in all channels. Checks if a client is muted, in queue, or has run out of time. 
    If a client's time is up, they are removed from the channel and their connection is closed. 
    A server message is sent to all clients in the channel. The function also handles EOFError exceptions.
    Status: TODO
    Args:
        channels (dict): A dictionary of all channels.
    """
    # Write your code here...
    # parse through all the clients in all the channels

    # if client is muted or in queue, do nothing

    # remove client from the channel and close connection, print AFK message

    # if client is not muted, decrement remaining time
    pass

def handle_mute_durations(channels) -> None:
    """
    Continuously manages the mute status of clients in all channels. If a client's mute duration has expired, 
    their mute status is lifted. If a client is still muted, their mute duration is decremented. 
    The function sleeps for 0.99 seconds between iterations and handles EOFError exceptions.
    Status: Given
    Args:
        channels (dict): A dictionary of all channels.
    """
    while True:
        try:
            for channel_name in channels:
                channel = channels[channel_name]
                for client in channel.clients:
                    if client.mute_duration <= 0:
                        client.muted = False
                        client.mute_duration = 0
                    if client.muted and client.mute_duration > 0:
                        client.mute_duration -= 1
            time.sleep(0.99)
        except EOFError:
            continue

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 chatserver.py configfile")
        sys.exit(1)

    config_file = sys.argv[1]

    # parsing and creating channels
    parsed_lines = parse_config(config_file)
    channels = get_channels_dictionary(parsed_lines)

    # creating individual threads to handle channels connections
    for _, channel in channels.items():
        thread = threading.Thread(target=channel_handler, args=(channel, channels))
        thread.start()

    server_commands_thread = threading.Thread(target=server_commands, args=(channels,))
    server_commands_thread.start()

    inactive_clients_thread = threading.Thread(target=check_inactive_clients, args=(channels,))
    inactive_clients_thread.start()

    mute_duration_thread = threading.Thread(target=handle_mute_durations, args=(channels,))
    mute_duration_thread.start()


if __name__ == "__main__":
    main()
