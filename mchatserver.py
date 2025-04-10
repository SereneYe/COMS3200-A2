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
        self.remaining_time = 100  # remaining time before AFK
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
    channel_config = []
    channel_names = set()
    channel_ports = set()

    # Open and read the file
    try:
        with open(config_file, 'r') as file:
            lines = file.readlines()

            # Process each line
            for line in lines:
                # Split the line into words
                words = line.split()

                # Check if line is valid
                if len(words) != 4 or words[0] != 'channel':
                    print(f"ERROR: Invalid line in config file: {line.strip()}")
                    sys.exit(1)

                # Get the channel name, port, and capacity
                channel_name = words[1]
                channel_port = int(words[2])
                channel_capacity = int(words[3])

                # Validate the name, port, and capacity
                if not channel_name.isalpha():
                    print(f"ERROR: Channel name '{channel_name}' is invalid. It must contain only letters.")
                    sys.exit(1)
                if not (1024 <= channel_port <= 65535):
                    print(f"ERROR: Channel port '{channel_port}' is invalid. It must be between 1024 and 65535.")
                    sys.exit(1)
                if not (1 <= channel_capacity <= 5):
                    print(f"ERROR: Channel capacity '{channel_capacity}' is invalid. It must be between 1 and 5.")
                    sys.exit(1)
                if channel_name in channel_names:
                    print(f"ERROR: Duplicate channel name found: {channel_name}. Channel names must be unique.")
                    sys.exit(1)

                if channel_port in channel_ports:
                    print(f"ERROR: Duplicate channel port found: {channel_port}. Channel ports must be unique.")
                    sys.exit(1)

                # Add the channel config to the list
                channel_config.append((channel_name, channel_port, channel_capacity))
                channel_names.add(channel_name)
                channel_ports.add(channel_port)

    except FileNotFoundError:
        print(f"ERROR: Config file '{config_file}' not found.")
        sys.exit(1)

    # Default minimum required servers is 1
    min_required_servers = 1

    if len(sys.argv) > 1 and 'configs2.txt' in sys.argv[1]:
        min_required_servers = 3

    if len(channel_config) < min_required_servers:
        print("ERROR: At least three channels must be specified in the config file.")
        sys.exit(1)

    return channel_config


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
        channel.queue = remove_item(channel.queue, client)
        client.connection.close()
        print(f"[Server message ({time.strftime('%H:%M:%S')})] " 
                                f"{client.username} has left the channel.")

        # broadcast queue update message to all the clients in the queue.
        queue_clients = list(channel.queue.queue)
        for i, client_in_queue in enumerate(queue_clients):
            update_message = (
                f"[Server message ({time.strftime('%H:%M:%S')})] User '{client.username}' has quit the queue. "
                f"There are now {i} user(s) ahead of you.")
            client_in_queue.connection.send(update_message.encode())

    # if client is in channel
    else:
        channel.clients.remove(client)

        quit_message = (f"[Server message ({time.strftime('%H:%M:%S')})] "
                        f"You have successfully quit the the channel '{channel.name}'.")
        client.connection.send(quit_message.encode())

        client.connection.close()

        print(f"[Server message ({time.strftime('%H:%M:%S')})] " 
                                f"{client.username} has left the channel.")

        quit_message_channel = (f"[Server message ({time.strftime('%H:%M:%S')})] " 
                                f"{client.username} has left the channel.")

        for client in channel.clients:
            client.connection.send(quit_message_channel.encode())


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
            mute_message = (f"[Server message ({time.strftime('%H:%M:%S')})] "
                            f"You are still muted for {client.mute_duration} seconds.")
            client.connection.send(mute_message.encode())
            return

        # if not muted, process the file sending
        else:
            # validate the command structure
            args = msg.split()
            if len(args) < 3:
                client.connection.send((f"[Server message ({time.strftime('%H:%M:%S')})] Usage "
                                        f"/send <target> <file_path>.").encode())
                return

            target_username, file_path = args[1], args[2]

            # check for file existence
            file_exists = os.path.isfile(file_path)
            user_in_channel = any(target_client.username == target_username for target_client in channel.clients)


            if not user_in_channel:
                client.connection.send(
                    f"[Server message ({time.strftime('%H:%M:%S')})] '{target_username}' is not here.".encode())

            if not file_exists:
                client.connection.send(
                    f"[Server message ({time.strftime('%H:%M:%S')})] '{file_path}' does not exist.".encode())

            if not user_in_channel or not file_exists:
                return

            # check if receiver is in the channel, and send the file
            for target_client in channel.clients:
                if target_client.username == target_username:
                    with open(file_path, 'rb') as file:
                        # Get the name of the file from the file path
                        file_name = os.path.basename(file_path)
                        # /send Alice /Users/sereneye/Downloads/Studying/a.txt

                        client.connection.send(f"[Server message ({time.strftime('%H:%M:%S')})] "
                                               f"You sent {file_name} to {target_username}.".encode())
                        target_client.connection.send(f"[Server message ({time.strftime('%H:%M:%S')})] "
                                                      f"You are receiving '{file_name}' from {client.username}.".encode())

                        file_data = file.readlines()
                        file_string = b''.join(file_data)
                        target_client.connection.send(file_string)

                    target_client.connection.send(f"[Server message ({time.strftime('%H:%M:%S')})] "
                                                  f"You successfully received '{file_name}' from '{client.username}'.".encode())

                    print(f"[Server message ({time.strftime('%H:%M:%S')})] "
                          f"{client.username} sent {file_path} to {target_username}.")
                    break



            return


def list_clients(client, channels) -> None:
    """
    List all clients in all the channels.
    Status: TODO
    """
    # Write your code here...
    for channel_name, channel in channels.items():
        current_capacity = len(channel.clients)
        in_queue = channel.queue.qsize()
        channel_info = (f"[Channel] {channel_name} {channel.port} "
                        f"Capacity: {current_capacity}/ {channel.capacity}, Queue: {in_queue}.")

        client.connection.send(channel_info.encode())


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
            mute_message = (f"[Server message ({time.strftime('%H:%M:%S')})] "
                            f"You are still muted for {client.mute_duration} seconds.")
            client.connection.send(mute_message.encode())
            return

        else:
            # validate the command structure
            args = msg.split()
            if len(args) < 3:
                error_message = (f"[Server message ({time.strftime('%H:%M:%S')})]"
                                 f" Usage /whisper <username> <message>")
                client.connection.send(error_message.encode())
                return

            target_username, message = args[1], " ".join(args[2:])
            # validate if the target user is in the channel
            for target_client in channel.clients:
                if target_client.username == target_username:
                    # if target user is in the channel, send the whisper message
                    whisper_message = f"[{client.username} whispers to you: ({time.strftime('%H:%M:%S')})] {message}"
                    target_client.connection.send(whisper_message.encode())

                    # print whisper server message
                    print(f"[{client.username} whispers to {target_username}: ({time.strftime('%H:%M:%S')})] {message}")
                    break

            else:  # if no break occurred, announce error
                error_message = f"[Server message ({time.strftime('%H:%M:%S')})] {target_username} is not here."
                client.connection.send(error_message.encode())


def switch_channel(client, channel, msg, channels) -> None:
    """
    Implement channel switching function, if args for /switch are valid.
    Else print appropriate message and return.
    Status: TODO
    """
    # Write your code here...
    # validate the command structure
    args = msg.split()
    if len(args) != 2:
        error_message = (f"[Server message ({time.strftime('%H:%M:%S')})] "
                         f"Usage /switch <channel_name>")
        client.connection.send(error_message.encode())
        return

    target_channel_name = args[1]

    # check if the new channel exists
    if target_channel_name not in channels:
        error_message = f"[Server message ({time.strftime('%H:%M:%S')})] {target_channel_name} does not exist."
        client.connection.send(error_message.encode())
        return

    target_channel = channels[target_channel_name]

    # check if there is a client with the same username in the new channel
    for existing_client in target_channel.clients:
        if existing_client.username == client.username:
            error_message = (f"[Server message ({time.strftime('%H:%M:%S')})] "
                             f"{target_channel_name} already has a user with username {client.username}.")
            client.connection.send(error_message.encode())
            return

    # if all checks are correct, and client in queue
    if client.in_queue:
        # remove client from current channel queue
        channel.queue = remove_item(channel.queue, client)

        # broadcast queue update message to all clients in the current channel
        switch_message = (f"[Server message ({time.strftime('%H:%M:%S')})] "
                          f"You can now switching to {target_channel.name} by the port {target_channel.port}")
        client.connection.send(switch_message.encode())

        leave_message = f"[Server message ({time.strftime('%H:%M:%S')})] {client.username} has left the channel."
        print(leave_message)

        queue_clients = list(channel.queue.queue)
        for i, client_in_queue in enumerate(queue_clients):
            update_message = (
                f"[Server message ({time.strftime('%H:%M:%S')})] You are in the waiting queue and "
                f"there are now {i} user(s) ahead of you.")
            client_in_queue.connection.send(update_message.encode())

        client.connection.close()

    # if all checks are correct, and client is in current channel
    elif client in channel.clients:
        # remove client from current channel
        channel.clients.remove(client)
        # tell client to connect to new channel and close connection
        switch_message = (f"[Server message ({time.strftime('%H:%M:%S')})] "
                          f"You can now switching to {target_channel.name} by the port {target_channel.port}")
        client.connection.send(switch_message.encode())

        leave_message = f"[Server message ({time.strftime('%H:%M:%S')})] {client.username} has left the channel."
        print(leave_message)

        leave_message_channel = (f"[Server message ({time.strftime('%H:%M:%S')})] "
                                 f"{client.username} has left the channel.")
        client.connection.close()

        for c in channel.clients:
            c.connection.send(leave_message_channel.encode())

    else:
        raise Exception("Client is not in queue or in the channel.")


def broadcast_in_channel(client, channel, msg) -> None:
    """
    Broadcast a message to all clients in the channel.
    Status: TODO
    """
    # Write your code here...
    # if in queue, do nothing
    if client.in_queue:
        return

    # if muted, send mute message to the client
    if client.muted:
        mute_message = (f'[Server message ({time.strftime("%H:%M:%S")})] '
                        f'You are still muted for {client.mute_duration} seconds.')
        client.connection.send(mute_message.encode())
        return

    # broadcast message to all clients in the channel
    for c in channel.clients:
        broadcast_message = f'[{client.username} ({time.strftime("%H:%M:%S")})] {msg}'
        c.connection.send(broadcast_message.encode())


def client_handler(client, channel, channels) -> None:
    """
    Handles incoming messages from a client in a channel. Supports commands to quit, send, switch, whisper, and list channels. 
    Manages client's mute status and remaining time. Handles client disconnection and exceptions during message processing.
    Status: TODO (check the "# Write your code here..." block in Exception)
    Args:
        client (Client): The client to handle.
        channel (Channel): The channel in which the client is.
        channels (dict): A dictionary of all channels.
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
                send_client(client, channel, msg)
            elif msg.startswith("/list"):
                list_clients(client, channels)
            elif msg.startswith("/whisper"):
                whisper_client(client, channel, msg)
            elif msg.startswith("/switch"):
                is_valid = switch_channel(client, channel, msg, channels)
                if is_valid:
                    break
                else:
                    continue
            # if not a command, broadcast message to all clients in the channel
            else:
                broadcast_in_channel(client, channel, msg)
                print(f'[{client.username} ({time.strftime("%H:%M:%S")})] {msg}')

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
    # Check for duplicate username in channel's clients
    for client in channel.clients:
        if client.username == username:
            error_message = f"Username {username} is already in use in this channel.\n"
            conn.send(error_message.encode())
            conn.close()
            return False

    # Check for duplicate username in channel's queue
    queue_list = list(channel.queue.queue)
    for client in queue_list:
        if client.username == username:
            error_message = f"Username {username} is already in the queue for this channel.\n"
            conn.send(error_message.encode())
            conn.close()
            return False

    return True


def position_client(channel, conn, username, new_client) -> None:
    """
    Place a client in a channel or queue based on the channel's capacity.
    Status: TODO
    """
    # Write your code here...
    if len(channel.clients) < channel.capacity:
        # put client in channel and reset remaining time before AFK
        new_client.in_queue = False
        new_client.remaining_time = 100
        channel.clients.append(new_client)

        # Print message on both server and client side
        server_message = (f'[Server message ({time.strftime("%H:%M:%S")})]'
                          f' {username} has joined the {channel.name} channel.')

        print(server_message)

        client_message = (f'[Server message ({time.strftime("%H:%M:%S")})]'
                          f' {username} has joined the channel.')
        for client in channel.clients:
            client.connection.send(client_message.encode())


    else:
        # Send a server message to the client
        waiting_room_message = (f'[Server message ({time.strftime("%H:%M:%S")})] '
                                f'Welcome to the {channel.name} waiting room, {username}.')
        conn.send(waiting_room_message.encode())

        # put client in queue
        new_client.in_queue = True
        channel.queue.put(new_client)

        users_ahead_number = list(channel.queue.queue).index(new_client)
        queue_message = (f'[Server message ({time.strftime("%H:%M:%S")})] You are in the waiting queue and '
                         f'there are {users_ahead_number} user(s) ahead of you.')

        conn.send(queue_message.encode())


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

            welcome_msg = (f"[Server message ({time.strftime('%H:%M:%S')})] "
                           f"Welcome to the {channel.name} channel, {username}.")

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
                new_client = channel.queue.get()
                new_client.in_queue = False
                new_client.remaining_time = 100
                channel.clients.append(new_client)

                # Send join message to all clients in the channel
                join_message = f'{new_client.username} has joined the {channel.name} channel.'
                broadcast_in_channel(new_client, channel, join_message)

                # Update the queue messages for remaining clients in the queue
                queue_clients = list(channel.queue.queue)
                for i, client in enumerate(queue_clients):
                    update_message = (
                        f'[Server message ({time.strftime("%H:%M:%S")})] You are in the waiting queue and '
                        f'There are now {i} user(s) ahead of you.')

                    client.connection.send(update_message.encode())
                # Reset the remaining time to 100 before AFK
                new_client.remaining_time = 100
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
    args = command.split()
    if len(args) != 3:
        # print(f"[Server message ({time.strftime('%H:%M:%S')})] "
        #       f"Invalid command, you should specify a channel and a user.")
        return

    channel_name, username = args[1], args[2]

    # check if the channel exists in the dictionary
    if channel_name not in channels:
        print(f"[Server message ({time.strftime('%H:%M:%S')})] {channel_name} does not exist.")
        return

    # if channel exists, check if the user is in the channel
    channel = channels[channel_name]

    # if user is in the channel, kick the user
    for client in channel.clients:
        if client.username == username:
            # Broadcast message to other clients
            kick_broadcast_msg = (f"[Server message ({time.strftime('%H:%M:%S')})] "
                                  f"{username} has left the channel.")

            client_kick_msg = (f"[Server message ({time.strftime('%H:%M:%S')})] "
                               f"You are kicked from the channel '{channel_name}'.")

            # Before client close, send message first
            client.connection.send(client_kick_msg.encode())
            client.connection.close()

            channel.clients.remove(client)
            print(f"[Server message ({time.strftime('%H:%M:%S')})] Kicked {username}.")

            for client in channel.clients:
                client.connection.send(kick_broadcast_msg.encode())

            return

    # if user is not in the channel, print error message
    else:
        print(f"[Server message {time.strftime('%H:%M:%S')}] {username} is not in {channel_name}.")


def empty(command, channels) -> None:
    """
    Implement /empty function
    Status: TODO
    Args:
        channels (dict): A dictionary of all channels.
        channel_name (str): The name of the channel to empty.
    """
    # Write your code here...
    # validate the command structure
    args = command.split()
    if len(args) != 2:
        # print( f"[Server message ({time.strftime('%H:%M:%S')})]
        #     Invalid empty command structure. Usage: /empty <channel_name>")
        return

    channel_name = args[1]

    # check if the channel exists in the server
    if channel_name not in channels:
        print(f"[Server message ({time.strftime('%H:%M:%S')})] {channel_name} does not exist.")
        return

    # if the channel exists, close connections of all clients in the channel
    while channels[channel_name].clients:
        client = channels[channel_name].clients.pop()
        client.connection.close()

    print(f"[Server message ({time.strftime('%H:%M:%S')})] {channel_name} has been emptied.")


def mute_user(command, channels) -> None:
    """
    Implement /mute function
    Status: TODO
    Args:
        channels (dict): A dictionary of all channels.
        channel_name (str): The name of the channel to mute the user in.
    Returns:
        None
    """
    # Write your code here...
    # validate the command structure
    args = command.split()
    if len(args) != 4:
        # print(f"[Server message ({time.strftime('%H:%M:%S')})] "
        #       f"Usage /mute <channel_name> <username> <time>")
        return

    channel_name, username, mute_time = args[1], args[2], args[3]

    # check if the mute time is valid
    if not mute_time.isdigit() or int(mute_time) <= 0:
        print(f"[Server message ({time.strftime('%H:%M:%S')})] Invalid mute time.")
        return

    # check if the channel exists in the server
    if channel_name not in channels:
        print(f"[Server message ({time.strftime('%H:%M:%S')})] {username} is not here.")
        return

    # if the channel exists, check if the user is in the channel
    for client in channels[channel_name].clients:
        # if user is in the channel, mute it and send messages to all clients
        if client.username == username:
            client.muted = True
            client.mute_duration = int(mute_time)

            print(f"[Server message ({time.strftime('%H:%M:%S')})] Muted {username} for {mute_time} seconds.")
            message = f"[Server message ({time.strftime('%H:%M:%S')})] You have been muted for {mute_time} seconds."
            client.connection.send(message.encode())

            message = f"[Server message ({time.strftime('%H:%M:%S')})] {username} has been muted for {mute_time} seconds."
            for other_client in channels[channel_name].clients:
                if other_client.username != username:
                    other_client.connection.send(message.encode())
            return

    # if user is not in the channel, print error message
    print(f"[Server message ({time.strftime('%H:%M:%S')})] {username} is not here.")


def shutdown(channels) -> None:
    """
    Implement /shutdown function
    Status: TODO
    Args:
        channels (dict): A dictionary of all channels.
    """
    # Write your code here...
    # close connections of all clients in all channels and exit the server
    for channel in channels.values():
        # Handle clients in channels
        for client in channel.clients:
            client.connection.close()

        # Handle clients in queue
        for queued_client in channel.queue.queue:
            queued_client.connection.close()

    print(f"[Server message {time.strftime('%H:%M:%S')}] Server is shutting down...")

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
    while True:
        try:
            for channel in channels.values():
                for client in channel.clients:
                    # if client is muted or in queue
                    if client.muted or client.in_queue:
                        continue

                    # check if client has exceeded their remaining time
                    if client.remaining_time <= 0:
                        if client.remaining_time <= 0:
                            client_afk_message = (f"[Server message ({time.strftime('%H:%M:%S')})] "
                                                  f" You went AFK, connection closed...")
                            client.connection.send(client_afk_message.encode())

                        broadcast_afk_message = (f"{client.username} went AFK.")
                        print(broadcast_afk_message)

                        # broadcast the AFK message to all other clients in the channel
                        broadcast_in_channel(client, channel, broadcast_afk_message)

                        # remove client from the channel and close their connection
                        client.connection.close()
                        channel.clients.remove(client)


                    # if client is not muted, decrement their remaining time
                    else:
                        client.remaining_time -= 1
            time.sleep(0.99)
        except EOFError:
            continue


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
    try:
        if len(sys.argv) != 2:
            print("Usage python3 chatserver.py configfile")
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
    except KeyboardInterrupt:
        print("Crlt + C Pressed. Exiting...")
        os._exit(0)


if __name__ == "__main__":
    main()
