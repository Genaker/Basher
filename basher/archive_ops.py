"""Archive operations for Basher."""

import os
import subprocess
from .core import BashCommand

class ArchiveOps(BashCommand):
    """
    A class that provides archive operation methods.
    """
    
    def __init__(self, system):
        """Initialize the ArchiveOps object."""
        super().__init__()
        self.system = system
    
    def exists(self, path):
        """
        Check if a file or directory exists.
        
        :param path: Path to check.
        :return: True if the path exists, False otherwise.
        """
        if self.system:
            return self.system.exists(path)
        else:
            result = subprocess.run(f"[ -e '{path}' ]", shell=True)
            return result.returncode == 0
    
    def folder_exists(self, path):
        """
        Check if a directory exists.
        
        :param path: Path to check.
        :return: True if the directory exists, False otherwise.
        """
        if self.system:
            return self.system.folder_exists(path)
        else:
            result = subprocess.run(f"[ -d '{path}' ]", shell=True)
            return result.returncode == 0
    
    def archive(self, source, archive_path, format='tar.gz'):
        """
        Create an archive.
        
        :param source: Path to the source file or directory.
        :param archive_path: Path to the archive file to create.
        :param format: Archive format ('tar.gz', 'tar.bz2', 'zip').
        :return: True if successful, False otherwise.
        """
        if not self.exists(source):
            self.error(f"Source '{source}' does not exist")
            return False
        
        # Create the directory for the archive if it doesn't exist
        archive_dir = os.path.dirname(archive_path)
        if archive_dir and not self.folder_exists(archive_dir):
            # Use subprocess directly if system is None
            if self.system is None:
                try:
                    subprocess.run(f"mkdir -p '{archive_dir}'", shell=True, check=True)
                except Exception as e:
                    self.error(f"Failed to create archive directory: {e}")
                    return False
            else:
                self.system.mkdir(archive_dir)
        
        try:
            if format == 'tar.gz':
                if os.path.isdir(source):
                    result = subprocess.run(f"tar -czf '{archive_path}' -C '{os.path.dirname(source)}' '{os.path.basename(source)}'", shell=True)
                else:
                    result = subprocess.run(f"tar -czf '{archive_path}' -C '{os.path.dirname(source)}' '{os.path.basename(source)}'", shell=True)
            elif format == 'tar.bz2':
                if os.path.isdir(source):
                    result = subprocess.run(f"tar -cjf '{archive_path}' -C '{os.path.dirname(source)}' '{os.path.basename(source)}'", shell=True)
                else:
                    result = subprocess.run(f"tar -cjf '{archive_path}' -C '{os.path.dirname(source)}' '{os.path.basename(source)}'", shell=True)
            elif format == 'zip':
                if os.path.isdir(source):
                    result = subprocess.run(f"cd '{os.path.dirname(source)}' && zip -r '{os.path.abspath(archive_path)}' '{os.path.basename(source)}'", shell=True)
                else:
                    result = subprocess.run(f"cd '{os.path.dirname(source)}' && zip '{os.path.abspath(archive_path)}' '{os.path.basename(source)}'", shell=True)
            else:
                self.error(f"Unsupported archive format '{format}'")
                return False
            
            return result.returncode == 0
        except Exception as e:
            self.error(f"Failed to create archive: {e}")
            return False
    
    def extract(self, archive_path, destination=None):
        """
        Extract an archive file.
        
        :param archive_path: Path to the archive file.
        :param destination: Directory to extract to (optional).
        :return: True if successful, False otherwise.
        """
        if not self.exists(archive_path):
            self.error(f"Archive '{archive_path}' does not exist")
            return False
        
        dest_option = f"-C '{destination}'" if destination else ""
        
        if archive_path.endswith('.zip'):
            result = subprocess.run(f"unzip '{archive_path}' {dest_option}", shell=True)
        elif archive_path.endswith(('.tar.gz', '.tgz')):
            result = subprocess.run(f"tar -xzf '{archive_path}' {dest_option}", shell=True)
        elif archive_path.endswith(('.tar.bz2', '.tbz2')):
            result = subprocess.run(f"tar -xjf '{archive_path}' {dest_option}", shell=True)
        else:
            self.error(f"Unsupported archive format for '{archive_path}'")
            return False
        
        return result.returncode == 0
    
    def gzip(self, file_path, keep_original=False):
        """
        Compress a file using gzip.
        
        :param file_path: Path to the file to compress.
        :param keep_original: If True, keep the original file after compression.
        :return: True if successful, False otherwise.
        """
        if not self.exists(file_path) or not os.path.isfile(file_path):
            self.error(f"File '{file_path}' does not exist or is not a file")
            return False
        
        try:
            # Use the -k flag to keep the original file if requested
            keep_flag = "-k" if keep_original else ""
            result = subprocess.run(f"gzip {keep_flag} '{file_path}'", shell=True)
            return result.returncode == 0
        except Exception as e:
            self.error(f"Failed to compress file: {e}")
            return False
    
    def gunzip(self, file_path, keep_original=False):
        """
        Decompress a gzipped file.
        
        :param file_path: Path to the gzipped file.
        :param keep_original: If True, keep the original file after decompression.
        :return: True if successful, False otherwise.
        """
        if not self.exists(file_path) or not os.path.isfile(file_path):
            self.error(f"File '{file_path}' does not exist or is not a file")
            return False
        
        if not file_path.endswith('.gz'):
            self.error(f"File '{file_path}' is not a gzipped file")
            return False
        
        try:
            # Use the -k flag to keep the original file if requested
            keep_flag = "-k" if keep_original else ""
            result = subprocess.run(f"gunzip {keep_flag} '{file_path}'", shell=True)
            return result.returncode == 0
        except Exception as e:
            self.error(f"Failed to decompress file: {e}")
            return False
    
    def download(self, url, destination=None):
        """
        Download a file from a URL.
        
        :param url: URL to download from.
        :param destination: Path to save the file to (optional).
        :return: True if successful, False otherwise.
        """
        try:
            if destination:
                result = subprocess.run(f"curl -L '{url}' -o '{destination}'", shell=True)
            else:
                result = subprocess.run(f"curl -L '{url}'", shell=True)
            return result.returncode == 0
        except Exception as e:
            self.error(f"Failed to download file: {e}")
            return False 