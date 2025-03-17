"""File operations for Basher."""

import os
import subprocess
import re
from .core import BashCommand

class FileOps(BashCommand):
    """
    A class that provides file operation methods.
    """
    
    def write_to_file(self, file_path, content, mode='w'):
        """
        Write content to a file.
        
        :param file_path: Path to the file.
        :param content: Content to write.
        :param mode: Write mode ('w' for write, 'a' for append).
        :return: True if successful, False otherwise.
        """
        if mode not in ['w', 'a']:
            raise ValueError("Mode must be 'w' (write) or 'a' (append)")
        
        redirect = '>' if mode == 'w' else '>>'
        return self.cmd(f"echo '{content}' {redirect} '{file_path}'") is not None
    
    def read_file(self, file_path):
        """
        Read the contents of a file.
        
        :param file_path: Path to the file.
        :return: The file contents as a string, or None if the file doesn't exist.
        """
        if not self.exists(file_path):
            self.error(f'File "{file_path}" does not exist')
            return None
        
        return self.cmd(f"cat '{file_path}'", show_output=False)
    
    def replace_in_file(self, file_path, start_pattern, new_string):
        """
        Replace lines in a file that match a pattern.
        
        :param file_path: Path to the file.
        :param start_pattern: Pattern to match at the start of lines.
        :param new_string: String to replace the matched lines with.
        :return: True if successful, False otherwise.
        """
        if not self.exists(file_path) or not os.path.isfile(file_path):
            self.error(f'File "{file_path}" does not exist or is not a file')
            return False
        
        # Escape special characters in the pattern and new string for sed
        escaped_pattern = start_pattern.replace("/", "\\/").replace("'", "'\\''").replace("&", "\\&")
        escaped_new_string = new_string.replace("/", "\\/").replace("'", "'\\''").replace("&", "\\&")
        
        try:
            # Use sed with a different delimiter (|) to avoid issues with slashes in the pattern or replacement
            cmd = f"sed -i 's|^{escaped_pattern}.*|{escaped_new_string}|' '{file_path}'"
            return self.cmd(cmd) is not None
        except Exception as e:
            self.error(f"Failed to replace in file: {e}")
            return False
    
    def chmod(self, path, permissions, recursive=True):
        """
        Change file permissions.
        
        :param path: Path to the file or directory.
        :param permissions: Permissions to set.
        :param recursive: If True, change permissions recursively.
        :return: True if successful, False otherwise.
        """
        if not self.exists(path):
            self.error(f"Path '{path}' does not exist")
            return False
        
        try:
            recursive_flag = "-R" if recursive else ""
            return self.cmd(f"chmod {recursive_flag} {permissions} '{path}'") is not None
        except Exception as e:
            self.error(f"Failed to change permissions: {e}")
            return False
    
    def chown(self, path, user, group=None):
        """
        Change file ownership.
        
        :param path: Path to the file or directory.
        :param user: User to set as owner.
        :param group: Group to set as owner (optional).
        :return: True if successful, False otherwise.
        """
        if not self.exists(path):
            self.error(f"Path '{path}' does not exist")
            return False
        
        owner = user if group is None else f"{user}:{group}"
        try:
            return self.cmd(f"chown {owner} '{path}'") is not None
        except Exception as e:
            self.error(f"Failed to change ownership: {e}")
            return False
    
    def string_in_file(self, file_path, search_string):
        """
        Check if a string exists in a file.
        
        :param file_path: Path to the file.
        :param search_string: String to search for.
        :return: True if the string is found, False otherwise.
        """
        if not self.exists(file_path) or not os.path.isfile(file_path):
            self.error(f"File '{file_path}' does not exist or is not a file")
            return False
        
        # Escape special characters in the search string
        escaped_search = search_string.replace("'", "'\\''")
        
        # Use grep to search for the string
        try:
            # Use -q for quiet mode (no output, just return code)
            # grep returns 0 if the string is found, 1 if not found
            result = subprocess.run(f"grep -q '{escaped_search}' '{file_path}'", shell=True)
            return result.returncode == 0
        except Exception:
            # If the command fails for any reason, return False
            return False

    def copy(self, source, destination, recursive=True):
        """
        Copy a file or directory.
        
        :param source: Source path.
        :param destination: Destination path.
        :param recursive: If True, copy directories recursively.
        :return: True if successful, False otherwise.
        """
        if not self.exists(source):
            self.error(f"Source '{source}' does not exist")
            return False
        
        try:
            if os.path.isfile(source):
                # Copy a file
                result = subprocess.run(f"cp '{source}' '{destination}'", shell=True)
                return result.returncode == 0
            elif os.path.isdir(source):
                if recursive:
                    # Copy a directory recursively
                    result = subprocess.run(f"cp -r '{source}' '{destination}'", shell=True)
                    return result.returncode == 0
                else:
                    # Create the destination directory and copy contents
                    result = subprocess.run(f"mkdir -p '{destination}'", shell=True)
                    return result.returncode == 0
            else:
                self.error(f"Source '{source}' is neither a file nor a directory")
                return False
        except Exception as e:
            self.error(f"Failed to copy: {e}")
            return False

    def mv(self, source, destination):
        """
        Move a file or directory.
        
        :param source: Source path.
        :param destination: Destination path.
        :return: True if successful, False otherwise.
        """
        if not self.exists(source):
            self.error(f"Source '{source}' does not exist")
            return False
        
        try:
            result = subprocess.run(f"mv '{source}' '{destination}'", shell=True)
            return result.returncode == 0
        except Exception as e:
            self.error(f"Failed to move: {e}")
            return False

    def find(self, directory, pattern):
        """
        Find files matching a pattern in a directory.
        
        :param directory: Directory to search in.
        :param pattern: Pattern to match.
        :return: List of matching files, or None if the directory doesn't exist.
        """
        if not self.folder_exists(directory):
            self.error(f"Directory '{directory}' does not exist")
            return None
        
        try:
            result = self.cmd(f"find '{directory}' -name '{pattern}'", show_output=False)
            if result:
                return result.strip().split('\n')
            else:
                return []
        except Exception as e:
            self.error(f"Failed to find files: {e}")
            return None

    def exists(self, path):
        """
        Check if a file or directory exists.
        
        :param path: Path to check.
        :return: True if the path exists, False otherwise.
        """
        result = subprocess.run(f"[ -e '{path}' ]", shell=True)
        return result.returncode == 0
    
    def folder_exists(self, path):
        """
        Check if a directory exists.
        
        :param path: Path to check.
        :return: True if the directory exists, False otherwise.
        """
        result = subprocess.run(f"[ -d '{path}' ]", shell=True)
        return result.returncode == 0 