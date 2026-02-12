"""Pytest fixtures for Basher tests."""

import os
import tempfile
import shutil

import pytest

from basher import Basher


@pytest.fixture(autouse=True)
def reset_verbosity():
    """Reset verbosity after each test to avoid leaking state."""
    yield
    os.environ.pop("BASHER_VERBOSITY", None)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files. Cleaned up after test."""
    test_dir = tempfile.mkdtemp()
    yield test_dir
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)


@pytest.fixture
def bash(temp_dir):
    """Basher instance with working_dir set to temp directory."""
    old_dir = os.getcwd()
    os.chdir(temp_dir)
    instance = Basher(temp_dir)
    yield instance
    os.chdir(old_dir)


@pytest.fixture
def sample_file(temp_dir):
    """Create a sample file with content."""
    path = os.path.join(temp_dir, "sample.txt")
    with open(path, "w") as f:
        f.write("line1\nline2 pattern here\nline3\n")
    return path


@pytest.fixture
def sample_dir(temp_dir):
    """Create a sample directory with files."""
    path = os.path.join(temp_dir, "sample_dir")
    os.makedirs(path)
    for f in ["a.txt", "b.txt", "c.jpg"]:
        with open(os.path.join(path, f), "w") as fp:
            fp.write("content")
    return path
