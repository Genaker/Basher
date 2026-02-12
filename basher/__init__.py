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
string_exists_in_file = _default_instance.string_exists_in_file
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

# Verbosity
set_verbosity = _default_instance.set_verbosity
get_verbosity = _default_instance.get_verbosity

# Dry-run: set_emulate(True) makes cmd() skip execution
set_emulate = _default_instance.set_emulate

# Installation helpers
command_exists = _default_instance.command_exists
user_exists = _default_instance.user_exists
add_apt_repository = _default_instance.add_apt_repository
composer_install = _default_instance.composer_install
npm_install = _default_instance.npm_install
service_start = _default_instance.service_start
run_ok = _default_instance.run_ok

__version__ = '0.1.0' 