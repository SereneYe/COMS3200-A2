import re
import os
import time
import signal
import tempfile
import subprocess

import random

def update_config_file(config_path):
    with open(config_path, "r") as file:
        lines = file.readlines()

    updated_ports = []
    for i, line in enumerate(lines):
        parts = line.split()
        if len(parts) >= 3 and parts[0] == "channel":
            # Replace the port number with a random number between 2000 and 50000
            parts[2] = str(random.randint(2000, 50000))
            lines[i] = " ".join(parts) + "\n"
            updated_ports.append(parts[2])

    with open(config_path, "w") as file:
        file.writelines(lines)
    
    return updated_ports


class PublicTestcasesScenarioOne:
    def __init__(self,
                 server_path="mchatserver.py",
                 client_path="mchatclient.py",
                 config_path="configs1.txt",
                 client_name="Alice"):
        # randomise the port number in the config file
        updated_ports = update_config_file(config_path)
        self.port_number = str(updated_ports[0])

        # Start server
        self.server_process = subprocess.Popen(['python3', server_path, config_path],
                                                stdin=subprocess.PIPE,
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE)
        time.sleep(1)  # Wait for server to start

        # Start client
        self.client_process_one = subprocess.Popen(['python3', client_path, self.port_number, client_name],
                                                stdin=subprocess.PIPE,  # Redirect stdin
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE)

        time.sleep(1)  # Wait for client to start

        self.GREEN = '\033[32m'  # Green text
        self.RED = '\033[31m'  # Red text
        self.RESET = '\033[0m'  # Reset to default color

    def interact(self):

        try:
            # step 1: joined client says Hi.
            msg = "Hi\n"
            self.client_process_one.stdin.write(msg.encode())
            self.client_process_one.stdin.flush()
            time.sleep(0.5)

            # step 2: join another client
            self.client_process_two = subprocess.Popen(['python3', 'mchatclient.py', self.port_number, 'Bob'],
                                                        stdin=subprocess.PIPE,  # Redirect stdin
                                                        stdout=subprocess.PIPE,
                                                        stderr=subprocess.PIPE)
            time.sleep(1)  # Wait for client to start

            # step 3: Alice sends a file to Bob
            self.creation_time = os.path.getctime("configs1.txt")
            msg = "/send Bob configs1.txt\n"
            self.client_process_one.stdin.write(msg.encode())
            self.client_process_one.stdin.flush()
            time.sleep(0.5)

            # step 4: join another client
            self.client_process_three = subprocess.Popen(['python3', 'mchatclient.py', self.port_number, 'Charlie'],
                                                        stdin=subprocess.PIPE,  # Redirect stdin
                                                        stdout=subprocess.PIPE,
                                                        stderr=subprocess.PIPE)
            time.sleep(1)  # Wait for client to start

            # step 5: Charlie says Hi
            msg = "Hi\n"
            self.client_process_three.stdin.write(msg.encode())
            self.client_process_three.stdin.flush()
            time.sleep(0.5)

            # step 6: /kick Charlie
            msg = "/kick abc Charlie\n"
            self.server_process.stdin.write(msg.encode())
            self.server_process.stdin.flush()
            time.sleep(0.5)

            # step 7: /quit by Bob
            msg = "/quit\n"
            self.client_process_two.stdin.write(msg.encode())
            self.client_process_two.stdin.flush()
            time.sleep(0.5)

            # step 8: /shutdown by server
            msg = "/shutdown\n"
            self.server_process.stdin.write(msg.encode())
            self.server_process.stdin.flush()
            time.sleep(0.5)

            # ctrl + c for server and all client processes
            time.sleep(1)
            self.server_process.send_signal(signal.SIGINT)
            self.client_process_one.send_signal(signal.SIGINT)
            self.client_process_two.send_signal(signal.SIGINT)
            self.client_process_three.send_signal(signal.SIGINT)
            time.sleep(1)

            # terminate the server process
            self.server_process.terminate()
            time.sleep(1)

            # capture and print server output
            server_outputs, self.server_error = self.server_process.communicate(timeout=200)

            self.server_outputs = server_outputs.decode().strip()
            # print("server_outputs:\n" + self.server_outputs)
            # print("server_error:\n" + self.server_error.decode())
            time.sleep(1)

            # terminate the client process
            self.client_process_one.terminate()
            self.client_process_two.terminate()
            self.client_process_three.terminate()
            time.sleep(1)

            # capture and print client output
            client_one_outputs, self.client_one_error = self.client_process_one.communicate(timeout=200)
            client_two_outputs, self.client_two_error = self.client_process_two.communicate(timeout=200)
            client_three_outputs, self.client_three_error = self.client_process_three.communicate(timeout=200)

            # check client output
            self.client_one_outputs = client_one_outputs.decode().strip()
            self.client_two_outputs = client_two_outputs.decode().strip()
            self.client_three_outputs = client_three_outputs.decode().strip()
            # print("Client outputs:")
            # print("client_one_outputs:\n" + self.client_one_outputs)
            # print("client_two_outputs:\n" + self.client_two_outputs)
            # print("client_three_outputs:\n" + self.client_three_outputs)
            
            # print("Client errors:")
            # print("client_one_error:\n" + self.client_one_error.decode())
            # print("client_two_error:\n" + self.client_two_error.decode())
            # print("client_three_error:\n" + self.client_three_error.decode())
        
        except Exception as e:
            print(f"{self.RED}Interaction failed:{self.RESET}", e)

    def test_first_client_joins(self):
        server_expected_output = [
            r"\[Server message \((\d{2}:\d{2}:\d{2})\)\] Alice has joined the abc channel.",
            r"\[Alice \((\d{2}:\d{2}:\d{2})\)\] Hi"
        ]
        client_one_expected_output = [
            r"\[Server message \((\d{2}:\d{2}:\d{2})\)\] Welcome to the abc channel, Alice.",
            r"\[Server message \((\d{2}:\d{2}:\d{2})\)\] Alice has joined the channel.",
            r"\[Alice \((\d{2}:\d{2}:\d{2})\)\] Hi"
        ]

        try:
            server_outputs = self.server_outputs.split("\n")
            assert re.fullmatch(server_expected_output[0], server_outputs[0]), "Server output 0 does not match"
            assert re.fullmatch(server_expected_output[1], server_outputs[1]), "Server output 1 does not match"

            client_one_outputs = self.client_one_outputs.split("\n")
            assert re.fullmatch(client_one_expected_output[0], client_one_outputs[0]), "Client 1 output 0 does not match"
            assert re.fullmatch(client_one_expected_output[1], client_one_outputs[1]), "Client 1 output 1 does not match"
            assert re.fullmatch(client_one_expected_output[2], client_one_outputs[2]), "Client 1 output 2 does not match"
        
        except Exception as e:
            print(f"{self.RED}First client joins test failed:{self.RESET}", e)
        else:
            print(f"{self.GREEN}First client joins test passed!{self.RESET}")
    
    def test_second_client_joins(self):
        server_expected_output = [
            r"\[Server message \((\d{2}:\d{2}:\d{2})\)\] Bob has joined the abc channel."
        ]
        client_one_expected_output = [
            r"\[Server message \((\d{2}:\d{2}:\d{2})\)\] Bob has joined the channel.",
        ]
        client_two_expected_output = [
            r"\[Server message \((\d{2}:\d{2}:\d{2})\)\] Welcome to the abc channel, Bob.",
            r"\[Server message \((\d{2}:\d{2}:\d{2})\)\] Bob has joined the channel."
        ]

        try:
            server_outputs = self.server_outputs.split("\n")
            assert re.fullmatch(server_expected_output[0], server_outputs[2]), "Server output 2 does not match"

            client_one_outputs = self.client_one_outputs.split("\n")
            assert re.fullmatch(client_one_expected_output[0], client_one_outputs[3]), "Client 1 output 3 does not match"

            client_two_outputs = self.client_two_outputs.split("\n")
            assert re.fullmatch(client_two_expected_output[0], client_two_outputs[0]), "Client 2 output 0 does not match"
            assert re.fullmatch(client_two_expected_output[1], client_two_outputs[1]), "Client 2 output 1 does not match"
        
        except Exception as e:
            print(f"{self.RED}Second client joins test failed:{self.RESET}", e)
        else:
            print(f"{self.GREEN}Second client joins test passed!{self.RESET}")
    
    def test_file_transfer(self):
        server_expected_output = [
            r"\[Server message \((\d{2}:\d{2}:\d{2})\)\] Alice sent configs1.txt to Bob.",
        ]
        client_one_expected_output = [
            r"\[Server message \((\d{2}:\d{2}:\d{2})\)\] You sent configs1.txt to Bob."
        ]
        modified_time = os.path.getmtime("configs1.txt")

        try:
            server_outputs = self.server_outputs.split("\n")
            assert re.fullmatch(server_expected_output[0], server_outputs[3]), "Server output 3 does not match"

            client_one_outputs = self.client_one_outputs.split("\n")
            assert re.fullmatch(client_one_expected_output[0], client_one_outputs[4]), "Client 1 output 4 does not match"

            assert modified_time != self.creation_time, "File is not modified"

        except Exception as e:
            print(f"{self.RED}File transfer test failed:{self.RESET}", e)
        else:
            print(f"{self.GREEN}File transfer test passed!{self.RESET}")
    
    def test_third_client_joins(self):
        server_expected_output = [
            r"\[Server message \((\d{2}:\d{2}:\d{2})\)\] Charlie has joined the abc channel.",
            r"\[Charlie \((\d{2}:\d{2}:\d{2})\)\] Hi"
        ]
        client_one_expected_output = [
            r"\[Server message \((\d{2}:\d{2}:\d{2})\)\] Charlie has joined the channel.",
            r"\[Charlie \((\d{2}:\d{2}:\d{2})\)\] Hi"
        ]
        client_two_expected_output = [
            r"\[Server message \((\d{2}:\d{2}:\d{2})\)\] Charlie has joined the channel.",
            r"\[Charlie \((\d{2}:\d{2}:\d{2})\)\] Hi"
        ]
        client_three_expected_output = [
            r"\[Server message \((\d{2}:\d{2}:\d{2})\)\] Welcome to the abc channel, Charlie.",
            r"\[Server message \((\d{2}:\d{2}:\d{2})\)\] Charlie has joined the channel.",
            r"\[Charlie \((\d{2}:\d{2}:\d{2})\)\] Hi"
        ]

        try:
            server_outputs = self.server_outputs.split("\n")
            assert re.fullmatch(server_expected_output[0], server_outputs[4]), "Server output 4 does not match"
            assert re.fullmatch(server_expected_output[1], server_outputs[5]), "Server output 5 does not match"

            client_one_outputs = self.client_one_outputs.split("\n")
            assert re.fullmatch(client_one_expected_output[0], client_one_outputs[5]), "Client 1 output 5 does not match"
            assert re.fullmatch(client_one_expected_output[1], client_one_outputs[6]), "Client 1 output 6 does not match"

            client_two_outputs = self.client_two_outputs.split("\n")

            assert re.fullmatch(client_two_expected_output[0], client_two_outputs[2]), "Client 2 output 2 does not match"
            assert re.fullmatch(client_two_expected_output[1], client_two_outputs[3]), "Client 2 output 3 does not match"

            client_three_outputs = self.client_three_outputs.split("\n")
            assert re.fullmatch(client_three_expected_output[0], client_three_outputs[0]), "Client 3 output 0 does not match"
            assert re.fullmatch(client_three_expected_output[1], client_three_outputs[1]), "Client 3 output 1 does not match"
            assert re.fullmatch(client_three_expected_output[2], client_three_outputs[2]), "Client 3 output 2 does not match"

        except Exception as e:
            print(f"{self.RED}Third client joins test failed:{self.RESET}", e)
        else:
            print(f"{self.GREEN}Third client joins test passed!{self.RESET}")

    def test_kick_command(self):
        server_expected_output = [
            r"\[Server message \((\d{2}:\d{2}:\d{2})\)\] Kicked Charlie."
        ]
        client_one_expected_output = [
            r"\[Server message \((\d{2}:\d{2}:\d{2})\)\] Charlie has left the channel."
        ]
        client_two_expected_output = [
            r"\[Server message \((\d{2}:\d{2}:\d{2})\)\] Charlie has left the channel."
        ]

        try:
            server_outputs = self.server_outputs.split("\n")
            assert re.fullmatch(server_expected_output[0], server_outputs[6]), "Server output 6 does not match"

            client_one_outputs = self.client_one_outputs.split("\n")

            assert re.fullmatch(client_one_expected_output[0], client_one_outputs[7]), "Client 1 output 7 does not match"

            client_two_outputs = self.client_two_outputs.split("\n")
            assert re.fullmatch(client_two_expected_output[0], client_two_outputs[4]), "Client 2 output 4 does not match"
        
        except Exception as e:
            print(f"{self.RED}Kick command test failed:{self.RESET}", e)
        else:
            print(f"{self.GREEN}Kick command test passed!{self.RESET}")

    def test_quit_command(self):
        client_one_expected_output = [
            r"\[Server message \((\d{2}:\d{2}:\d{2})\)\] Bob has left the channel."
        ]

        try:
            client_one_outputs = self.client_one_outputs.split("\n")
            assert re.fullmatch(client_one_expected_output[0], client_one_outputs[8]), "Client 1 output 8 does not match"
        
        except Exception as e:
            print(f"{self.RED}Quit command test failed:{self.RESET}", e)
        else:
            print(f"{self.GREEN}Quit command test passed!{self.RESET}")


if __name__ == "__main__":
    testcases = PublicTestcasesScenarioOne()
    testcases.interact()
    testcases.test_first_client_joins()
    testcases.test_second_client_joins()
    testcases.test_file_transfer()
    testcases.test_third_client_joins()
    testcases.test_kick_command()
    testcases.test_quit_command()
