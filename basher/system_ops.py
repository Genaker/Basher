"""System operations for Basher."""

import os
import subprocess
from .core import BashCommand
from .shell_utils import quote

class SystemOps(BashCommand):
    """
    A class that provides system operation methods.
    """

    # Initialize package_manager as None (not detected yet)
    package_manager = None

    
    def __init__(self, working_dir=None, file_ops=None):
        """Initialize the SystemOps object."""
        super().__init__(working_dir)
        self.file_ops = file_ops
    
    def detect_package_manager(self):
        """
        Detect the system's package manager.
        
        :return: The package manager name ('apt', 'yum', 'dnf', 'pacman', etc.) or None if not detected.
        """
        # If we've already detected the package manager, return the cached value
        if self.package_manager is not None:
            return self.package_manager
            
        # Check for apt (Debian, Ubuntu)
        if self.cmd("which apt", show_output=False, check=False) == 0:
            self.package_manager = "apt"
        # Check for yum (CentOS, RHEL)
        elif self.cmd("which yum", show_output=False, check=False) == 0:
            self.package_manager = "yum"
        # Check for dnf (Fedora)
        elif self.cmd("which dnf", show_output=False, check=False) == 0:
            self.package_manager = "dnf"
        # Check for pacman (Arch)
        elif self.cmd("which pacman", show_output=False, check=False) == 0:
            self.package_manager = "pacman"
        # No supported package manager found
        else:
            self.package_manager = None

        if self.get_verbosity() > 0:
            self.info("Apt package manager detected")
            
        return self.package_manager
    
    def install(self, packages, check_installed=True):
        """
        Install packages using the system's package manager.
        
        :param packages: Package(s) to install. Can be a string for a single package or a list of packages.
        :return: True if successful, False otherwise.
        """
        # Handle empty input
        if not packages:
            return True
        
        # Convert string to list if a single package is provided
        if isinstance(packages, str):
            packages = [packages]

        if check_installed:
            for package in packages:
                if self.cmd(f"apt list --installed | grep -F {quote(package)}", show_output=False, check=False) == 0:
                    self.info(f"{package} is already installed")
                    return True
        
        # Quote each package to prevent injection
        packages_str = " ".join(quote(p) for p in packages)
        
        package_manager = self.detect_package_manager()
        
        if not package_manager:
            self.error("No supported package manager detected")
            return False
        
        try:
            if package_manager == "apt":
                return self.cmd(f"sudo apt update && sudo apt install -y {packages_str}") is not None
            elif package_manager == "yum":
                return self.cmd(f"sudo yum install -y {packages_str}") is not None
            elif package_manager == "dnf":
                return self.cmd(f"sudo dnf install -y {packages_str}") is not None
            elif package_manager == "pacman":
                return self.cmd(f"sudo pacman -Sy --noconfirm {packages_str}") is not None
            else:
                self.error(f"Unsupported package manager: {package_manager}")
                return False
        except Exception as e:
            self.error(f"Failed to install packages: {e}")
            return False
    
    def purge(self, software):
        """
        Remove a package from the system using apt-get purge.

        :param software: Name of the software package to remove.
        """
        try:
            return self.cmd(f"sudo apt-get purge -y {quote(software)}*", check=True)
        except Exception as e:
            self.error(f"Failed to purge {software}. Error: {e}")
    
    def cd(self, directory_path):
        """
        Change the current working directory.
        
        :param directory_path: Path to the directory.
        :return: True if successful, False otherwise.
        """
        if not os.path.isdir(directory_path):
            self.error(f"Directory '{directory_path}' does not exist")
            return False
        
        try:
            os.chdir(directory_path)
            self.working_dir = directory_path
            return True
        except Exception as e:
            self.error(f"Failed to change directory: {e}")
            return False
    
    def mkdir(self, directory_path, exist_ok=True):
        """
        Create a directory.
        
        :param directory_path: Path to the directory.
        :param exist_ok: If True, don't raise an error if the directory already exists.
        :return: True if successful, False otherwise.
        """
        if os.path.exists(directory_path) and not exist_ok:
            self.error(f"Path '{directory_path}' already exists")
            return False
        
        try:
            result = subprocess.run(f"mkdir -p {quote(directory_path)}", shell=True)
            return result.returncode == 0
        except Exception as e:
            self.error(f"Failed to create directory: {e}")
            return False
    
    def rm(self, path, recursive=True):
        """
        Remove a file or directory.
        
        :param path: Path to the file or directory.
        :param recursive: If True, remove directories and their contents recursively.
        :return: True if successful, False otherwise.
        """
        if not self.exists(path):
            self.error(f"Path '{path}' does not exist")
            return False
        
        try:
            if os.path.isfile(path) or os.path.islink(path):
                result = subprocess.run(f"rm {quote(path)}", shell=True)
                return result.returncode == 0
            elif os.path.isdir(path):
                if recursive:
                    result = subprocess.run(f"rm -rf {quote(path)}", shell=True)
                    return result.returncode == 0
                else:
                    result = subprocess.run(f"rmdir {quote(path)} 2>/dev/null", shell=True)
                    return result.returncode == 0
            return False
        except Exception as e:
            print(f"Failed to remove path: {e}")
            return False
    
    def ensure_sudo(self):
        """
        Check if sudo is installed and install it if not.
        
        :return: True if sudo is available (either already installed or successfully installed), False otherwise.
        """
        # Check if sudo is already installed
        if self.cmd("which sudo", show_output=False, check=False):
            self.info("sudo is already installed")
            return True
        
        self.warning("sudo is not installed. Attempting to install it...")
        
        try:
            # Try to install sudo using the system's package manager
            package_manager = self.detect_package_manager()
            
            if package_manager == "apt":
                result = self.cmd("apt update && apt install -y sudo", capture_output=False)
                return result is not None
            elif package_manager == "yum":
                result = self.cmd("yum install -y sudo", capture_output=False)
                return result is not None
            elif package_manager == "dnf":
                result = self.cmd("dnf install -y sudo", capture_output=False)
                return result is not None
            elif package_manager == "pacman":
                result = self.cmd("pacman -Sy --noconfirm sudo", capture_output=False)
                return result is not None
            else:
                self.error("Could not install sudo: unsupported package manager")
                return False
        except Exception as e:
            self.error(f"Failed to install sudo: {e}")
            return False

    def exists(self, path):
        """
        Check if a file or directory exists.
        
        :param path: Path to check.
        :return: True if the path exists, False otherwise.
        """
        if self.file_ops:
            return self.file_ops.exists(path)
        else:
            result = subprocess.run(f"[ -e {quote(path)} ]", shell=True)
            return result.returncode == 0

    def folder_exists(self, path):
        """
        Check if a directory exists.
        
        :param path: Path to check.
        :return: True if the directory exists, False otherwise.
        """
        if self.file_ops:
            return self.file_ops.folder_exists(path)
        else:
            result = subprocess.run(f"[ -d {quote(path)} ]", shell=True)
            return result.returncode == 0
        
    def pwd(self):
        """
        Get the current working directory.
        """
        return self.cmd("pwd", show_output=True)

    def command_exists(self, command):
        """
        Check if a command exists in PATH.

        :param command: Command name to check (e.g. 'php', 'supervisord').
        :return: True if command exists, False otherwise.
        """
        return self.cmd(f"which {quote(command)}", show_output=False, check=False) == 0

    def user_exists(self, username):
        """
        Check if a system user exists.

        :param username: Username to check (e.g. 'elasticsearch', 'mysql').
        :return: True if user exists, False otherwise.
        """
        return self.cmd(f"getent passwd {quote(username)}", show_output=False, check=False) == 0

    def add_apt_repository(self, ppa):
        """
        Add an apt PPA repository. Requires software-properties-common.

        :param ppa: PPA spec (e.g. 'ppa:ondrej/php').
        :return: True if successful, False otherwise.
        """
        return self.cmd(f"add-apt-repository -y {quote(ppa)}") == 0

    def composer_install(self, no_scripts=False, working_dir=None):
        """
        Run composer install.

        :param no_scripts: If True, skip Composer scripts (e.g. post-install).
        :param working_dir: Directory to run in (default: self.working_dir).
        :return: True if successful, False otherwise.
        """
        flags = " --no-scripts" if no_scripts else ""
        return self.cmd(f"composer install{flags}", cwd=working_dir or self.working_dir) == 0

    def npm_install(self, prefix=None):
        """
        Run npm install.

        :param prefix: Directory to install in (npm --prefix).
        :return: True if successful, False otherwise.
        """
        cmd = f"npm install --prefix {quote(prefix)}" if prefix else "npm install"
        return self.cmd(cmd) == 0

    def service_start(self, service_name):
        """
        Start a system service.

        :param service_name: Service name (e.g. 'nginx', 'php8.3-fpm').
        :return: True if successful, False otherwise.
        """
        return self.cmd(f"service {quote(service_name)} start") == 0
    
    def env_var(self, var_name, value=None):
        """
        Manage environment variables.
        
        :param var_name: Name of the environment variable.
        :param value: Value to set for the environment variable.
        :return: The value of the environment variable.
        """
        if value is not None:
            # Set the environment variable
            # print(f"{self.YELLOW}CMD#{self.RESET} export {var_name}='{value}'")  # For Unix-like systems

            self.cmd(f"export {var_name}={quote(str(value))}", emulate=True);
            self.env_vars[var_name] = str(value).strip()
            # Set environment variable in Python otherwise it will not work
            os.environ[var_name] = str(value).strip()
            # bash.cmd(f"set {var_name}={value}")  # For Windows systems
            result = value
        else:
            # Get the environment variable
            sh_result = self.cmd(f"echo ${var_name}", show_output=True, capture_output=True).strip();
            result = os.environ[var_name]
            # self.cmd(f"echo ${var_name}", show_output=True, capture_output=True);
            # print(f"{self.YELLOW}CMD#{self.RESET} echo ${var_name}")  # For Unix-like systems
            # result = bash.cmd(f"echo %{var_name}%").strip()  # For Windows systems
            self.echo(f"The value of {var_name} is: [{result}]")
        return result
