"""
Basher - Python utilities that wrap bash commands

This package provides a set of utility functions that wrap bash commands,
making it easier to perform common file and system operations in Python.
"""

from .basher import Basher
from .supervisord import SupervisorD

# Create a default instance for backward compatibility
_default_instance = Basher()

# Expose functions from the default instance for backward compatibility
cmd = _default_instance.cmd
execute_in_directory = _default_instance.execute_in_directory


# File operations
write_to_file = _default_instance.write_to_file
read_file = _default_instance.read_file
replace_in_file = _default_instance.replace_in_file
string_in_file = _default_instance.string_in_file
copy = _default_instance.copy
mv = _default_instance.mv
find = _default_instance.find
chmod = _default_instance.chmod
chown = _default_instance.chown

# System operations
detect_package_manager = _default_instance.detect_package_manager
install = _default_instance.install
cd = _default_instance.cd
mkdir = _default_instance.mkdir
rm = _default_instance.rm

# Archive operations
archive = _default_instance.archive
extract = _default_instance.extract
gzip = _default_instance.gzip
gunzip = _default_instance.gunzip
download = _default_instance.download

# Output operations
echo = _default_instance.echo

__version__ = '0.1.0' 