"""Core functionality for Basher."""

import os
import subprocess

class BashCommand:
    """
    A class that provides basic bash command execution.
    """
    
    # ANSI color codes
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    ITALIC = '\033[3m'
    RESET = '\033[0m'  # Reset to default color

   
    # Initialize env_vars as an empty dictionary
    env_vars = {}
    # the directory to run the command in
    working_dir = None
    # the user run the command as
    current_user = None
     # Default to not show output you can set it to True to show output by default
    show_output = False

    def __init__(self, working_dir=None):
        """Initialize the BashCommand object.
        :param working_dir: The working directory to use for the commands by default it will use the current directory if not set.
        """
        if working_dir is None:
            self.working_dir = os.getcwd()
        else:
            if os.path.exists(working_dir):
                self.working_dir = working_dir
            else:
                raise ValueError(f"Working directory '{working_dir}' does not exist")
        
    
    def cmd(self, command, show_output=None, capture_output=False, check=True, cwd=None, user=None, detect_input_prompt=True, arguments=None, emulate=False, bashrc=False, executable='/bin/bash'):
        """
        Execute a bash SuperHerocommand.
        
        :param command: The command to execute.
        :param show_output: Whether to show the command output.
        :param capture_output: Whether to capture and return the command output.
        :param check: Whether to raise an exception if the command fails.
        :param cwd: The directory to execute the command in.
        :param detect_input_prompt: Whether to detect and raise an exception if the command requires input.
        :param arguments: Additional arguments to pass to the command.
        :param emulate: Whether to emulate the command and don't run it.
        :param bashrc: Whether to add bashrc file to the command.
        :return: The command output if capture_output is True, otherwise the return code.
        """
        import time
        import re
        
        # Use class properties as defaults if parameters are not provided
        if show_output is None:
            show_output = self.show_output  # Assuming self.show_output is defined elsewhere
        if cwd is None:
            cwd = self.working_dir
        if user is None:
            user = self.current_user

        if bashrc:
            command = f"source ~/.bashrc && {command}"
        
        # Get verbosity level (default to 1 if not set)
        verbosity = self.get_verbosity()
        result = None
     
        # If cwd is provided, temporarily change to that directory
        original_dir = None
        
        # Only show command if verbosity > 0
        if verbosity > 0:
            print(f"{self.YELLOW}CMD#{self.RESET} {command}")
        elif verbosity == 0:
            print(f"{self.YELLOW}CMD#{self.RESET} {command}")
        
        # If emulate is True, don't run the command
        if emulate:
            return 0
        
        if verbosity == 3:
            # Print positional arguments
            print(f"{self.BLUE}    Arguments->{self.RESET} show_output:{show_output}, capture_output:{capture_output}, user:{user}, check:{check}, cwd:{cwd}, detect_input_prompt:{detect_input_prompt}, bashrc:{bashrc}, executable:{executable}")

   
        if cwd:
            original_dir = os.getcwd()
            os.chdir(cwd)

        # Create a base arguments dictionary
        run_args = {'shell': True, 'capture_output': True, 'text': True, 'executable': executable, 'cwd': cwd, 'user': user}
                
        # Update with custom arguments if provided
        if arguments is not None:
            run_args.update(arguments)
        
        try:
            if verbosity == 0:
                run_args = {'shell': True, 'capture_output': True, 'text': True, 'user':user, 'executable': executable, 'cwd': cwd, 'user': user}
                
                # Update with custom arguments if provided
                if arguments is not None:
                    run_args.update(arguments)
                    
                # Run the command with the arguments
                result = subprocess.run(command, **run_args)
                
            # out put live progress if verbosity is greater than 0
            if verbosity > 0:
                
                run_args = {'shell': True, 'user':user, 'stdout': subprocess.PIPE, 'stderr': subprocess.PIPE, 'text': True, 'bufsize': 1, 'executable': executable, 'cwd': cwd, 'user': user}
                
                # Update with custom arguments if provided
                if arguments is not None:
                    run_args.update(arguments)
                # Use subprocess.Popen for better control over output
                process = subprocess.Popen(
                    command,
                    **run_args
                )
                
                # Collect output if needed
                stdout_output = ""
                stderr_output = ""
                
                # Patterns that indicate a command is waiting for input
                input_prompt_patterns = [
                    r"\[Y/n\]",
                    r"\[y/N\]",
                    r"password:",
                    r"Password:",
                    r"continue\?",
                    r"Do you want to continue",
                    r"Please enter",
                    r"Press \[ENTER\]",
                    r"Press Enter to continue",
                    r"debconf: DbDriver .* is locked by another process",
                    r"waiting for lock",
                    r"Formatting Code (en):"
                ]
                
                # Read output line by line
                while True:
                    # Read a line from stdout
                    stdout_line = process.stdout.readline()
                    if stdout_line:
                        # Only show output if verbosity level allows it or show_output is True
                        if verbosity > 0 or show_output:
                            print(f'{self.BLUE}     STDOUT#{self.RESET} {stdout_line.rstrip()}')
            
                        if capture_output:
                            stdout_output += stdout_line
                        
                        # Check for input prompts in stdout
                        if detect_input_prompt:
                            for pattern in input_prompt_patterns:
                                if re.search(pattern, stdout_line, re.IGNORECASE):
                                    # Kill the process
                                    if verbosity > 0:
                                        print(f"{self.RED}Command requires input: {command}\nPrompt detected: {stdout_line.strip()}{self.RESET}")
                                    process.terminate()
                                    try:
                                        process.wait(timeout=5)
                                    except subprocess.TimeoutExpired:
                                        if verbosity > 0:
                                            print(f"{self.RED}Command requires input: {command}\nPrompt detected: {stdout_line.strip()}{self.RESET}")
                                        process.kill()
                                        process.wait()
                                    
                                    # Raise an exception
                                    raise Exception(f"Command requires input: {command}\nPrompt detected: {stdout_line.strip()}")
                    
                    # Read a line from stderr
                    stderr_line = process.stderr.readline()
                    if stderr_line:
                        if verbosity > 0:
                            print(f'{self.BLUE}     STDERR#{self.RESET} {self.RED}{stderr_line.rstrip()}{self.RESET}')
                        # Only show errors if verbosity level allows it
                        if show_output and (verbosity > 0):
                            print(f"{self.RED}{stderr_line}{self.RESET}", end='')

                        
                        stderr_output += stderr_line
                        
                        # Check for input prompts in stderr
                        if detect_input_prompt:
                            for pattern in input_prompt_patterns:
                                if re.search(pattern, stderr_line, re.IGNORECASE):
                                    # Kill the process
                                    process.terminate()
                                    try:
                                        process.wait(timeout=5)
                                    except subprocess.TimeoutExpired:
                                        process.kill()
                                        process.wait()
                                    
                                    # Raise an exception
                                    raise Exception(f"Command requires input: {command}\nPrompt detected: {stderr_line.strip()}")
                    
                    # Check if process has ended and no more output
                    if not stdout_line and not stderr_line and process.poll() is not None:
                        if verbosity == 3:
                            print(f'{self.BLUE}Process has ended and no more output{self.RESET}')
                        break
                    
                    # If no output but process is still running, check if it's waiting for input
                    if not stdout_line and not stderr_line and process.poll() is None and detect_input_prompt:
                        print(f"{self.YELLOW}Command is waiting for input{self.RESET}")
                        # Sleep a bit to avoid busy waiting
                        time.sleep(100 / 1000)
                        
                        # Check if the process has been running for too long without output
                        # This could indicate it's waiting for input
                        if hasattr(process, '_start_time'):
                            if time.time() - process._start_time > 5:  # 5 seconds without output
                                # Check if the process is waiting for input using external tools
                                try:
                                    # Get the process ID
                                    pid = process.pid
                                    
                                    # Check if the process is reading from stdin
                                    result = subprocess.run(
                                        f"lsof -p {pid} | grep -E 'stdin|tty'",
                                        shell=True,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        text=True
                                    )
                                    
                                    if result.returncode == 0 and result.stdout.strip():
                                        # Process is reading from stdin, likely waiting for input
                                        process.terminate()
                                        try:
                                            process.wait(timeout=5)
                                        except subprocess.TimeoutExpired:
                                            process.kill()
                                            process.wait()
                                        
                                        # Raise an exception
                                        raise Exception(f"Command appears to be waiting for input: {command}")
                                except:
                                    # If the check fails, continue
                                    pass
                        else:
                            # Set the start time for the process
                            process._start_time = time.time()
                
                # Get the return code
                return_code = process.poll()
            else:
                return_code = result.returncode
                stdout_output = result.stdout
                stderr_output = result.stderr
            
            # Print output if requested
            if show_output:
                print(f"{self.BLUE}    OUTPUT#{self.RESET} {(stdout_output + stderr_output).rstrip()}")
                
            # Check for errors if requested
            if check and return_code != 0:
                if verbosity > 0:
                    if not show_output:
                        print(f"{self.BLUE}ERR OUTPUT:{self.RESET} {self.RED}{(stdout_output + stderr_output).rstrip()}{self.RESET}")
            
            # Print status based on verbosity
            if verbosity > 0:  # Only show status in verbose mode
                if return_code == 0:
                    print(f"{self.GREEN}Command completed successfully{self.RESET}")
            
            # Return combined output if requested
            if capture_output:
                if verbosity == 3:
                    print(f"{self.BLUE}    Captured Output->{self.RESET} {(stdout_output + stderr_output).rstrip()}")
                return stdout_output + stderr_output
            
            if verbosity > -1:
                print(f"{self.BLUE}    Return code:{self.RESET} {self.MAGENTA}[{return_code}]{self.RESET}")
            # If the command failed, print the output any way
            if return_code != 0 and stderr_output:
                print(f"Command failed with return code = {self.RED}[{return_code}]{self.RESET}")
                print(f"{self.BLUE}    ERR OUTPUT:{self.RESET} {self.RED}{(stdout_output + stderr_output).rstrip()}{self.RESET}")
            return return_code
        
        except Exception as e:
            print(f"{self.RED}Error executing command: {e}{self.RESET}")
            if capture_output:
                return "Exception: " + str(e)
            return 1
        
        finally:
            # Change back to the original directory if we changed it
            if original_dir:
                os.chdir(original_dir)
    
    def error(self, message):
        """
        Display an error message in red.
        
        :param message: The error message to display.
        """
        self.cmd(f"echo -e '{self.RED}{message}{self.RESET}'", capture_output=False)
    
    def warning(self, message):
        """
        Display a warning message in yellow.
        
        :param message: The warning message to display.
        """
        self.cmd(f"echo -e '{self.YELLOW}{message}{self.RESET}'", capture_output=False)
    
    def success(self, message):
        """
        Display a success message in green.
        
        :param message: The success message to display.
        """
        self.cmd(f"echo -e '{self.GREEN}{message}{self.RESET}'", capture_output=False)
    
    def info(self, message):
        """
        Display an info message in blue.
        
        :param message: The info message to display.
        """
        self.cmd(f"echo -e '{self.BLUE}{message}{self.RESET}'", capture_output=False)
    
    def execute_in_directory(self, command, directory, show_output=True):
        """
        Execute a command in a specific directory.
        
        :param command: The command to execute.
        :param directory: The directory to execute the command in.
        :param show_output: Whether to show the command output in real-time.
        :return: The command output if successful, otherwise None.
        """
        # Check if the directory exists
        result = subprocess.run(f"[ -d '{directory}' ]", shell=True)
        if result.returncode != 0:
            self.error(f"Directory '{directory}' does not exist")
            return None
        
        # Execute the command in the specified directory
        return self.cmd(f"cd '{directory}' && {command}", show_output=show_output)
    
        os.chdir(original_dir)

    def user(self, user=None):
        """
        Set the current user.
        
        :param user: The user to set.
        """
        if user is None:
            return self.current_user
        else:
            self.current_user = user
    
    def echo(self, message):
        """
        Display a message.
        
        :param message: The message to display.
        """
        print(message)

    def run(self, command, cwd=None):
        """
        Run a command and display its output in real-time.
        A simplified version of cmd that focuses on reliable output display.
        
        :param command: The command to execute.
        :param cwd: The directory to execute the command in.
        :return: True if the command succeeded, False otherwise.
        """
        print(f"{self.YELLOW}RUN#{self.RESET} {command}")
        
        # If cwd is provided, temporarily change to that directory
        original_dir = None
        if cwd:
            original_dir = os.getcwd()
            os.chdir(cwd)
        
        try:
            # Use the standard subprocess.run for simplicity and reliability
            # This won't show output in real-time, but it's more reliable
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True
            )
            
            # Print output after command completes
            if result.stdout:
                print(result.stdout)
            
            if result.stderr:
                print(f"{self.RED}{result.stderr}{self.RESET}")
            
            # Print status
            if result.returncode == 0:
                print(f"{self.GREEN}Command completed successfully{self.RESET}")
                return True
            else:
                print(f"{self.RED}Command failed with return code {result.returncode}{self.RESET}")
                return False
        
        except Exception as e:
            print(f"{self.RED}Error executing command: {e}{self.RESET}")
            return False
        
        finally:
            # Change back to the original directory if we changed it
            if original_dir:
                os.chdir(original_dir)
    
    def might_require_input(self, command):
        """
        Check if a command might require input.
        
        :param command: The command to check.
        :return: True if the command might require input, False otherwise.
        """
        # Commands that typically require input
        interactive_commands = [
            "apt install", "apt-get install",
            "apt remove", "apt-get remove",
            "apt upgrade", "apt-get upgrade",
            "apt dist-upgrade", "apt-get dist-upgrade",
            "dpkg-reconfigure",
            "mysql_secure_installation",
            "passwd",
            "adduser", "useradd",
            "visudo",
            "fdisk", "parted",
            "nano", "vim", "vi", "emacs",
            "ssh-keygen",
            "configure"
        ]
        
        # Check if the command contains any of the interactive commands
        for interactive_command in interactive_commands:
            if interactive_command in command and "-y" not in command and "DEBIAN_FRONTEND=noninteractive" not in command:
                return True
        
        return False
    
    def if_condition(self, condition):
        """
        Start a conditional block based on a shell condition.
        
        :param condition: The condition to check (e.g., "test -f /path/to/file")
        :return: True if the condition is true, False otherwise.
        """
        print(f"{self.YELLOW}IF#{self.RESET} {condition}")
        
        # Execute the condition
        result = subprocess.run(condition, shell=True)
        
        # Store the result for later use
        self._last_if_result = (result.returncode == 0)
        self._if_executed = self._last_if_result  # Track if any block in the if/elif/else chain has executed
        
        # Print the result
        if self._last_if_result:
            print(f"{self.GREEN}Condition is TRUE{self.RESET}")
        else:
            print(f"{self.RED}Condition is FALSE{self.RESET}")
        
        return self._last_if_result

    def elif_condition(self, condition):
        """
        Add an elif branch to a conditional block.
        
        :param condition: The condition to check (e.g., "test -f /path/to/file")
        :return: True if the condition is true and no previous if/elif was true, False otherwise.
        """
        if not hasattr(self, '_last_if_result'):
            raise RuntimeError("elif_condition() called without a preceding if_condition()")
        
        # If a previous condition was true, skip this one
        if self._if_executed:
            print(f"{self.YELLOW}ELIF#{self.RESET} {condition} {self.YELLOW}(SKIPPED){self.RESET}")
            return False
        
        print(f"{self.YELLOW}ELIF#{self.RESET} {condition}")
        
        # Execute the condition
        result = subprocess.run(condition, shell=True)
        
        # Store the result for later use
        self._last_if_result = (result.returncode == 0)
        if self._last_if_result:
            self._if_executed = True
        
        # Print the result
        if self._last_if_result:
            print(f"{self.GREEN}Condition is TRUE{self.RESET}")
        else:
            print(f"{self.RED}Condition is FALSE{self.RESET}")
        
        return self._last_if_result

    def else_condition(self):
        """
        Add an else branch to a conditional block.
        
        :return: True if no previous if/elif was true, False otherwise.
        """
        if not hasattr(self, '_last_if_result'):
            raise RuntimeError("else_condition() called without a preceding if_condition()")
        
        # If a previous condition was true, skip the else block
        if self._if_executed:
            print(f"{self.YELLOW}ELSE#{self.RESET} {self.YELLOW}(SKIPPED){self.RESET}")
            return False
        
        print(f"{self.YELLOW}ELSE#{self.RESET}")
        
        # The else block always executes if we get here
        self._last_if_result = True
        self._if_executed = True
        
        return True

    def ifend(self):
        """
        End a conditional block.
        """
        print(f"{self.YELLOW}ENDIF#{self.RESET}")
        
        # Reset the if state
        if hasattr(self, '_last_if_result'):
            del self._last_if_result
        if hasattr(self, '_if_executed'):
            del self._if_executed
    
    def set_verbosity(self, level):
        """
        Set the verbosity level for command output.
        
        :param level: Verbosity level (0=quiet, 1=normal, 2=verbose)
        :return: The set verbosity level
        """
        os.environ['BASHER_VERBOSITY'] = str(level)
        return int(level)

    def get_verbosity(self):
        """
        Get the current verbosity level.
        
        :return: The current verbosity level
        """
        return int(os.environ.get('BASHER_VERBOSITY', 0))