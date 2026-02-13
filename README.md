# Basher

Basher is a Python library that provides a convenient wrapper around common bash commands, making it easier to perform file system operations, package management, and archive handling in Python scripts. Basher can also be used to build Docker images and used in Dockerfiles.

## Quick start

```bash
# Install from PyPI
pip3 install basher2

# Or install from repo (for development)
cd Basher && pip3 install -e .

# Run tests
python3 -m pytest tests/ -v
```

## Project structure

```
Basher/
├── basher/           # Library source
├── install-oro.py    # OroCommerce install script
├── install-magento.py
├── tests/            # pytest tests
├── tests.py          # legacy tests
├── docker-compose.yml
├── Dockerfile
└── docs/
```

## Philosophy

**When Python is used instead of shell commands, the output must match the Linux command analog—so that copying the output allows reproduction without Python.** See [docs/PHILOSOPHY.md](docs/PHILOSOPHY.md) for the full design principles.

# Why Python for Bash

Python is a great choice for tasks that you might otherwise do in a Bash script for several reasons:

## Readability and Maintainability

Python’s syntax is often more readable and less prone to subtle errors compared to complex Bash one-liners.
It’s easier for teams (especially those less familiar with shell scripting) to understand and maintain Python scripts.

## Large Standard Library

Python has built-in support for common tasks like working with files, directories, CSV or JSON data, HTTP requests, etc.
In Bash, you often need external utilities (like awk, sed, curl, etc.) or rely on multiple commands piped together.

## Portability

Python is available on most modern systems, including Linux, macOS, and Windows.
Complex Bash scripts can run into portability issues when you use commands or shell features that differ across Unix-like systems.

## Error Handling and Debugging

Python’s exception handling is more robust and easier to manage compared to handling exit codes and conditional branching in Bash.
Python’s built-in debugger (pdb) can step through code, making it simpler to diagnose and fix problems.

## Scaling Complexity

As your script grows, Python can handle more advanced logic, data structures, and third-party libraries with ease.
Bash scripts become harder to read and maintain once they get beyond trivial tasks.

## Better for String Manipulation and Data Parsing

Python excels at parsing logs, JSON, XML, CSV, and other data formats with minimal hassle.
In Bash, such tasks quickly get messy, often requiring multiple external tools.

## Easier Interfacing with Other Systems

Whether you need to interact with databases, perform network calls, or handle complex file I/O, Python provides a straightforward approach.
While Bash can call these tools, chaining them together can be more cumbersome.

## Features

- **File Operations**: Read, write, copy, move, and find files
- **System Operations**: Install packages, create directories, change permissions
- **Archive Operations**: Create and extract archives, compress and decompress files
- **Command Execution**: Run bash commands with proper error handling
- **Colorful Output**: Display messages in different colors for better visibility
- **Interactive Mode**: Interactive mode for easy configuration of the script
- **No Interaction Mode**: No interaction mode for easy installation of the script
- **Detect Package Manager**: Detect the system's package manager

## Compilation to bash script

By design, Basher is a Python library; however, it can be compiled into a Bash script, with each command acting as a straightforward Python wrapper in pure Bash.

# Methodology

One Core Basher method is to use `bash.cmd` to execute commands. This method is a wrapper around the `bash` command and is the most straightforward way to execute commands. 

In our implementation we wraping one logical server configuration into one method using basher core commands.

Forexample:
Install git and configure it
```python
def install_git():
    bash.echo("Installing git")
    bash.install("git")
    bash.cmd("git config --global user.name 'John Doe'")
    bash.cmd("git config --global user.email 'john.doe@example.com'")
```

Install nginx
```python
def install_nginx():
    bash.echo("Installing nginx")
    bash.install("nginx")
```

Install php
```python
def install_php():
    bash.echo("Installing php")
    bash.install("php")
```

Install mysql
```python
def install_mysql():
    bash.echo("Installing mysql")
    bash.install("mysql")
```

Install redis
```python
def install_redis():
    bash.echo("Installing redis")
    bash.install("redis")
```

Install postgresql
```python
def install_postgresql():
    bash.echo("Installing postgresql")
    bash.install("postgresql")
```

Install elasticsearch
```python
def install_elasticsearch():
    bash.echo("Installing elasticsearch")
    bash.install("elasticsearch")
```

Install node.js
```python
def install_nodejs():
    bash.echo("Installing node.js")
    bash.install("nodejs")
    bash.install("npm")
    bash.cmd("npm install -g yarn")
```

Install docker
```python
def install_docker():
    bash.echo("Installing docker")
    bash.install("docker")
    bash.cmd("docker --version")
    bash.echo("Installing docker compose")
    bash.install("docker-compose")
```

Install elasticsearch
```python
def install_elasticsearch():
    bash.echo("Installing elasticsearch")
    bash.install("elasticsearch")
```

Install composer for php
```python
def install_composer():
    bash.cmd("php -r \"copy('https://getcomposer.org/installer', 'composer-setup.php');\"")
    bash.cmd("php composer-setup.php")
    bash.cmd("php -r \"unlink('composer-setup.php');\"")
    bash.cmd("mv composer.phar /usr/bin/composer")
    bash.cmd("composer --version")
    bash.echo("Composer installed")
```

# Complex Installation Example

Here's an example of a complex installation using Basher, divided into logical methods:

```python
def setup_web_server():
    bash.echo("Setting up web server environment")
    install_nginx()
    install_php()
    install_mysql()
    configure_nginx_for_php()
    bash.echo("Web server environment setup complete")

def install_nginx():
    bash.echo("Installing Nginx")
    bash.install("nginx")
    bash.cmd("systemctl start nginx")
    bash.cmd("systemctl enable nginx")

def install_php():
    bash.echo("Installing PHP")
    bash.install("php-fpm")
    bash.install("php-mysql")

def install_mysql():
    bash.echo("Installing MySQL")
    bash.install("mysql-server")
    bash.cmd("systemctl start mysql")
    bash.cmd("systemctl enable mysql")

def configure_nginx_for_php():
    bash.echo("Configuring Nginx to use PHP")
    bash.write_to_file("/etc/nginx/sites-available/default", """
    server {
        listen 80;
        server_name example.com;
        root /var/www/html;

        index index.php index.html index.htm;

        location / {
            try_files $uri $uri/ =404;
        }

        location ~ \.php$ {
            include snippets/fastcgi-php.conf;
            fastcgi_pass unix:/var/run/php/php7.4-fpm.sock;
        }

        location ~ /\.ht {
            deny all;
        }
    }
    """)
    bash.cmd("systemctl restart nginx")
```

## Usage

### Basic Usage

```python
from basher import Basher

# Create a Basher instance
bash = Basher()

# Execute a shell command
output = bash.cmd("ls -la")

# Write to a file
bash.write_to_file("/path/to/file.txt", "Hello, world!")

# Read from a file
content = bash.read_file("/path/to/file.txt")

# Check if a file exists
if bash.exists("/path/to/file.txt"):
    print("File exists!")
```

### File Operations

```python
# Copy a file
bash.copy("/source/file.txt", "/destination/file.txt")

# Move a file
bash.mv("/source/file.txt", "/destination/file.txt")

# Find files matching a pattern
files = bash.find("/search/directory", "*.txt")

# Check if a string exists in a file
if bash.string_in_file("/path/to/file.txt", "search string"):
    print("String found!")

# Replace content in a file
bash.replace_in_file("/path/to/file.txt", "old_pattern", "new_content")

# Change file permissions
bash.chmod("/path/to/file.txt", "755")

# Change file ownership
bash.chown("/path/to/file.txt", "user", "group")
```

### System Operations

```python
# Detect the system's package manager
package_manager = bash.detect_package_manager()
print(f"Using package manager: {package_manager}")

# Install packages
bash.install(["git", "curl", "wget"])

# Create a directory
bash.mkdir("/path/to/directory")

# Change directory
bash.cd("/path/to/directory")

# Remove a file or directory
bash.rm("/path/to/file.txt")
bash.rm("/path/to/directory", recursive=True)

# Ensure sudo is available
if bash.ensure_sudo():
    print("Sudo is available")
```

### Archive Operations

```python
# Create an archive
bash.archive("/source/directory", "/path/to/archive.tar.gz", format="tar.gz")

# Extract an archive
bash.extract("/path/to/archive.tar.gz", "/destination/directory")

# Compress a file with gzip
bash.gzip("/path/to/file.txt", keep_original=True)

# Decompress a gzipped file
bash.gunzip("/path/to/file.txt.gz", keep_original=False)

# Download a file
bash.download("https://example.com/file.txt", "/path/to/save/file.txt")
```

### Colorful Output

```python
# Display messages in different colors
bash.error("This is an error message")  # Red
bash.warning("This is a warning message")  # Yellow
bash.success("This is a success message")  # Green
bash.info("This is an info message")  # Blue

# Use the echo method with colors
bash.echo("This is a colored message", color="cyan")
```

## Command Execution in a Directory

```python
# Execute a command in a specific directory
output = bash.execute_in_directory("ls -la", "/path/to/directory")
```

## Error Handling

Most methods return `True` if successful and `False` if they fail, making it easy to check for errors:

```python
if not bash.mkdir("/path/to/directory"):
    print("Failed to create directory")
```
## Build for PyPI

Change version in `setup.py` and run:

```bash
rm -rf dist/*
python3 setup.py sdist bdist_wheel
python3 -m twine upload dist/*
```

Add credentials to `~/.pypirc`:

```
[pypi]
username = __token__
password = pypi-AgEIcH***
```

Or use environment variables:

```bash
export PYPI_USERNAME=__token__
export PYPI_PASSWORD=pypi-AgEIcH***
```

## Installation

```bash
sudo apt install python3 python3-pip
pip3 install basher2
```

## Testing

```bash
# Pytest (147 tests)
python3 -m pytest tests/ -v

# Legacy tests
python3 tests.py
```

## Docker (OroCommerce & Magento install scripts)

**Prerequisites:** Docker and Docker Compose.

### Quick start

```bash
# Build the image
docker compose build

# Run Magento full install (non-interactive)
docker compose run --rm magento-install --no-interaction

# Run OroCommerce full install (non-interactive)
docker compose run --rm oro-install --no-interaction
```

### Magento install (`install-magento.py`)

Installs: PHP 8.2, Composer, Nginx, MySQL, Redis, Elasticsearch. Magento is installed at `/var/www/html/magento`.

```bash
# Interactive menu (choose steps with arrow keys)
docker compose run --rm magento-install

# Full install (runs all steps automatically)
docker compose run --rm magento-install --no-interaction
```

### Test Magento install inside container

Get a shell inside the container and run the install manually:

```bash
# Start interactive shell (overrides default entrypoint)
docker compose run --rm --entrypoint bash magento-install

# Inside the container (/app is the project root):
python3 install-magento.py                    # interactive menu
python3 install-magento.py --no-interaction   # full install
```

From the interactive menu you can run individual steps (1–8): Packages, PHP, Nginx, MySQL, Redis, Elasticsearch, Magento setup, or Full installation.

### OroCommerce install (`install-oro.py`)

Installs: PHP 8.3, Composer, Node.js, Nginx, Supervisor, MySQL/PostgreSQL, Redis, Elasticsearch.

```bash
docker compose run --rm oro-install                    # interactive menu
docker compose run --rm oro-install --no-interaction   # full install
```

### Script options

| Option | Description |
|--------|-------------|
| `--no-interaction` | Full install without prompts |
| `-v`, `--verbose` | Increase verbosity |
| `-n`, `--no-inp` | No input mode |

### Notes

- The project is mounted at `/app`, so code changes are reflected immediately without rebuilding.
- Build with verbose output: `docker compose build --progress=plain`

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
