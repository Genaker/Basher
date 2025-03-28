"""
Basher - Main class that combines all functionality

This module provides the main Basher class that combines all the functionality
from the different components of the package.
"""
import os
from .core import BashCommand
from .file_ops import FileOps
from .system_ops import SystemOps
from .archive_ops import ArchiveOps
from .supervisord import SupervisorD

class Basher(BashCommand):
    """
    A class that combines all Basher functionality.
    """
    def __init__(self, working_dir=None):
        """Initialize the Basher object."""
        super().__init__(working_dir)
        self.file = FileOps(working_dir)
        self.system = SystemOps(working_dir, self.file)
        self.archive_ops = ArchiveOps(self.system)
        self.supervisor = SupervisorD()
        
    # File operations
    def write_to_file(self, file_path, content, mode='w'):
        """Write content to a file."""
        return self.file.write_to_file(file_path, content, mode)
    
    def read_file(self, file_path):
        """Read the contents of a file."""
        return self.file.read_file(file_path)
    
    def replace_in_file(self, file_path, start_pattern, new_string):
        """Replace lines in a file that match a pattern."""
        return self.file.replace_in_file(file_path, start_pattern, new_string)
    
    def string_exists_in_file(self, file_path, search_string):
        """Check if a string exists in a file."""
        return self.file.string_exists_in_file(file_path, search_string)
    
    def tail(self, file_path, n=20):
        """Tail a file."""
        return self.file.tail(file_path, n)
    
    def string_in_file(self, file_path, search_string):
        """Check if a string exists in a file."""
        return self.file.string_in_file(file_path, search_string)
    
    def copy(self, source, destination, recursive=True):
        """Copy a file or directory."""
        return self.file.copy(source, destination, recursive)
    
    def mv(self, source, destination):
        """Move or rename a file or directory."""
        return self.file.mv(source, destination)
    
    def find(self, directory, pattern):
        """Find files matching a pattern."""
        return self.file.find(directory, pattern)
    
    def exists(self, path):
        """Check if a file or directory exists."""
        return self.file.exists(path)
    
    def folder_exists(self, path):
        """Check if a directory exists."""
        return self.file.folder_exists(path)
    
    def chmod(self, path, permissions, recursive=True):
        """Change file permissions."""
        return self.file.chmod(path, permissions, recursive)
    
    def chown(self, path, user, group=None):
        """Change file ownership."""
        return self.file.chown(path, user, group)
    
    # System operations
    def detect_package_manager(self):
        """Detect the system's package manager."""
        return self.system.detect_package_manager()
    
    def install(self, packages, check_installed=True):
        """Install packages using the system's package manager."""
        return self.system.install(packages, check_installed)
    
    def purge(self, software):
        """Remove pakage"""
        return self.system.purge(software);
    
    def cd(self, directory_path):
        """Change the current working directory."""
        result = self.system.cd(directory_path)
        if result:
            # Update working_dir for all components
            self.working_dir = directory_path
            self.file.working_dir = directory_path
            self.archive_ops.working_dir = directory_path
        return result
    
    def pwd(self):
        """Get the current working directory."""
        return self.system.pwd()
    
    def mkdir(self, directory_path, exist_ok=True):
        """Create a directory."""
        return self.system.mkdir(directory_path, exist_ok)
    
    def rm(self, path, recursive=True):
        """Remove a file or directory."""
        return self.system.rm(path, recursive)
    
    # Archive operations
    def archive(self, source, archive_path, format='tar.gz'):
        """Create an archive."""
        return self.archive_ops.archive(source, archive_path, format)
    
    def extract(self, archive_path, destination=None):
        """Extract an archive."""
        return self.archive_ops.extract(archive_path, destination)
    
    def gzip(self, file_path, keep_original=False):
        """Compress a file with gzip."""
        return self.archive_ops.gzip(file_path, keep_original)
    
    def gunzip(self, file_path, keep_original=False):
        """Decompress a gzipped file."""
        return self.archive_ops.gunzip(file_path, keep_original)
    
    def download(self, url, destination=None):
        """Download a file from a URL."""
        return self.archive_ops.download(url, destination)
    
    def echo(self, message, color=None, end='\n'):
        """
        Print a message to the console using the native echo command.
        
        :param message: The message to print.
        :param color: Optional color to use ('red', 'green', 'yellow', 'blue', 'purple', 'cyan').
                      If None, no color is applied.
        :param end: The string to append after the message (default: newline).
        :return: True if successful, False otherwise.
        """
        # ANSI color codes
        colors = {
            'red': '\033[0;31m',
            'green': '\033[0;32m',
            'yellow': '\033[0;33m',
            'blue': '\033[0;34m',
            'purple': '\033[0;35m',
            'cyan': '\033[0;36m',
            'reset': '\033[0m'
        }
        
        # Escape single quotes in the message
        escaped_message = message.replace("'", "'\\''")
        
        # Apply color if specified
        if color and color.lower() in colors:
            color_code = colors[color.lower()]
            reset_code = colors['reset']
            escaped_message = f"{color_code}{escaped_message}{reset_code}"
            # Always use -e flag when we have color codes
            e_flag = ""
        else:
            # No -e flag needed for plain text
            e_flag = ""
        
        # Handle the end parameter
        if end == '\n':
            # Standard newline behavior
            cmd_str = f"echo {e_flag} \"{escaped_message}\""
        else:
            # Custom end character - suppress newline and add custom end
            escaped_end = end.replace("'", "'\\''")
            if e_flag:
                # If we're using -e for colors, combine with -n
                cmd_str = f"echo {e_flag} -n '{escaped_message}' && echo -n '{escaped_end}'"
            else:
                # Just use -n for suppressing newline
                cmd_str = f"echo -n '{escaped_message}' && echo -n '{escaped_end}'"
        
        # Execute the command
        return self.cmd(cmd_str.strip(), capture_output=False) is not None

    def ensure_sudo(self):
        """
        Check if sudo is installed and install it if not.
        
        :return: True if sudo is available (either already installed or successfully installed), False otherwise.
        """
        return self.system.ensure_sudo()

    def if_condition(self, condition):
        """
        Start a conditional block based on a shell condition.
        
        :param condition: The condition to check (e.g., "test -f /path/to/file")
        :return: True if the condition is true, False otherwise.
        """
        return super().if_condition(condition)

    # Alias for if_condition
    def if_(self, condition):
        """Alias for if_condition."""
        return self.if_condition(condition)

    def elif_condition(self, condition):
        """
        Add an elif branch to a conditional block.
        
        :param condition: The condition to check (e.g., "test -f /path/to/file")
        :return: True if the condition is true and no previous if/elif was true, False otherwise.
        """
        return super().elif_condition(condition)

    # Alias for elif_condition
    def elif_(self, condition):
        """Alias for elif_condition."""
        return self.elif_condition(condition)

    def else_condition(self):
        """
        Add an else branch to a conditional block.
        
        :return: True if no previous if/elif was true, False otherwise.
        """
        return super().else_condition()

    # Alias for else_condition
    def else_(self):
        """Alias for else_condition."""
        return self.else_condition()

    def ifend(self):
        """
        End a conditional block.
        """
        return super().ifend()

    # Alias for ifend
    def endif(self):
        """Alias for ifend."""
        return self.ifend()
    
    def env_var(self, var_name, value=None):
        """Manage environment variables."""
        return self.system.env_var(var_name, value)

