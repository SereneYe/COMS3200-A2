import signal
import subprocess
import random
import time
import re

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

class PublicTestcasesScenarioTwo:
    def __init__(self,
                 server_path="mchatserver.py",
                 client_path="mchatclient.py",
                 config_path="configs2.txt",
                 port_number="5555",
                 client_name="Alice"):
        
        # Update config file
        self.port_numbers = update_config_file(config_path)

        # Start server
        self.server_process = subprocess.Popen(['python3', server_path, config_path],
                                                stdin=subprocess.PIPE,
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE)
        time.sleep(1)  # Wait for server to start

        # Start client
        self.client_one_in_abc = subprocess.Popen(['python3', client_path, str(self.port_numbers[0]), client_name],
                                                    stdin=subprocess.PIPE,  # Redirect stdin
                                                    stdout=subprocess.PIPE,
                                                    stderr=subprocess.PIPE)

        time.sleep(1)  # Wait for client to start

        self.GREEN = '\033[32m'  # Green text
        self.RED = '\033[31m'  # Red text
        self.RESET = '\033[0m'  # Reset to default color

    def interact(self):

        try:
            # step 1: join another client in abc
            self.client_two_in_abc = subprocess.Popen(['python3', 'mchatclient.py', str(self.port_numbers[0]), 'Bob'],
                                                        stdin=subprocess.PIPE,  # Redirect stdin
                                                        stdout=subprocess.PIPE,
                                                        stderr=subprocess.PIPE)
            
            # step 2: join a client in def
            self.client_one_in_def = subprocess.Popen(['python3', 'mchatclient.py', str(self.port_numbers[1]), 'Charlie'],
                                                        stdin=subprocess.PIPE,  # Redirect stdin
                                                        stdout=subprocess.PIPE,
                                                        stderr=subprocess.PIPE)
            time.sleep(1)  # Wait for client to start

            # step 3: Alice uses /list
            msg = "/list\n"
            self.client_one_in_abc.stdin.write(msg.encode())
            self.client_one_in_abc.stdin.flush()
            time.sleep(0.5)

            # step 4: Alice /whispers to Bob
            msg = "/whisper Bob Heya!\n"
            self.client_one_in_abc.stdin.write(msg.encode())
            self.client_one_in_abc.stdin.flush()
            time.sleep(0.5)

            # step 5: Alice /switch to def
            msg = "/switch def\n"
            self.client_one_in_abc.stdin.write(msg.encode())
            self.client_one_in_abc.stdin.flush()
            time.sleep(0.5)

            # step 6: /mute Alice for 20 seconds
            msg = "/mute def Alice 20\n"
            self.server_process.stdin.write(msg.encode())
            self.server_process.stdin.flush()
            time.sleep(0.5)

            # step 7: wait for Charlie to go on AFK
            # time.sleep(100)

            # step 8: empty the def channel
            msg = "/empty def\n"
            self.server_process.stdin.write(msg.encode())
            self.server_process.stdin.flush()
            time.sleep(0.5)

            # step 7.5: Bob uses /list
            msg = "/list\n"
            self.client_two_in_abc.stdin.write(msg.encode())
            self.client_two_in_abc.stdin.flush()
            time.sleep(0.5)

            # step 8: /shutdown by server
            msg = "/shutdown\n"
            self.server_process.stdin.write(msg.encode())
            self.server_process.stdin.flush()
            time.sleep(0.5)

            # ctrl+c for server and all client processes
            time.sleep(1)
            self.server_process.send_signal(signal.SIGINT)
            self.client_one_in_abc.send_signal(signal.SIGINT)
            self.client_two_in_abc.send_signal(signal.SIGINT)
            self.client_one_in_def.send_signal(signal.SIGINT)
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

            # terminate the client processes
            self.client_one_in_abc.terminate()
            self.client_one_in_abc.wait()  # Wait for the process to terminate
            self.client_two_in_abc.terminate()
            self.client_two_in_abc.wait()  # Wait for the process to terminate
            self.client_one_in_def.terminate()
            self.client_one_in_def.wait()  # Wait for the process to terminate
            time.sleep(1)            

            # capture and print client output
            client_one_in_abc_op, self.client_one_error = self.client_one_in_abc.communicate(timeout=200)
            client_two_in_abc_op, self.client_two_error = self.client_two_in_abc.communicate(timeout=200)
            client_one_in_def_op, self.client_three_error = self.client_one_in_def.communicate(timeout=200)

            # check client output
            self.client_one_in_abc_op = client_one_in_abc_op.decode().strip()
            self.client_two_in_abc_op = client_two_in_abc_op.decode().strip()
            self.client_one_in_def_op = client_one_in_def_op.decode().strip()
            # print("Client outputs:")
            # print("client_one_in_abc_op:\n" + self.client_one_in_abc_op)
            # print("client_two_in_abc_op:\n" + self.client_two_in_abc_op)
            # print("client_one_in_def_op:\n" + self.client_one_in_def_op)
            
            # print("Client errors:")
            # print("client_one_error:\n" + self.client_one_error.decode())
            # print("client_two_error:\n" + self.client_two_error.decode())
            # print("client_three_error:\n" + self.client_three_error.decode())
        
        except Exception as e:
            print(f"{self.RED}Interaction failed:{self.RESET}", e)
    
    def test_list_command(self):
        client_one_in_abc_exop = [
            rf"\[Channel\] abc {self.port_numbers[0]} Capacity: 2/ 3, Queue: 0.",
            rf"\[Channel\] def {self.port_numbers[1]} Capacity: 1/ 4, Queue: 0.",
            rf"\[Channel\] xyz {self.port_numbers[2]} Capacity: 0/ 5, Queue: 0."
        ]

        try:
            client_one_in_abc_op = self.client_one_in_abc_op.split("\n")

            assert re.fullmatch(client_one_in_abc_exop[0], client_one_in_abc_op[3]), "Client 1 in abc output 3 does not match"

            assert re.fullmatch(client_one_in_abc_exop[1], client_one_in_abc_op[4]), "Client 1 in abc output 4 does not match"
            assert re.fullmatch(client_one_in_abc_exop[2], client_one_in_abc_op[5]), "Client 1 in abc output 5 does not match"
        
        except Exception as e:
            print(f"{self.RED}List command test failed:{self.RESET}", e)
        else:
            print(f"{self.GREEN}List command test passed!{self.RESET}")
    
    def test_whisper_command(self):
        server_exop = [
            r"\[Alice whispers to Bob: \((\d{2}:\d{2}:\d{2})\)\] Heya!"
        ]
        client_two_in_abc_exop = [
            r"\[Alice whispers to you: \((\d{2}:\d{2}:\d{2})\)\] Heya!"
        ]

        try:
            server_op = self.server_outputs.split("\n")
            assert re.fullmatch(server_exop[0], server_op[3]), "Server output 3 does not match"

            client_two_in_abc_op = self.client_two_in_abc_op.split("\n")
            assert re.fullmatch(client_two_in_abc_exop[0], client_two_in_abc_op[2]), "Client 2 in abc output 2 does not match"

        except Exception as e:
            print(f"{self.RED}Whisper command test failed:{self.RESET}", e)
        else:
            print(f"{self.GREEN}Whisper command test passed!{self.RESET}")
    
    def test_switch_command(self):
        server_exop = [
            r"\[Server message \((\d{2}:\d{2}:\d{2})\)\] Alice has left the channel.",
            r"\[Server message \((\d{2}:\d{2}:\d{2})\)\] Alice has joined the def channel."
        ]
        client_one_in_abc_exop = [
            r"\[Server message \((\d{2}:\d{2}:\d{2})\)\] Welcome to the def channel, Alice.",
            r"\[Server message \((\d{2}:\d{2}:\d{2})\)\] Alice has joined the channel."
        ]
        client_two_in_abc_exop = [
            r"\[Server message \((\d{2}:\d{2}:\d{2})\)\] Alice has left the channel."
        ]
        client_one_in_def_exop = [
            r"\[Server message \((\d{2}:\d{2}:\d{2})\)\] Alice has joined the channel.",
        ]

        try:
            server_op = self.server_outputs.split("\n")
            assert re.fullmatch(server_exop[0], server_op[4]), "Server output 4 does not match"
            assert re.fullmatch(server_exop[1], server_op[5]), "Server output 5 does not match"

            client_one_in_abc_op = self.client_one_in_abc_op.split("\n")

            assert re.fullmatch(client_one_in_abc_exop[0], client_one_in_abc_op[6]), "Client 1 in abc output 6 does not match"
            assert re.fullmatch(client_one_in_abc_exop[1], client_one_in_abc_op[7]), "Client 1 in abc output 7 does not match"

            client_two_in_abc_op = self.client_two_in_abc_op.split("\n")
            assert re.fullmatch(client_two_in_abc_exop[0], client_two_in_abc_op[3]), "Client 2 in abc output 3 does not match"

            client_one_in_def_op = self.client_one_in_def_op.split("\n")
            assert re.fullmatch(client_one_in_def_exop[0], client_one_in_def_op[2]), "Client 1 in def output 3 does not match"
        
        except Exception as e:
            print(f"{self.RED}Switch command test failed:{self.RESET}", e)
        else:
            print(f"{self.GREEN}Switch command test passed!{self.RESET}")
    
    def test_mute_command(self):
        server_exop = [
            r"\[Server message \((\d{2}:\d{2}:\d{2})\)\] Muted Alice for 20 seconds."
        ]
        client_one_in_abc_exop = [
            r"\[Server message \((\d{2}:\d{2}:\d{2})\)\] You have been muted for 20 seconds."
        ]
        client_one_in_def_exop = [
            r"\[Server message \((\d{2}:\d{2}:\d{2})\)\] Alice has been muted for 20 seconds."
        ]

        try:
            server_op = self.server_outputs.split("\n")
            assert re.fullmatch(server_exop[0], server_op[6]), "Server output 6 does not match"

            client_one_in_abc_op = self.client_one_in_abc_op.split("\n")
            assert re.fullmatch(client_one_in_abc_exop[0], client_one_in_abc_op[8]), "Client 1 in abc output 8 does not match"

            client_one_in_def_op = self.client_one_in_def_op.split("\n")
            assert re.fullmatch(client_one_in_def_exop[0], client_one_in_def_op[3]), "Client 1 in def output 3 does not match"

        except Exception as e:
            print(f"{self.RED}Mute command test failed:{self.RESET}", e)
        else:
            print(f"{self.GREEN}Mute command test passed!{self.RESET}")

    def test_empty_command(self):
        server_exop = [
            r"\[Server message \((\d{2}:\d{2}:\d{2})\)\] def has been emptied."
        ]

        try:
            server_op = self.server_outputs.split("\n")

            assert re.fullmatch(server_exop[0], server_op[7]), "Server output 7 does not match"

        except Exception as e:
            print(f"{self.RED}Empty command test failed:{self.RESET}", e)
        else:
            print(f"{self.GREEN}Empty command test passed!{self.RESET}")

if __name__ == "__main__":
    testcases = PublicTestcasesScenarioTwo()
    testcases.interact()
    testcases.test_list_command()
    testcases.test_whisper_command()
    testcases.test_switch_command()
    testcases.test_mute_command()
    testcases.test_empty_command()
