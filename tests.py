#!/usr/bin/env python3
"""
Test suite for Basher package.

This script tests all the main functionality of the Basher package.
Run with: python -m unittest tests.py
"""

import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Import the Basher class from the renamed module
from basher import Basher
from basher.core import BashCommand


class TestBasher(unittest.TestCase):
    """Test cases for Basher package."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.old_dir = os.getcwd()
        os.chdir(self.test_dir)
        # Create a Basher instance for testing
        self.bash = Basher()

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.old_dir)
        shutil.rmtree(self.test_dir)

    # Core tests
    @patch('basher.core.subprocess.run')
    def test_cmd(self, mock_run):
        """Test the cmd function."""
        mock_result = MagicMock()
        mock_result.stdout = "Command output"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Test with default parameters (capture_output=True to get output)
        result = self.bash.cmd("ls -la", capture_output=True)
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]
        self.assertTrue(call_kwargs.get('shell'))
        self.assertTrue(call_kwargs.get('capture_output') or 'stdout' in call_kwargs)
        self.assertEqual(result, "Command output")

        # Test with show_output=False
        mock_run.reset_mock()
        mock_run.return_value = mock_result
        result = self.bash.cmd("ls -la", show_output=False, capture_output=True)
        self.assertEqual(result, "Command output")

        # Test with capture_output=False
        mock_run.reset_mock()
        mock_run.return_value = mock_result
        result = self.bash.cmd("ls -la", capture_output=False)
        self.assertEqual(result, 0)

        # Test with cwd parameter
        with patch('basher.core.os.getcwd', return_value="/original/dir"):
            with patch('basher.core.os.chdir') as mock_chdir:
                mock_run.return_value = mock_result
                self.bash.cmd("ls -la", cwd="/test/dir")
                mock_chdir.assert_any_call("/test/dir")
                mock_chdir.assert_any_call("/original/dir")

    @patch('basher.core.BashCommand.cmd')
    @patch('basher.core.subprocess.run')
    def test_execute_in_directory(self, mock_subprocess_run, mock_cmd):
        """Test the execute_in_directory function."""
        # Mock subprocess.run to simulate directory exists
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess_run.return_value = mock_result
        
        mock_cmd.return_value = "Command output"

        # Test with existing directory
        result = self.bash.execute_in_directory("ls -la", "/test/dir")
        mock_cmd.assert_called_with("cd /test/dir && ls -la", show_output=True)
        self.assertEqual(result, "Command output")

        # Test with non-existent directory
        mock_result.returncode = 1
        result = self.bash.execute_in_directory("ls -la", "/nonexistent/dir")
        self.assertIsNone(result)

    # File operations tests
    def test_write_to_file(self):
        """Test the write_to_file function (uses Python I/O for safety)."""
        file_path = os.path.join(self.test_dir, "test.txt")
        # Test write mode
        result = self.bash.write_to_file(file_path, "Test content")
        self.assertTrue(result)
        with open(file_path) as f:
            self.assertEqual(f.read(), "Test content")

        # Test append mode
        result = self.bash.write_to_file(file_path, "More content", 'a')
        self.assertTrue(result)
        with open(file_path) as f:
            self.assertEqual(f.read(), "Test contentMore content")

        # Test with invalid mode
        with self.assertRaises(ValueError):
            self.bash.write_to_file(file_path, "Content", 'x')

    @patch('basher.file_ops.FileOps.exists')
    def test_read_file(self, mock_exists):
        """Test the read_file function (uses Python I/O, equivalent to cat)."""
        # Test with existing file - use real file in temp dir
        file_path = os.path.join(self.test_dir, "read_test.txt")
        with open(file_path, "w") as f:
            f.write("File content")

        mock_exists.return_value = True
        result = self.bash.read_file(file_path)
        self.assertEqual(result, "File content")

        # Test with non-existent file
        mock_exists.return_value = False
        result = self.bash.read_file("/nonexistent/file.txt")
        self.assertIsNone(result)

    @patch('basher.file_ops.FileOps.cmd')
    @patch('basher.file_ops.FileOps.exists')
    @patch('basher.file_ops.os.path.isfile')
    def test_replace_in_file(self, mock_isfile, mock_exists, mock_cmd):
        """Test the replace_in_file function."""
        # Mock file existence checks
        mock_exists.return_value = True
        mock_isfile.return_value = True
        
        # Test replacing content (implementation uses | delimiter for sed)
        self.bash.replace_in_file("/test/file.txt", "pattern", "new string")
        
        # Check that the correct sed command was called
        mock_cmd.assert_any_call("sed -i 's|^pattern.*|new string|' /test/file.txt")
        
        # Test with non-existent file
        mock_exists.return_value = False
        self.bash.replace_in_file("/nonexistent/file.txt", "pattern", "new string")
        
        # Check that an error message about the non-existent file was displayed
        for call in mock_cmd.call_args_list:
            if "echo" in call[0][0] and "File \"/nonexistent/file.txt\" does not exist" in call[0][0]:
                break
        else:
            self.fail("Error message about non-existent file was not displayed")

    @patch('basher.file_ops.subprocess.run')
    @patch('basher.file_ops.FileOps.exists')
    @patch('basher.file_ops.os.path.isfile')
    @patch('basher.file_ops.os.path.isdir')
    def test_copy(self, mock_isdir, mock_isfile, mock_exists, mock_run):
        """Test the copy function."""
        mock_exists.return_value = True
        mock_run.return_value.returncode = 0
        
        # Test copying a file
        mock_isfile.return_value = True
        mock_isdir.return_value = False
        result = self.bash.copy("/source/file.txt", "/dest/file.txt")
        mock_run.assert_called_with("cp /source/file.txt /dest/file.txt", shell=True)
        self.assertTrue(result)
        
        # Test copying a directory recursively
        mock_isfile.return_value = False
        mock_isdir.return_value = True
        result = self.bash.copy("/source/dir", "/dest/dir", recursive=True)
        mock_run.assert_called_with("cp -r /source/dir /dest/dir", shell=True)
        self.assertTrue(result)
        
        # Test copying a directory non-recursively
        result = self.bash.copy("/source/dir", "/dest/dir", recursive=False)
        mock_run.assert_called_with("mkdir -p /dest/dir", shell=True)
        self.assertTrue(result)
        
        # Test with non-existent source
        mock_exists.return_value = False
        result = self.bash.copy("/nonexistent/source", "/dest")
        self.assertFalse(result)

    @patch('basher.file_ops.subprocess.run')
    @patch('basher.file_ops.FileOps.exists')
    def test_mv(self, mock_exists, mock_run):
        """Test the mv function."""
        mock_exists.return_value = True
        mock_run.return_value.returncode = 0
        
        # Test moving a file
        result = self.bash.mv("/source/file.txt", "/dest/file.txt")
        mock_run.assert_called_with("mv /source/file.txt /dest/file.txt", shell=True)
        self.assertTrue(result)
        
        # Test with non-existent source
        mock_exists.return_value = False
        result = self.bash.mv("/nonexistent/source", "/dest")
        self.assertFalse(result)

    @patch('basher.file_ops.FileOps.cmd')
    @patch('basher.file_ops.FileOps.folder_exists')
    def test_find(self, mock_folder_exists, mock_cmd):
        """Test the find function."""
        mock_folder_exists.return_value = True
        mock_cmd.return_value = "/test/dir/file1.txt\n/test/dir/file2.txt"
        
        # Test finding files
        result = self.bash.find("/test/dir", "*.txt")
        mock_cmd.assert_called_with("find /test/dir -name '*.txt'", show_output=False)
        self.assertEqual(result, ["/test/dir/file1.txt", "/test/dir/file2.txt"])
        
        # Test with no matches
        mock_cmd.return_value = ""
        result = self.bash.find("/test/dir", "*.jpg")
        self.assertEqual(result, [])
        
        # Test with non-existent directory
        mock_folder_exists.return_value = False
        result = self.bash.find("/nonexistent/dir", "*.txt")
        self.assertIsNone(result)

    @patch('basher.file_ops.FileOps.cmd')
    @patch('basher.file_ops.FileOps.exists')
    def test_chmod(self, mock_exists, mock_cmd):
        """Test the chmod function."""
        mock_exists.return_value = True
        
        # Test changing permissions
        self.bash.chmod("/test/file.txt", "755")
        mock_cmd.assert_called_with("chmod -R 755 /test/file.txt")
        
        # Reset the mock before testing with non-existent file
        mock_cmd.reset_mock()
        
        # Test with non-existent file
        mock_exists.return_value = False
        self.bash.chmod("/nonexistent/file.txt", "755")
        
        # Check that no chmod command was called
        # We can't use assert_not_called() because cmd is called for the error message
        for call in mock_cmd.call_args_list:
            self.assertNotIn("chmod", call[0][0])

    @patch('basher.file_ops.FileOps.cmd')
    @patch('basher.file_ops.FileOps.exists')
    def test_chown(self, mock_exists, mock_cmd):
        """Test the chown function."""
        mock_exists.return_value = True
        mock_cmd.return_value = True
        
        # Test changing ownership
        result = self.bash.chown("/test/file.txt", "user")
        mock_cmd.assert_called_with("chown user /test/file.txt")
        self.assertTrue(result)
        
        # Test changing ownership with group
        result = self.bash.chown("/test/file.txt", "user", "group")
        mock_cmd.assert_called_with("chown user:group /test/file.txt")
        self.assertTrue(result)
        
        # Test with non-existent file
        mock_exists.return_value = False
        result = self.bash.chown("/nonexistent/file.txt", "user")
        self.assertFalse(result)

    # System operations tests
    @patch('basher.system_ops.SystemOps.cmd')
    def test_detect_package_manager(self, mock_cmd):
        """Test the detect_package_manager function."""
        # Reset the cached package manager before each test
        self.bash.system.package_manager = None
        
        # Test with apt (cmd returns 0 on success)
        mock_cmd.return_value = 0
        result = self.bash.detect_package_manager()
        self.assertEqual(result, "apt")
        
        # Reset the cached package manager for the next test
        self.bash.system.package_manager = None
        
        # Test with yum
        def side_effect(cmd, **kwargs):
            if cmd == "which apt":
                return 1  # which apt returns failure
            elif cmd == "which yum":
                return 0   # which yum returns success
            return 1
        
        mock_cmd.side_effect = side_effect
        result = self.bash.detect_package_manager()
        self.assertEqual(result, "yum")
        
        # Reset the cached package manager for the next test
        self.bash.system.package_manager = None
        
        # Test with no package manager
        mock_cmd.side_effect = lambda cmd, **kwargs: 1  # All commands fail (non-zero return)
        result = self.bash.detect_package_manager()
        self.assertIsNone(result)

    @patch('basher.system_ops.SystemOps.cmd')
    @patch('basher.system_ops.SystemOps.detect_package_manager')
    def test_install(self, mock_detect, mock_cmd):
        """Test the install function."""
        mock_cmd.return_value = "Installation successful"
        
        # Test installing with apt
        mock_detect.return_value = "apt"
        
        # Test with a list of packages
        result = self.bash.install(["package1", "package2"])
        mock_cmd.assert_called_with("sudo apt update && sudo apt install -y package1 package2")
        self.assertTrue(result)
        
        # Test with a single package as a string
        result = self.bash.install("single-package")
        mock_cmd.assert_called_with("sudo apt update && sudo apt install -y single-package")
        self.assertTrue(result)
        
        # Test with other package managers...

    @patch('basher.system_ops.os.path.isdir')
    @patch('basher.system_ops.os.chdir')
    def test_cd(self, mock_chdir, mock_isdir):
        """Test the cd function."""
        mock_isdir.return_value = True
        
        # Test changing directory
        result = self.bash.cd("/new/dir")
        mock_chdir.assert_called_with("/new/dir")
        self.assertTrue(result)
        
        # Test with non-existent directory - chdir raises only for bad path
        def chdir_side_effect(path):
            if path == "/nonexistent/dir":
                raise FileNotFoundError()
        mock_chdir.side_effect = chdir_side_effect
        result = self.bash.cd("/nonexistent/dir")
        self.assertFalse(result)

    @patch('basher.system_ops.subprocess.run')
    @patch('basher.system_ops.os.path.exists')
    def test_mkdir(self, mock_exists, mock_run):
        """Test the mkdir function."""
        mock_run.return_value.returncode = 0
        
        # Test creating a directory
        mock_exists.return_value = False
        result = self.bash.mkdir("/test/dir")
        mock_run.assert_called_with("mkdir -p /test/dir", shell=True)
        self.assertTrue(result)
        
        # Test with exist_ok=True (default) when directory exists
        mock_exists.return_value = True
        result = self.bash.mkdir("/test/dir")
        self.assertTrue(result)
        
        # Test with exist_ok=False when directory exists
        result = self.bash.mkdir("/test/dir", exist_ok=False)
        self.assertFalse(result)

    @patch('basher.system_ops.subprocess.run')
    @patch('basher.system_ops.SystemOps.exists')
    @patch('basher.system_ops.os.path.isfile')
    @patch('basher.system_ops.os.path.isdir')
    @patch('basher.system_ops.os.path.islink')
    def test_rm(self, mock_islink, mock_isdir, mock_isfile, mock_exists, mock_run):
        """Test the rm function."""
        mock_exists.return_value = True
        mock_run.return_value.returncode = 0
        
        # Test removing a file (implementation uses path without quotes)
        mock_isfile.return_value = True
        mock_isdir.return_value = False
        mock_islink.return_value = False
        result = self.bash.rm("/test/file.txt")
        mock_run.assert_called_with("rm /test/file.txt", shell=True)
        self.assertTrue(result)
        
        # Test removing a symlink (implementation uses path without quotes)
        mock_isfile.return_value = False
        mock_isdir.return_value = False
        mock_islink.return_value = True
        result = self.bash.rm("/test/link")
        mock_run.assert_called_with("rm /test/link", shell=True)
        self.assertTrue(result)
        
        # Test removing a directory recursively
        mock_isfile.return_value = False
        mock_isdir.return_value = True
        mock_islink.return_value = False
        result = self.bash.rm("/test/dir", recursive=True)
        mock_run.assert_called_with("rm -rf /test/dir", shell=True)
        self.assertTrue(result)
        
        # Test removing an empty directory non-recursively
        mock_run.return_value.returncode = 0
        result = self.bash.rm("/test/dir", recursive=False)
        mock_run.assert_called_with("rmdir /test/dir 2>/dev/null", shell=True)
        self.assertTrue(result)
        
        # Test with non-existent path
        mock_exists.return_value = False
        result = self.bash.rm("/nonexistent/path")
        self.assertFalse(result)
        
        # Test removing a non-empty directory non-recursively
        mock_exists.return_value = True
        mock_isfile.return_value = False
        mock_isdir.return_value = True
        mock_islink.return_value = False
        mock_run.return_value.returncode = 1
        result = self.bash.rm("/test/dir", recursive=False)
        self.assertFalse(result)

    # Archive operations tests
    @patch('basher.archive_ops.subprocess.run')
    @patch('basher.archive_ops.ArchiveOps.exists')
    @patch('basher.archive_ops.ArchiveOps.folder_exists')
    @patch('basher.archive_ops.os.path.isdir')
    def test_archive(self, mock_isdir, mock_folder_exists, mock_exists, mock_run):
        """Test the archive function."""
        mock_exists.return_value = True
        mock_run.return_value.returncode = 0
        
        # Create a mock for the system attribute
        mock_system = MagicMock()
        self.bash.archive_ops.fs = mock_system
        
        # Test creating a tar.gz archive
        mock_folder_exists.return_value = True
        result = self.bash.archive("/source/dir", "/archive/dir/archive.tar.gz", format="tar.gz")
        # Don't check the exact command, just verify it was called and returned success
        self.assertTrue(result)
        self.assertTrue(mock_run.called)
        
        # Test creating a tar.bz2 archive
        result = self.bash.archive("/source/dir", "/archive/dir/archive.tar.bz2", format="tar.bz2")
        self.assertTrue(result)
        
        # Test creating a zip archive from a directory
        mock_isdir.return_value = True
        result = self.bash.archive("/source/dir", "/archive/dir/archive.zip", format="zip")
        self.assertTrue(result)
        
        # Test creating a zip archive from a file
        mock_isdir.return_value = False
        result = self.bash.archive("/source/file.txt", "/archive/dir/archive.zip", format="zip")
        self.assertTrue(result)
        
        # Test with non-existent source
        mock_exists.return_value = False
        result = self.bash.archive("/nonexistent/source", "/archive/dir/archive.tar.gz")
        self.assertFalse(result)
        
        # Test with unsupported format
        mock_exists.return_value = True
        result = self.bash.archive("/source/dir", "/archive/dir/archive.xyz", format="xyz")
        self.assertFalse(result)
        
        # Test with archive directory that doesn't exist
        mock_folder_exists.return_value = False
        result = self.bash.archive("/source/dir", "/archive/dir/archive.tar.gz")
        mock_system.mkdir.assert_called_with("/archive/dir")

    @patch('basher.archive_ops.subprocess.run')
    @patch('basher.archive_ops.ArchiveOps.exists')
    def test_extract(self, mock_exists, mock_run):
        """Test the extract function."""
        mock_exists.return_value = True
        mock_run.return_value.returncode = 0
        
        # Test extracting a zip file
        result = self.bash.extract("/archive/dir/archive.zip")
        mock_run.assert_called_with("unzip /archive/dir/archive.zip ", shell=True)
        self.assertTrue(result)
        
        # Test extracting a tar.gz file with destination
        result = self.bash.extract("/archive/dir/archive.tar.gz", "/extract/dir")
        mock_run.assert_called_with("tar -xzf /archive/dir/archive.tar.gz -C /extract/dir", shell=True)
        self.assertTrue(result)
        
        # Test extracting a tar.bz2 file
        result = self.bash.extract("/archive/dir/archive.tar.bz2")
        mock_run.assert_called_with("tar -xjf /archive/dir/archive.tar.bz2 ", shell=True)
        self.assertTrue(result)
        
        # Test with unsupported format
        result = self.bash.extract("/archive/dir/archive.xyz")
        self.assertFalse(result)
        
        # Test with non-existent archive
        mock_exists.return_value = False
        result = self.bash.extract("/nonexistent/archive.tar.gz")
        self.assertFalse(result)

    @patch('basher.archive_ops.subprocess.run')
    @patch('basher.archive_ops.ArchiveOps.exists')
    @patch('basher.archive_ops.os.path.isfile')
    def test_gzip(self, mock_isfile, mock_exists, mock_run):
        """Test the gzip function."""
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_run.return_value.returncode = 0
        
        # Test compressing a file with keep_original=False
        result = self.bash.gzip("/test/file.txt", keep_original=False)
        mock_run.assert_called_with("gzip  /test/file.txt", shell=True)
        self.assertTrue(result)
        
        # Test compressing a file with keep_original=True
        result = self.bash.gzip("/test/file.txt", keep_original=True)
        mock_run.assert_called_with("gzip -k /test/file.txt", shell=True)
        self.assertTrue(result)
        
        # Test with non-existent file
        mock_exists.return_value = False
        result = self.bash.gzip("/nonexistent/file.txt")
        self.assertFalse(result)
        
        # Test with a directory instead of a file
        mock_exists.return_value = True
        mock_isfile.return_value = False
        result = self.bash.gzip("/test/dir")
        self.assertFalse(result)

    @patch('basher.archive_ops.subprocess.run')
    @patch('basher.archive_ops.ArchiveOps.exists')
    @patch('basher.archive_ops.os.path.isfile')
    def test_gunzip(self, mock_isfile, mock_exists, mock_run):
        """Test the gunzip function."""
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_run.return_value.returncode = 0
        
        # Test decompressing a file with keep_original=False
        result = self.bash.gunzip("/test/file.txt.gz", keep_original=False)
        mock_run.assert_called_with("gunzip  /test/file.txt.gz", shell=True)
        self.assertTrue(result)
        
        # Test decompressing a file with keep_original=True
        result = self.bash.gunzip("/test/file.txt.gz", keep_original=True)
        mock_run.assert_called_with("gunzip -k /test/file.txt.gz", shell=True)
        self.assertTrue(result)
        
        # Test with non-existent file
        mock_exists.return_value = False
        result = self.bash.gunzip("/nonexistent/file.txt.gz")
        self.assertFalse(result)
        
        # Test with a directory instead of a file
        mock_exists.return_value = True
        mock_isfile.return_value = False
        result = self.bash.gunzip("/test/dir.gz")
        self.assertFalse(result)
        
        # Test with a file that doesn't have .gz extension
        mock_isfile.return_value = True
        result = self.bash.gunzip("/test/file.txt")
        self.assertFalse(result)

    @patch('basher.archive_ops.subprocess.run')
    def test_download(self, mock_run):
        """Test the download function."""
        mock_run.return_value.returncode = 0
        
        # Test downloading without specifying destination
        result = self.bash.download("https://example.com/file.txt")
        mock_run.assert_called_with("curl -L https://example.com/file.txt", shell=True)
        self.assertTrue(result)
        
        # Test downloading with destination
        result = self.bash.download("https://example.com/file.txt", "/download/dir/file.txt")
        mock_run.assert_called_with("curl -L https://example.com/file.txt -o /download/dir/file.txt", shell=True)
        self.assertTrue(result)

    @patch('basher.file_ops.subprocess.run')
    @patch('basher.file_ops.FileOps.exists')
    @patch('basher.file_ops.os.path.isfile')
    def test_string_in_file(self, mock_isfile, mock_exists, mock_run):
        """Test the string_in_file function."""
        mock_exists.return_value = True
        mock_isfile.return_value = True
        
        # Test when string is found
        mock_run.return_value.returncode = 0
        result = self.bash.string_in_file("/test/file.txt", "search string")
        self.assertTrue(result)
        
        # Test when string is not found
        mock_run.return_value.returncode = 1
        result = self.bash.string_in_file("/test/file.txt", "missing string")
        self.assertFalse(result)
        
        # Test with non-existent file
        mock_exists.return_value = False
        result = self.bash.string_in_file("/nonexistent/file.txt", "search string")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main() 