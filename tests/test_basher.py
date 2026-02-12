"""Comprehensive tests for Basher package."""

import os
from unittest.mock import patch, MagicMock

import pytest

from basher import Basher
from basher.shell_utils import quote


class TestCmd:
    """Tests for cmd()."""

    @patch("basher.core.subprocess.run")
    def test_cmd_capture_output(self, mock_run, bash):
        mock_run.return_value = MagicMock(stdout="output", stderr="", returncode=0)
        result = bash.cmd("ls", capture_output=True)
        assert result == "output"
        mock_run.assert_called_once()

    @patch("basher.core.subprocess.run")
    def test_cmd_return_code(self, mock_run, bash):
        mock_run.return_value = MagicMock(returncode=0)
        result = bash.cmd("ls", capture_output=False)
        assert result == 0

    @patch("basher.core.subprocess.run")
    def test_cmd_emulate_skips_execution(self, mock_run, bash):
        bash.set_emulate(True)
        result = bash.cmd("dangerous command")
        mock_run.assert_not_called()
        assert result == 0
        bash.set_emulate(False)

    @patch("basher.core.subprocess.run")
    def test_cmd_with_cwd(self, mock_run, bash):
        mock_run.return_value = MagicMock(returncode=0)
        with patch("basher.core.os.getcwd", return_value="/old"):
            with patch("basher.core.os.chdir") as mock_chdir:
                bash.cmd("ls", cwd="/new")
                mock_chdir.assert_any_call("/new")
                mock_chdir.assert_any_call("/old")

    @patch("basher.core.subprocess.run")
    def test_cmd_failure_capture_output_returns_exception_string(self, mock_run, bash):
        mock_run.side_effect = Exception("Failed")
        result = bash.cmd("bad", capture_output=True)
        assert "Exception" in result and "Failed" in result

    @patch("basher.core.subprocess.run")
    def test_cmd_passes_command_as_given(self, mock_run, bash):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        bash.cmd("ls /tmp", capture_output=True)
        assert "ls" in mock_run.call_args[0][0]


class TestExecuteInDirectory:
    """Tests for execute_in_directory()."""

    @patch("basher.core.BashCommand.cmd")
    @patch("basher.core.subprocess.run")
    def test_execute_in_existing_dir(self, mock_sub_run, mock_cmd, bash):
        mock_sub_run.return_value.returncode = 0
        mock_cmd.return_value = "result"
        result = bash.execute_in_directory("ls", "/test/dir")
        assert result == "result"
        mock_cmd.assert_called_with("cd /test/dir && ls", show_output=True)

    @patch("basher.core.subprocess.run")
    def test_execute_in_nonexistent_dir_returns_none(self, mock_sub_run, bash):
        mock_sub_run.return_value.returncode = 1
        result = bash.execute_in_directory("ls", "/nonexistent")
        assert result is None

    @patch("basher.core.BashCommand.cmd")
    @patch("basher.core.subprocess.run")
    def test_execute_in_directory_path_with_spaces_quoted(self, mock_sub_run, mock_cmd, bash):
        mock_sub_run.return_value.returncode = 0
        mock_cmd.return_value = "ok"
        bash.execute_in_directory("ls", "/path with spaces")
        assert quote("/path with spaces") in mock_cmd.call_args[0][0]


class TestWriteToFile:
    """Tests for write_to_file()."""

    def test_write_mode(self, bash, temp_dir):
        path = os.path.join(temp_dir, "out.txt")
        result = bash.write_to_file(path, "content")
        assert result is True
        assert open(path).read() == "content"

    def test_append_mode(self, bash, temp_dir):
        path = os.path.join(temp_dir, "out.txt")
        bash.write_to_file(path, "first")
        result = bash.write_to_file(path, "second", "a")
        assert result is True
        assert open(path).read() == "firstsecond"

    def test_invalid_mode_raises(self, bash, temp_dir):
        with pytest.raises(ValueError):
            bash.write_to_file(os.path.join(temp_dir, "x"), "c", "x")

    def test_content_with_newlines(self, bash, temp_dir):
        path = os.path.join(temp_dir, "multiline.txt")
        content = "line1\nline2\n"
        bash.write_to_file(path, content)
        assert open(path).read() == content

    def test_write_empty_content(self, bash, temp_dir):
        path = os.path.join(temp_dir, "empty.txt")
        assert bash.write_to_file(path, "") is True
        assert open(path).read() == ""

    def test_write_unicode_content(self, bash, temp_dir):
        path = os.path.join(temp_dir, "unicode.txt")
        content = "café 日本語 ñ"
        assert bash.write_to_file(path, content) is True
        assert open(path, encoding="utf-8").read() == content

    def test_write_path_with_spaces(self, bash, temp_dir):
        path = os.path.join(temp_dir, "file with spaces.txt")
        assert bash.write_to_file(path, "x") is True
        assert open(path).read() == "x"


class TestReadFile:
    """Tests for read_file()."""

    @patch("basher.file_ops.FileOps.exists")
    def test_read_existing_file(self, mock_exists, bash, sample_file):
        mock_exists.return_value = True
        result = bash.read_file(sample_file)
        assert result == "line1\nline2 pattern here\nline3\n"

    @patch("basher.file_ops.FileOps.exists")
    def test_read_nonexistent_returns_none(self, mock_exists, bash):
        mock_exists.return_value = False
        assert bash.read_file("/nonexistent") is None

    def test_read_empty_file(self, bash, temp_dir):
        path = os.path.join(temp_dir, "empty.txt")
        bash.write_to_file(path, "")
        assert bash.read_file(path) == ""

    @patch("basher.file_ops.FileOps.exists")
    def test_read_io_error_returns_none(self, mock_exists, bash):
        mock_exists.return_value = True
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            assert bash.read_file("/restricted") is None


class TestReplaceInFile:
    """Tests for replace_in_file()."""

    @patch("basher.file_ops.FileOps.cmd")
    @patch("basher.file_ops.FileOps.exists")
    @patch("basher.file_ops.os.path.isfile")
    def test_replace_calls_sed(self, mock_isfile, mock_exists, mock_cmd, bash):
        mock_exists.return_value = mock_isfile.return_value = True
        bash.replace_in_file("/f", "pat", "new")
        assert any("sed" in str(c) for c in mock_cmd.call_args_list)

    @patch("basher.file_ops.FileOps.exists")
    def test_replace_nonexistent_returns_false(self, mock_exists, bash):
        mock_exists.return_value = False
        assert bash.replace_in_file("/nonexistent", "pat", "new") is False

    @patch("basher.file_ops.FileOps.cmd")
    @patch("basher.file_ops.FileOps.exists")
    @patch("basher.file_ops.os.path.isfile")
    def test_replace_isfile_false_returns_false(self, mock_isfile, mock_exists, mock_cmd, bash):
        mock_exists.return_value = True
        mock_isfile.return_value = False
        assert bash.replace_in_file("/dir", "pat", "new") is False
        assert not any("sed" in str(c) for c in mock_cmd.call_args_list)

    def test_replace_with_special_chars_in_pattern(self, bash, temp_dir):
        path = os.path.join(temp_dir, "sed_test.txt")
        bash.write_to_file(path, "foo/bar\nline2\n")
        assert bash.replace_in_file(path, "foo/bar", "replaced") is True
        assert "replaced" in bash.read_file(path)


class TestStringInFile:
    """Tests for string_in_file()."""

    @patch("basher.file_ops.subprocess.run")
    @patch("basher.file_ops.FileOps.exists")
    @patch("basher.file_ops.os.path.isfile")
    def test_string_found(self, mock_isfile, mock_exists, mock_run, bash):
        mock_exists.return_value = mock_isfile.return_value = True
        mock_run.return_value.returncode = 0
        assert bash.string_in_file("/f", "x") is True

    @patch("basher.file_ops.subprocess.run")
    @patch("basher.file_ops.FileOps.exists")
    @patch("basher.file_ops.os.path.isfile")
    def test_string_not_found(self, mock_isfile, mock_exists, mock_run, bash):
        mock_exists.return_value = mock_isfile.return_value = True
        mock_run.return_value.returncode = 1
        assert bash.string_in_file("/f", "x") is False

    @patch("basher.file_ops.FileOps.exists")
    @patch("basher.file_ops.os.path.isfile")
    def test_string_in_file_isfile_false_returns_false(self, mock_isfile, mock_exists, bash):
        mock_exists.return_value = True
        mock_isfile.return_value = False
        assert bash.string_in_file("/dir", "x") is False

    @patch("basher.file_ops.subprocess.run")
    @patch("basher.file_ops.FileOps.exists")
    @patch("basher.file_ops.os.path.isfile")
    def test_string_in_file_search_with_special_chars_quoted(self, mock_isfile, mock_exists, mock_run, bash):
        mock_exists.return_value = mock_isfile.return_value = True
        mock_run.return_value.returncode = 0
        result = bash.string_in_file("/f", "x'y")
        assert result is True
        cmd = mock_run.call_args[0][0]
        assert "grep" in cmd and "/f" in cmd


class TestStringExistsInFile:
    """Tests for string_exists_in_file()."""

    def test_string_exists_returns_true(self, bash, sample_file):
        result = bash.string_exists_in_file(sample_file, "pattern")
        assert result is True

    def test_string_not_exists_returns_false(self, bash, sample_file):
        result = bash.string_exists_in_file(sample_file, "nonexistent")
        assert result is False

    def test_case_insensitive(self, bash, sample_file):
        result = bash.string_exists_in_file(sample_file, "PATTERN")
        assert result is True

    def test_string_exists_empty_file(self, bash, temp_dir):
        path = os.path.join(temp_dir, "empty.txt")
        bash.write_to_file(path, "")
        assert bash.string_exists_in_file(path, "x") is False

    def test_string_exists_empty_search_string(self, bash, sample_file):
        assert bash.string_exists_in_file(sample_file, "") is True

    def test_string_exists_nonexistent_file(self, bash, temp_dir):
        path = os.path.join(temp_dir, "nonexistent_xyz.txt")
        assert bash.string_exists_in_file(path, "x") is False


class TestCopy:
    """Tests for copy()."""

    @patch("basher.file_ops.subprocess.run")
    @patch("basher.file_ops.FileOps.exists")
    @patch("basher.file_ops.os.path.isfile")
    @patch("basher.file_ops.os.path.isdir")
    def test_copy_file(self, mock_isdir, mock_isfile, mock_exists, mock_run, bash):
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_isdir.return_value = False
        mock_run.return_value.returncode = 0
        assert bash.copy("/a", "/b") is True
        mock_run.assert_called_with("cp /a /b", shell=True)

    @patch("basher.file_ops.FileOps.exists")
    def test_copy_nonexistent_returns_false(self, mock_exists, bash):
        mock_exists.return_value = False
        assert bash.copy("/nonexistent", "/dest") is False

    @patch("basher.file_ops.subprocess.run")
    @patch("basher.file_ops.FileOps.exists")
    @patch("basher.file_ops.os.path.isfile")
    @patch("basher.file_ops.os.path.isdir")
    def test_copy_directory_recursive(self, mock_isdir, mock_isfile, mock_exists, mock_run, bash):
        mock_exists.return_value = True
        mock_isfile.return_value = False
        mock_isdir.return_value = True
        mock_run.return_value.returncode = 0
        assert bash.copy("/dir", "/dest", recursive=True) is True
        assert "cp -r" in mock_run.call_args[0][0]

    @patch("basher.file_ops.subprocess.run")
    @patch("basher.file_ops.FileOps.exists")
    @patch("basher.file_ops.os.path.isfile")
    @patch("basher.file_ops.os.path.isdir")
    def test_copy_directory_non_recursive(self, mock_isdir, mock_isfile, mock_exists, mock_run, bash):
        mock_exists.return_value = True
        mock_isfile.return_value = False
        mock_isdir.return_value = True
        mock_run.return_value.returncode = 0
        assert bash.copy("/dir", "/dest", recursive=False) is True
        assert "mkdir -p" in mock_run.call_args[0][0]


class TestMv:
    """Tests for mv()."""

    @patch("basher.file_ops.subprocess.run")
    @patch("basher.file_ops.FileOps.exists")
    def test_mv_success(self, mock_exists, mock_run, bash):
        mock_exists.return_value = True
        mock_run.return_value.returncode = 0
        assert bash.mv("/a", "/b") is True

    @patch("basher.file_ops.subprocess.run")
    @patch("basher.file_ops.FileOps.exists")
    def test_mv_failure_returns_false(self, mock_exists, mock_run, bash):
        mock_exists.return_value = True
        mock_run.return_value.returncode = 1
        assert bash.mv("/a", "/b") is False

    @patch("basher.file_ops.subprocess.run")
    @patch("basher.file_ops.FileOps.exists")
    def test_mv_path_with_spaces_quoted(self, mock_exists, mock_run, bash):
        mock_exists.return_value = True
        mock_run.return_value.returncode = 0
        assert bash.mv("/a b", "/c d") is True
        assert quote("/a b") in mock_run.call_args[0][0]


class TestFind:
    """Tests for find()."""

    @patch("basher.file_ops.FileOps.cmd")
    @patch("basher.file_ops.FileOps.folder_exists")
    def test_find_returns_list(self, mock_folder, mock_cmd, bash):
        mock_folder.return_value = True
        mock_cmd.return_value = "/a\n/b"
        assert bash.find("/dir", "*.txt") == ["/a", "/b"]

    @patch("basher.file_ops.FileOps.cmd")
    @patch("basher.file_ops.FileOps.folder_exists")
    def test_find_empty_returns_empty_list(self, mock_folder, mock_cmd, bash):
        mock_folder.return_value = True
        mock_cmd.return_value = ""
        assert bash.find("/dir", "*.xyz") == []

    @patch("basher.file_ops.FileOps.folder_exists")
    def test_find_nonexistent_dir_returns_none(self, mock_folder, bash):
        mock_folder.return_value = False
        assert bash.find("/nonexistent", "*.txt") is None

    @patch("basher.file_ops.FileOps.cmd")
    @patch("basher.file_ops.FileOps.folder_exists")
    def test_find_single_result(self, mock_folder, mock_cmd, bash):
        mock_folder.return_value = True
        mock_cmd.return_value = "/only.txt"
        assert bash.find("/dir", "*.txt") == ["/only.txt"]

    @patch("basher.file_ops.FileOps.cmd")
    @patch("basher.file_ops.FileOps.folder_exists")
    def test_find_result_with_trailing_newline(self, mock_folder, mock_cmd, bash):
        mock_folder.return_value = True
        mock_cmd.return_value = "/a\n/b\n"
        assert bash.find("/dir", "*.txt") == ["/a", "/b"]


class TestChmod:
    """Tests for chmod()."""

    @patch("basher.file_ops.FileOps.cmd")
    @patch("basher.file_ops.FileOps.exists")
    def test_chmod_recursive(self, mock_exists, mock_cmd, bash):
        mock_exists.return_value = True
        bash.chmod("/f", "755")
        assert "-R" in mock_cmd.call_args[0][0]

    @patch("basher.file_ops.FileOps.cmd")
    @patch("basher.file_ops.FileOps.exists")
    def test_chmod_non_recursive(self, mock_exists, mock_cmd, bash):
        mock_exists.return_value = True
        bash.chmod("/f", "755", recursive=False)
        assert "-R" not in mock_cmd.call_args[0][0]

    @patch("basher.file_ops.FileOps.exists")
    def test_chmod_nonexistent_returns_false(self, mock_exists, bash):
        mock_exists.return_value = False
        assert bash.chmod("/nonexistent", "755") is False

    @patch("basher.file_ops.FileOps.cmd")
    @patch("basher.file_ops.FileOps.exists")
    def test_chmod_path_with_spaces_quoted(self, mock_exists, mock_cmd, bash):
        mock_exists.return_value = True
        bash.chmod("/path with spaces", "755")
        assert quote("/path with spaces") in mock_cmd.call_args[0][0]


class TestChown:
    """Tests for chown()."""

    @patch("basher.file_ops.FileOps.cmd")
    @patch("basher.file_ops.FileOps.exists")
    def test_chown_with_group(self, mock_exists, mock_cmd, bash):
        mock_exists.return_value = True
        bash.chown("/f", "user", "group")
        assert "user:group" in mock_cmd.call_args[0][0]

    @patch("basher.file_ops.FileOps.cmd")
    @patch("basher.file_ops.FileOps.exists")
    def test_chown_user_only(self, mock_exists, mock_cmd, bash):
        mock_exists.return_value = True
        bash.chown("/f", "user")
        cmd_str = mock_cmd.call_args[0][0]
        assert "chown" in cmd_str and "user" in cmd_str and "user:group" not in cmd_str

    @patch("basher.file_ops.FileOps.exists")
    def test_chown_nonexistent_returns_false(self, mock_exists, bash):
        mock_exists.return_value = False
        assert bash.chown("/nonexistent", "user") is False


class TestExists:
    """Tests for exists()."""

    def test_exists_true(self, bash, temp_dir):
        assert bash.exists(temp_dir) is True

    def test_exists_false(self, bash, temp_dir):
        assert bash.exists(os.path.join(temp_dir, "nonexistent_xyz")) is False

    def test_exists_path_with_spaces(self, bash, temp_dir):
        path = os.path.join(temp_dir, "file with spaces.txt")
        bash.write_to_file(path, "x")
        assert bash.exists(path) is True


class TestFolderExists:
    """Tests for folder_exists()."""

    def test_folder_exists_true(self, bash, temp_dir):
        assert bash.folder_exists(temp_dir) is True

    def test_folder_exists_false_for_file(self, bash, sample_file):
        assert bash.folder_exists(sample_file) is False

    def test_folder_exists_false_for_nonexistent(self, bash, temp_dir):
        assert bash.folder_exists(os.path.join(temp_dir, "nonexistent_dir_xyz")) is False


class TestTail:
    """Tests for tail()."""

    @patch("basher.file_ops.FileOps.cmd")
    def test_tail_calls_cmd(self, mock_cmd, bash):
        bash.tail("/f", n=10)
        mock_cmd.assert_called_once()
        assert "tail" in mock_cmd.call_args[0][0]
        assert "10" in mock_cmd.call_args[0][0]

    @patch("basher.file_ops.FileOps.cmd")
    def test_tail_default_n(self, mock_cmd, bash):
        bash.tail("/f")
        assert "20" in mock_cmd.call_args[0][0]

    @patch("basher.file_ops.FileOps.cmd")
    def test_tail_n_1(self, mock_cmd, bash):
        bash.tail("/f", n=1)
        assert "1" in mock_cmd.call_args[0][0]


class TestDetectPackageManager:
    """Tests for detect_package_manager()."""

    @patch("basher.system_ops.SystemOps.cmd")
    def test_detect_apt(self, mock_cmd, bash):
        bash.system.package_manager = None
        mock_cmd.return_value = 0
        assert bash.detect_package_manager() == "apt"

    @patch("basher.system_ops.SystemOps.cmd")
    def test_detect_caches_result(self, mock_cmd, bash):
        bash.system.package_manager = None
        mock_cmd.return_value = 0
        bash.detect_package_manager()
        bash.detect_package_manager()
        assert mock_cmd.call_count == 1


class TestInstall:
    """Tests for install()."""

    @patch("basher.system_ops.SystemOps.cmd")
    @patch("basher.system_ops.SystemOps.detect_package_manager")
    def test_install_packages(self, mock_detect, mock_cmd, bash):
        mock_detect.return_value = "apt"
        mock_cmd.return_value = 0
        assert bash.install(["pkg1"]) is True

    @patch("basher.system_ops.SystemOps.detect_package_manager")
    def test_install_empty_list_returns_true(self, mock_detect, bash):
        assert bash.install([]) is True
        mock_detect.assert_not_called()

    @patch("basher.system_ops.SystemOps.cmd")
    @patch("basher.system_ops.SystemOps.detect_package_manager")
    def test_install_single_string_package(self, mock_detect, mock_cmd, bash):
        mock_detect.return_value = "apt"
        mock_cmd.return_value = 0
        assert bash.install("single-pkg") is True

    @patch("basher.system_ops.SystemOps.cmd")
    @patch("basher.system_ops.SystemOps.detect_package_manager")
    def test_install_no_package_manager_returns_false(self, mock_detect, mock_cmd, bash):
        mock_detect.return_value = None
        mock_cmd.return_value = 1  # grep: pkg not installed
        assert bash.install(["pkg"], check_installed=False) is False


class TestPurge:
    """Tests for purge()."""

    @patch("basher.system_ops.SystemOps.cmd")
    def test_purge_calls_apt(self, mock_cmd, bash):
        bash.purge("software")
        mock_cmd.assert_called_once()
        assert "purge" in mock_cmd.call_args[0][0]

    @patch("basher.system_ops.SystemOps.cmd")
    def test_purge_name_with_special_chars_quoted(self, mock_cmd, bash):
        bash.purge("pkg-name")
        assert quote("pkg-name") in mock_cmd.call_args[0][0]


class TestCd:
    """Tests for cd()."""

    @patch("basher.system_ops.os.path.isdir")
    @patch("basher.system_ops.os.chdir")
    def test_cd_success(self, mock_chdir, mock_isdir, bash):
        mock_isdir.return_value = True
        assert bash.cd("/dir") is True
        mock_chdir.assert_called_with("/dir")

    @patch("basher.system_ops.os.path.isdir")
    def test_cd_not_directory_returns_false(self, mock_isdir, bash):
        mock_isdir.return_value = False
        assert bash.cd("/file.txt") is False

    @patch("basher.system_ops.os.path.isdir")
    @patch("basher.system_ops.os.chdir")
    def test_cd_updates_working_dir(self, mock_chdir, mock_isdir, bash):
        mock_isdir.return_value = True
        bash.cd("/new/dir")
        assert bash.working_dir == "/new/dir"


class TestPwd:
    """Tests for pwd()."""

    @patch("basher.system_ops.SystemOps.cmd")
    def test_pwd_calls_cmd(self, mock_cmd, bash):
        bash.pwd()
        mock_cmd.assert_called_with("pwd", show_output=True)


class TestMkdir:
    """Tests for mkdir()."""

    @patch("basher.system_ops.subprocess.run")
    @patch("basher.system_ops.os.path.exists")
    def test_mkdir_creates_dir(self, mock_exists, mock_run, bash):
        mock_exists.return_value = False
        mock_run.return_value.returncode = 0
        assert bash.mkdir("/new/dir") is True
        mock_run.assert_called_with("mkdir -p /new/dir", shell=True)

    @patch("basher.system_ops.subprocess.run")
    @patch("basher.system_ops.os.path.exists")
    def test_mkdir_exist_ok_true_succeeds(self, mock_exists, mock_run, bash):
        mock_exists.return_value = True
        mock_run.return_value.returncode = 0
        assert bash.mkdir("/existing", exist_ok=True) is True

    @patch("basher.system_ops.os.path.exists")
    def test_mkdir_exist_ok_false_when_exists_returns_false(self, mock_exists, bash):
        mock_exists.return_value = True
        assert bash.mkdir("/existing", exist_ok=False) is False

    @patch("basher.system_ops.subprocess.run")
    @patch("basher.system_ops.os.path.exists")
    def test_mkdir_path_with_spaces_quoted(self, mock_exists, mock_run, bash):
        mock_exists.return_value = False
        mock_run.return_value.returncode = 0
        bash.mkdir("/path with spaces")
        assert quote("/path with spaces") in mock_run.call_args[0][0]


class TestRm:
    """Tests for rm()."""

    @patch("basher.system_ops.subprocess.run")
    @patch("basher.system_ops.SystemOps.exists")
    @patch("basher.system_ops.os.path.isfile")
    @patch("basher.system_ops.os.path.isdir")
    @patch("basher.system_ops.os.path.islink")
    def test_rm_file(self, mock_link, mock_isdir, mock_isfile, mock_exists, mock_run, bash):
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_isdir.return_value = mock_link.return_value = False
        mock_run.return_value.returncode = 0
        assert bash.rm("/f") is True

    @patch("basher.system_ops.subprocess.run")
    @patch("basher.system_ops.SystemOps.exists")
    @patch("basher.system_ops.os.path.isfile")
    @patch("basher.system_ops.os.path.isdir")
    @patch("basher.system_ops.os.path.islink")
    def test_rm_dir_recursive(self, mock_link, mock_isdir, mock_isfile, mock_exists, mock_run, bash):
        mock_exists.return_value = True
        mock_isfile.return_value = False
        mock_isdir.return_value = True
        mock_link.return_value = False
        mock_run.return_value.returncode = 0
        assert bash.rm("/dir", recursive=True) is True
        assert "rm -rf" in mock_run.call_args[0][0]

    @patch("basher.system_ops.SystemOps.exists")
    def test_rm_nonexistent_returns_false(self, mock_exists, bash):
        mock_exists.return_value = False
        assert bash.rm("/nonexistent") is False

    @patch("basher.system_ops.subprocess.run")
    @patch("basher.system_ops.SystemOps.exists")
    @patch("basher.system_ops.os.path.isfile")
    @patch("basher.system_ops.os.path.isdir")
    @patch("basher.system_ops.os.path.islink")
    def test_rm_symlink(self, mock_link, mock_isdir, mock_isfile, mock_exists, mock_run, bash):
        mock_exists.return_value = True
        mock_isfile.return_value = mock_isdir.return_value = False
        mock_link.return_value = True
        mock_run.return_value.returncode = 0
        assert bash.rm("/symlink") is True
        assert "rm " in mock_run.call_args[0][0]

    @patch("basher.system_ops.subprocess.run")
    @patch("basher.system_ops.SystemOps.exists")
    @patch("basher.system_ops.os.path.isfile")
    @patch("basher.system_ops.os.path.isdir")
    @patch("basher.system_ops.os.path.islink")
    def test_rm_dir_non_recursive(self, mock_link, mock_isdir, mock_isfile, mock_exists, mock_run, bash):
        mock_exists.return_value = True
        mock_isfile.return_value = mock_link.return_value = False
        mock_isdir.return_value = True
        mock_run.return_value.returncode = 0
        assert bash.rm("/emptydir", recursive=False) is True
        assert "rmdir" in mock_run.call_args[0][0]


    @patch("basher.file_ops.subprocess.run")
    @patch("basher.file_ops.FileOps.exists")
    @patch("basher.file_ops.os.path.isfile")
    @patch("basher.file_ops.os.path.isdir")
    def test_copy_source_neither_file_nor_dir_returns_false(self, mock_isdir, mock_isfile, mock_exists, mock_run, bash):
        mock_exists.return_value = True
        mock_isfile.return_value = False
        mock_isdir.return_value = False
        assert bash.copy("/symlink_or_other", "/dest") is False
        assert not any("cp " in str(c) for c in mock_run.call_args_list)


class TestArchive:
    """Tests for archive()."""

    @patch("basher.archive_ops.subprocess.run")
    @patch("basher.archive_ops.ArchiveOps.exists")
    @patch("basher.archive_ops.ArchiveOps.folder_exists")
    def test_archive_tar_gz(self, mock_folder, mock_exists, mock_run, bash):
        mock_exists.return_value = mock_folder.return_value = True
        mock_run.return_value.returncode = 0
        bash.archive_ops.fs = MagicMock()
        assert bash.archive("/src", "/out.tar.gz", "tar.gz") is True

    @patch("basher.archive_ops.subprocess.run")
    @patch("basher.archive_ops.ArchiveOps.exists")
    @patch("basher.archive_ops.ArchiveOps.folder_exists")
    def test_archive_zip(self, mock_folder, mock_exists, mock_run, bash):
        mock_exists.return_value = mock_folder.return_value = True
        mock_run.return_value.returncode = 0
        bash.archive_ops.fs = MagicMock()
        assert bash.archive("/src", "/out.zip", "zip") is True

    @patch("basher.archive_ops.ArchiveOps.exists")
    def test_archive_nonexistent_returns_false(self, mock_exists, bash):
        mock_exists.return_value = False
        assert bash.archive("/nonexistent", "/out.tar.gz") is False

    @patch("basher.archive_ops.ArchiveOps.exists")
    def test_archive_unsupported_format_returns_false(self, mock_exists, bash):
        mock_exists.return_value = True
        with patch.object(bash.archive_ops, "folder_exists", return_value=True):
            assert bash.archive("/src", "/out.rar", "rar") is False

    @patch("basher.archive_ops.subprocess.run")
    @patch("basher.archive_ops.ArchiveOps.exists")
    @patch("basher.archive_ops.ArchiveOps.folder_exists")
    def test_archive_tar_bz2(self, mock_folder, mock_exists, mock_run, bash):
        mock_exists.return_value = mock_folder.return_value = True
        mock_run.return_value.returncode = 0
        bash.archive_ops.fs = MagicMock()
        assert bash.archive("/src", "/out.tar.bz2", "tar.bz2") is True
        assert "tar" in mock_run.call_args[0][0] and "j" in mock_run.call_args[0][0]


class TestExtract:
    """Tests for extract()."""

    @patch("basher.archive_ops.subprocess.run")
    @patch("basher.archive_ops.ArchiveOps.exists")
    def test_extract_zip(self, mock_exists, mock_run, bash):
        mock_exists.return_value = True
        mock_run.return_value.returncode = 0
        assert bash.extract("/a.zip") is True

    @patch("basher.archive_ops.subprocess.run")
    @patch("basher.archive_ops.ArchiveOps.exists")
    def test_extract_tar_gz_with_destination(self, mock_exists, mock_run, bash):
        mock_exists.return_value = True
        mock_run.return_value.returncode = 0
        assert bash.extract("/a.tar.gz", "/dest") is True
        assert "-C" in mock_run.call_args[0][0]

    @patch("basher.archive_ops.ArchiveOps.exists")
    def test_extract_nonexistent_returns_false(self, mock_exists, bash):
        mock_exists.return_value = False
        assert bash.extract("/nonexistent.zip") is False

    @patch("basher.archive_ops.subprocess.run")
    @patch("basher.archive_ops.ArchiveOps.exists")
    def test_extract_tgz_extension(self, mock_exists, mock_run, bash):
        mock_exists.return_value = True
        mock_run.return_value.returncode = 0
        assert bash.extract("/a.tgz") is True
        assert "tar" in mock_run.call_args[0][0]

    @patch("basher.archive_ops.ArchiveOps.exists")
    def test_extract_unsupported_format_returns_false(self, mock_exists, bash):
        mock_exists.return_value = True
        assert bash.extract("/a.rar") is False


class TestGzip:
    """Tests for gzip()."""

    @patch("basher.archive_ops.subprocess.run")
    @patch("basher.archive_ops.ArchiveOps.exists")
    @patch("basher.archive_ops.os.path.isfile")
    def test_gzip_keep_original(self, mock_isfile, mock_exists, mock_run, bash):
        mock_exists.return_value = mock_isfile.return_value = True
        mock_run.return_value.returncode = 0
        bash.archive_ops.fs = MagicMock()
        assert bash.gzip("/f", keep_original=True) is True
        assert "-k" in mock_run.call_args[0][0]

    @patch("basher.archive_ops.subprocess.run")
    @patch("basher.archive_ops.ArchiveOps.exists")
    @patch("basher.archive_ops.os.path.isfile")
    def test_gzip_remove_original(self, mock_isfile, mock_exists, mock_run, bash):
        mock_exists.return_value = mock_isfile.return_value = True
        mock_run.return_value.returncode = 0
        bash.archive_ops.fs = MagicMock()
        assert bash.gzip("/f", keep_original=False) is True
        assert "-k" not in mock_run.call_args[0][0]

    @patch("basher.archive_ops.ArchiveOps.exists")
    @patch("basher.archive_ops.os.path.isfile")
    def test_gzip_directory_returns_false(self, mock_isfile, mock_exists, bash):
        mock_exists.return_value = True
        mock_isfile.return_value = False
        assert bash.gzip("/dir") is False

    @patch("basher.archive_ops.subprocess.run")
    @patch("basher.archive_ops.ArchiveOps.exists")
    @patch("basher.archive_ops.os.path.isfile")
    def test_gzip_failure_returns_false(self, mock_isfile, mock_exists, mock_run, bash):
        mock_exists.return_value = mock_isfile.return_value = True
        mock_run.return_value.returncode = 1
        bash.archive_ops.fs = MagicMock()
        assert bash.gzip("/f") is False


class TestGunzip:
    """Tests for gunzip()."""

    @patch("basher.archive_ops.subprocess.run")
    @patch("basher.archive_ops.ArchiveOps.exists")
    @patch("basher.archive_ops.os.path.isfile")
    def test_gunzip_success(self, mock_isfile, mock_exists, mock_run, bash):
        mock_exists.return_value = mock_isfile.return_value = True
        mock_run.return_value.returncode = 0
        bash.archive_ops.fs = MagicMock()
        assert bash.gunzip("/f.gz", keep_original=True) is True
        assert "gunzip" in mock_run.call_args[0][0]

    @patch("basher.archive_ops.ArchiveOps.exists")
    def test_gunzip_non_gz_returns_false(self, mock_exists, bash):
        mock_exists.return_value = True
        assert bash.gunzip("/f.txt") is False

    @patch("basher.archive_ops.ArchiveOps.exists")
    def test_gunzip_nonexistent_returns_false(self, mock_exists, bash):
        mock_exists.return_value = False
        assert bash.gunzip("/nonexistent.gz") is False

    @patch("basher.archive_ops.ArchiveOps.exists")
    @patch("basher.archive_ops.os.path.isfile")
    def test_gunzip_directory_returns_false(self, mock_isfile, mock_exists, bash):
        mock_exists.return_value = True
        mock_isfile.return_value = False
        assert bash.gunzip("/dir.gz") is False


class TestDownload:
    """Tests for download()."""

    @patch("basher.archive_ops.subprocess.run")
    def test_download_with_dest(self, mock_run, bash):
        mock_run.return_value.returncode = 0
        assert bash.download("https://x.com/f", "/dest") is True
        assert "-o" in mock_run.call_args[0][0]

    @patch("basher.archive_ops.subprocess.run")
    def test_download_without_dest(self, mock_run, bash):
        mock_run.return_value.returncode = 0
        assert bash.download("https://x.com/f") is True
        assert "curl" in mock_run.call_args[0][0]

    @patch("basher.archive_ops.subprocess.run")
    def test_download_failure_returns_false(self, mock_run, bash):
        mock_run.return_value.returncode = 1
        assert bash.download("https://x.com/f", "/dest") is False

    @patch("basher.archive_ops.subprocess.run")
    def test_download_url_with_special_chars_quoted(self, mock_run, bash):
        mock_run.return_value.returncode = 0
        bash.download("https://x.com/file?name=foo&id=1", "/dest")
        assert quote("https://x.com/file?name=foo&id=1") in mock_run.call_args[0][0]


class TestEcho:
    """Tests for echo()."""

    @patch("basher.basher.BashCommand.cmd")
    def test_echo_calls_cmd(self, mock_cmd, bash):
        bash.echo("msg")
        mock_cmd.assert_called_once()

    @patch("basher.basher.BashCommand.cmd")
    def test_echo_with_color(self, mock_cmd, bash):
        bash.echo("msg", color="red")
        mock_cmd.assert_called_once()
        assert "033" in mock_cmd.call_args[0][0] or "31" in mock_cmd.call_args[0][0]

    @patch("basher.basher.BashCommand.cmd")
    def test_echo_with_custom_end(self, mock_cmd, bash):
        bash.echo("msg", end="")
        mock_cmd.assert_called_once()

    @patch("basher.basher.BashCommand.cmd")
    def test_echo_message_with_single_quotes_escaped(self, mock_cmd, bash):
        bash.echo("it's fine")
        cmd = mock_cmd.call_args[0][0]
        assert "it" in cmd and "fine" in cmd

    @patch("basher.basher.BashCommand.cmd")
    def test_echo_invalid_color_ignored(self, mock_cmd, bash):
        bash.echo("msg", color="invalid")
        mock_cmd.assert_called_once()


class TestVerbosity:
    """Tests for set_verbosity / get_verbosity."""

    def test_set_and_get_verbosity(self, bash):
        bash.set_verbosity(2)
        assert bash.get_verbosity() == 2
        bash.set_verbosity(0)


class TestSetEmulate:
    """Tests for set_emulate()."""

    def test_set_emulate_on(self, bash):
        bash.set_emulate(True)
        assert bash.emulate is True

    def test_set_emulate_off(self, bash):
        bash.set_emulate(True)
        bash.set_emulate(False)
        assert bash.emulate is False

    def test_set_emulate_falsy_becomes_false(self, bash):
        bash.set_emulate(True)
        bash.set_emulate(0)
        assert bash.emulate is False


class TestOutputMethods:
    """Tests for error, warning, success, info."""

    @patch("basher.core.BashCommand.cmd")
    def test_error_calls_cmd(self, mock_cmd, bash):
        bash.error("msg")
        mock_cmd.assert_called_once()
        assert "msg" in mock_cmd.call_args[0][0]

    @patch("basher.core.BashCommand.cmd")
    def test_warning_calls_cmd(self, mock_cmd, bash):
        bash.warning("msg")
        mock_cmd.assert_called_once()

    @patch("basher.core.BashCommand.cmd")
    def test_success_calls_cmd(self, mock_cmd, bash):
        bash.success("msg")
        mock_cmd.assert_called_once()
        assert "msg" in mock_cmd.call_args[0][0]

    @patch("basher.core.BashCommand.cmd")
    def test_info_calls_cmd(self, mock_cmd, bash):
        bash.info("msg")
        mock_cmd.assert_called_once()
        assert "msg" in mock_cmd.call_args[0][0]


class TestIntegration:
    """Integration tests with real files."""

    def test_write_read_roundtrip(self, bash, temp_dir):
        path = os.path.join(temp_dir, "roundtrip.txt")
        content = "hello\nworld"
        bash.write_to_file(path, content)
        assert bash.read_file(path) == content

    def test_exists_and_folder_exists_real(self, bash, temp_dir, sample_file, sample_dir):
        assert bash.exists(temp_dir) is True
        assert bash.exists(sample_file) is True
        assert bash.folder_exists(temp_dir) is True
        assert bash.folder_exists(sample_dir) is True
        assert bash.folder_exists(sample_file) is False


class TestBasherInit:
    """Tests for Basher initialization."""

    def test_init_with_none_uses_cwd(self):
        with patch("basher.basher.os.getcwd", return_value="/home"):
            b = Basher()
            assert b.working_dir == "/home"

    def test_init_with_nonexistent_dir_raises(self):
        with pytest.raises(ValueError, match="does not exist"):
            Basher("/nonexistent/path_xyz_123")



class TestConditional:
    """Tests for if_condition, elif_condition, else_condition, ifend."""

    @patch("basher.core.subprocess.run")
    def test_if_condition_true(self, mock_run, bash):
        mock_run.return_value = MagicMock(returncode=0)
        assert bash.if_condition("test -f /x") is True

    @patch("basher.core.subprocess.run")
    def test_if_condition_false(self, mock_run, bash):
        mock_run.return_value = MagicMock(returncode=1)
        assert bash.if_condition("test -f /x") is False

    @patch("basher.core.subprocess.run")
    def test_elif_after_if_skipped_when_if_true(self, mock_run, bash):
        mock_run.return_value = MagicMock(returncode=0)
        bash.if_condition("test -f /x")
        result = bash.elif_condition("test -d /y")
        assert result is False

    def test_elif_without_if_raises(self, bash):
        with pytest.raises(RuntimeError, match="without a preceding"):
            bash.elif_condition("test -f /x")

    def test_else_without_if_raises(self, bash):
        with pytest.raises(RuntimeError, match="without a preceding"):
            bash.else_condition()

    @patch("basher.core.subprocess.run")
    def test_ifend_clears_state(self, mock_run, bash):
        mock_run.return_value = MagicMock(returncode=0)
        bash.if_condition("test -f /x")
        bash.ifend()
        assert not hasattr(bash, "_last_if_result")

    @patch("basher.core.subprocess.run")
    def test_elif_executed_when_if_false(self, mock_run, bash):
        mock_run.return_value = MagicMock(returncode=1)
        bash.if_condition("test -f /x")
        mock_run.return_value = MagicMock(returncode=0)
        result = bash.elif_condition("test -d /y")
        assert result is True

    @patch("basher.core.subprocess.run")
    def test_else_executed_when_if_false(self, mock_run, bash):
        mock_run.return_value = MagicMock(returncode=1)
        bash.if_condition("test -f /x")
        result = bash.else_condition()
        assert result is True


class TestSupervisorD:
    """Tests for SupervisorD class."""

    @patch("basher.supervisord.BashCommand.cmd")
    def test_init(self, mock_cmd, temp_dir):
        from basher import SupervisorD
        sup = SupervisorD(temp_dir)
        mock_cmd.return_value = 0
        sup.init("/etc/supervisord.conf")
        mock_cmd.assert_called_once()
        assert "supervisord" in mock_cmd.call_args[0][0]

    @patch("basher.supervisord.BashCommand.cmd")
    def test_start_program(self, mock_cmd, temp_dir):
        from basher import SupervisorD
        sup = SupervisorD(temp_dir)
        mock_cmd.return_value = 0
        sup.start_program("myapp")
        mock_cmd.assert_called_once()
        assert "start" in mock_cmd.call_args[0][0]

    @patch("basher.supervisord.BashCommand.cmd")
    def test_reread(self, mock_cmd, temp_dir):
        from basher import SupervisorD
        sup = SupervisorD(temp_dir)
        mock_cmd.return_value = 0
        sup.reread()
        mock_cmd.assert_called_once()
        assert "reread" in mock_cmd.call_args[0][0]


class TestEnvVar:
    """Tests for env_var()."""

    def test_env_var_set_and_get(self, bash):
        bash.env_var("BASHER_TEST_VAR", "testval")
        assert os.environ.get("BASHER_TEST_VAR") == "testval"
        # Clean up
        os.environ.pop("BASHER_TEST_VAR", None)

    def test_env_var_get_existing(self, bash):
        os.environ["BASHER_TEST_VAR2"] = "existing"
        with patch("basher.system_ops.SystemOps.cmd") as mock_cmd:
            mock_cmd.return_value = "existing"
            result = bash.env_var("BASHER_TEST_VAR2")
        assert result == "existing"
        os.environ.pop("BASHER_TEST_VAR2", None)


class TestEnsureSudo:
    """Tests for ensure_sudo()."""

    @patch("basher.system_ops.SystemOps.detect_package_manager")
    @patch("basher.system_ops.SystemOps.cmd")
    def test_ensure_sudo_installs_when_missing(self, mock_cmd, mock_detect, bash):
        mock_cmd.side_effect = [1, 0]  # which sudo fails, install succeeds
        mock_detect.return_value = "apt"
        assert bash.ensure_sudo() is True


class TestCommandExists:
    """Tests for command_exists()."""

    @patch("basher.system_ops.SystemOps.cmd")
    def test_command_exists_true(self, mock_cmd, bash):
        mock_cmd.return_value = 0
        assert bash.command_exists("php") is True

    @patch("basher.system_ops.SystemOps.cmd")
    def test_command_exists_false(self, mock_cmd, bash):
        mock_cmd.return_value = 1
        assert bash.command_exists("nonexistent") is False


class TestUserExists:
    """Tests for user_exists()."""

    @patch("basher.system_ops.SystemOps.cmd")
    def test_user_exists_true(self, mock_cmd, bash):
        mock_cmd.return_value = 0
        assert bash.user_exists("root") is True

    @patch("basher.system_ops.SystemOps.cmd")
    def test_user_exists_false(self, mock_cmd, bash):
        mock_cmd.return_value = 2
        assert bash.user_exists("nonexistent") is False


class TestAddAptRepository:
    """Tests for add_apt_repository()."""

    @patch("basher.system_ops.SystemOps.cmd")
    def test_add_apt_repository(self, mock_cmd, bash):
        mock_cmd.return_value = 0
        assert bash.add_apt_repository("ppa:ondrej/php") is True
        mock_cmd.assert_called_once()
        assert "add-apt-repository" in mock_cmd.call_args[0][0]


class TestComposerInstall:
    """Tests for composer_install()."""

    @patch("basher.system_ops.SystemOps.cmd")
    def test_composer_install(self, mock_cmd, bash):
        mock_cmd.return_value = 0
        assert bash.composer_install() is True
        assert "composer install" in mock_cmd.call_args[0][0]

    @patch("basher.system_ops.SystemOps.cmd")
    def test_composer_install_no_scripts(self, mock_cmd, bash):
        mock_cmd.return_value = 0
        assert bash.composer_install(no_scripts=True) is True
        assert "--no-scripts" in mock_cmd.call_args[0][0]


class TestNpmInstall:
    """Tests for npm_install()."""

    @patch("basher.system_ops.SystemOps.cmd")
    def test_npm_install_with_prefix(self, mock_cmd, bash):
        mock_cmd.return_value = 0
        assert bash.npm_install(prefix="/var/www/html") is True
        assert "--prefix" in mock_cmd.call_args[0][0]


class TestRunOk:
    """Tests for run_ok()."""

    @patch("basher.core.subprocess.run")
    def test_run_ok_success(self, mock_run, bash):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        assert bash.run_ok("ls") is True

    @patch("basher.core.subprocess.run")
    def test_run_ok_failure(self, mock_run, bash):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")
        assert bash.run_ok("false") is False
