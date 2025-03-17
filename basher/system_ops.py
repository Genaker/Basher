"""System operations for Basher."""

import os
import subprocess
from .core import BashCommand

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
    
    def install(self, packages):
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
        
        # Convert list to space-separated string
        packages_str = " ".join(packages)
        
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
            result = subprocess.run(f"mkdir -p '{directory_path}'", shell=True)
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
                result = subprocess.run(f"rm '{path}'", shell=True)
                return result.returncode == 0
            elif os.path.isdir(path):
                if recursive:
                    result = subprocess.run(f"rm -rf '{path}'", shell=True)
                    return result.returncode == 0
                else:
                    # Try to remove an empty directory
                    result = subprocess.run(f"rmdir '{path}' 2>/dev/null", shell=True)
                    return result.returncode == 0
            return False
        except Exception as e:
            self.error(f"Failed to remove path: {e}")
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
            result = subprocess.run(f"[ -e '{path}' ]", shell=True)
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
            result = subprocess.run(f"[ -d '{path}' ]", shell=True)
            return result.returncode == 0
        
    def pwd(self):
        """
        Get the current working directory.
        """
        return self.cmd("pwd")
    
    def env_var(self, var_name, value=None):
        if value is not None:
            # Set the environment variable
            self.cmd(f"export {var_name}='{value}'")  # For Unix-like systems
            # bash.cmd(f"set {var_name}={value}")  # For Windows systems
            result = value
        else:
            # Get the environment variable
            result = self.cmd(f"echo ${var_name}", capture_output=True).strip()  # For Unix-like systems
            # result = bash.cmd(f"echo %{var_name}%").strip()  # For Windows systems
            self.echo(f"The value of {var_name} is: {result}")
        return result
