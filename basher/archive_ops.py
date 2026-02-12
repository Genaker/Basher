"""Archive operations for Basher."""

import os
import subprocess
from .shell_utils import quote


class ArchiveOps:
    """
    Archive operations (tar, zip, gzip, download).
    Uses composition: receives FilesystemContext for exists/folder_exists/mkdir/error.
    """

    def __init__(self, fs):
        """
        Initialize with a filesystem context.
        :param fs: Object with exists(), folder_exists(), mkdir(), error() methods.
        """
        self.fs = fs

    def exists(self, path):
        """Check if a file or directory exists."""
        if self.fs:
            return self.fs.exists(path)
        result = subprocess.run(f"[ -e {quote(path)} ]", shell=True)
        return result.returncode == 0

    def folder_exists(self, path):
        """Check if a directory exists."""
        if self.fs:
            return self.fs.folder_exists(path)
        result = subprocess.run(f"[ -d {quote(path)} ]", shell=True)
        return result.returncode == 0

    def _error(self, message):
        """Display error."""
        if self.fs:
            self.fs.error(message)
        else:
            print(f"{message}")

    def archive(self, source, archive_path, format='tar.gz'):
        """Create an archive."""
        if not self.exists(source):
            self._error(f"Source '{source}' does not exist")
            return False

        archive_dir = os.path.dirname(archive_path)
        if archive_dir and not self.folder_exists(archive_dir):
            if self.fs:
                self.fs.mkdir(archive_dir)
            else:
                try:
                    subprocess.run(f"mkdir -p {quote(archive_dir)}", shell=True, check=True)
                except Exception as e:
                    self._error(f"Failed to create archive directory: {e}")
                    return False

        try:
            if format == 'tar.gz':
                result = subprocess.run(
                    f"tar -czf {quote(archive_path)} -C {quote(os.path.dirname(source))} {quote(os.path.basename(source))}",
                    shell=True
                )
            elif format == 'tar.bz2':
                result = subprocess.run(
                    f"tar -cjf {quote(archive_path)} -C {quote(os.path.dirname(source))} {quote(os.path.basename(source))}",
                    shell=True
                )
            elif format == 'zip':
                recursive = "-r " if os.path.isdir(source) else ""
                result = subprocess.run(
                    f"cd {quote(os.path.dirname(source))} && zip {recursive}{quote(os.path.abspath(archive_path))} {quote(os.path.basename(source))}",
                    shell=True
                )
            else:
                self._error(f"Unsupported archive format '{format}'")
                return False

            return result.returncode == 0
        except Exception as e:
            self._error(f"Failed to create archive: {e}")
            return False

    def extract(self, archive_path, destination=None):
        """Extract an archive."""
        if not self.exists(archive_path):
            self._error(f"Archive '{archive_path}' does not exist")
            return False

        dest_option = f"-C {quote(destination)}" if destination else ""

        if archive_path.endswith('.zip'):
            result = subprocess.run(f"unzip {quote(archive_path)} {dest_option}", shell=True)
        elif archive_path.endswith(('.tar.gz', '.tgz')):
            result = subprocess.run(f"tar -xzf {quote(archive_path)} {dest_option}", shell=True)
        elif archive_path.endswith(('.tar.bz2', '.tbz2')):
            result = subprocess.run(f"tar -xjf {quote(archive_path)} {dest_option}", shell=True)
        else:
            self._error(f"Unsupported archive format for '{archive_path}'")
            return False

        return result.returncode == 0

    def gzip(self, file_path, keep_original=False):
        """Compress a file with gzip."""
        if not self.exists(file_path) or not os.path.isfile(file_path):
            self._error(f"File '{file_path}' does not exist or is not a file")
            return False

        try:
            keep_flag = "-k" if keep_original else ""
            result = subprocess.run(f"gzip {keep_flag} {quote(file_path)}", shell=True)
            return result.returncode == 0
        except Exception as e:
            self._error(f"Failed to compress file: {e}")
            return False

    def gunzip(self, file_path, keep_original=False):
        """Decompress a gzipped file."""
        if not self.exists(file_path) or not os.path.isfile(file_path):
            self._error(f"File '{file_path}' does not exist or is not a file")
            return False

        if not file_path.endswith('.gz'):
            self._error(f"File '{file_path}' is not a gzipped file")
            return False

        try:
            keep_flag = "-k" if keep_original else ""
            result = subprocess.run(f"gunzip {keep_flag} {quote(file_path)}", shell=True)
            return result.returncode == 0
        except Exception as e:
            self._error(f"Failed to decompress file: {e}")
            return False

    def download(self, url, destination=None):
        """Download a file from a URL."""
        try:
            if destination:
                result = subprocess.run(f"curl -L {quote(url)} -o {quote(destination)}", shell=True)
            else:
                result = subprocess.run(f"curl -L {quote(url)}", shell=True)
            return result.returncode == 0
        except Exception as e:
            self._error(f"Failed to download file: {e}")
            return False
