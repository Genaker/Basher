#!/usr/bin/env python3
"""
OroCommerce Installation Script

This script provides an interactive menu for installing and configuring OroCommerce.
It uses the Basher library to execute shell commands.
"""

import curses
import sys
import os
import re
from basher import Basher, SupervisorD
import argparse

def get_input(prompt, default):
    """Get user input with a default value."""
    response = input(f"{prompt} [{default}]: ")
    return response if response else default


def install_php(php_ini_path, php_version="8.3"):

    bash.echo("install PHP...")

    bash.install("software-properties-common")
    bash.add_apt_repository("ppa:ondrej/php")
    bash.cmd("apt update")
    
    bash.env_var("php_version", php_version)
    bash.rm(f"/etc/php/{php_version}/cli/php.ini");
    bash.rm(f"/etc/php/{php_version}/fpm/php.ini");
    bash.install([
        f"php{php_version}", f"php{php_version}-fpm", f"php{php_version}-cli",
        f"php{php_version}-pdo", f"php{php_version}-mysqlnd", f"php{php_version}-redis",
        f"php{php_version}-xml", f"php{php_version}-soap", f"php{php_version}-gd",
        f"php{php_version}-zip", f"php{php_version}-intl", f"php{php_version}-mbstring",
        f"php{php_version}-opcache", f"php{php_version}-curl", f"php{php_version}-bcmath",
        f"php{php_version}-ldap", f"php{php_version}-pgsql", f"php{php_version}-dev",
        f"php{php_version}-mongodb"
    ])
    php_settings = """
    memory_limit = 2048M
    max_input_time = 600
    max_execution_time = 600
    realpath_cache_size=4096K
    realpath_cache_ttl=600
    opcache.enable=1
    opcache.enable_cli=0
    opcache.memory_consumption=512
    opcache.interned_strings_buffer=32
    opcache.max_accelerated_files=32531
    opcache.save_comments=1"""
    php_ini_fpm_path =  f"/etc/php/{php_version}/fpm/php.ini"
    php_ini_cli_path = f"/etc/php/{php_version}/cli/php.ini"
    print(php_ini_fpm_path)
    print(php_ini_cli_path)
    bash.write_to_file(php_ini_fpm_path, php_settings, 'a')
    php_settings_cli = "memory_limit = 2048M"
    bash.write_to_file(php_ini_cli_path, php_settings_cli, 'a')
    bash.cmd("rm -rf /usr/bin/composer")
    bash.cmd("php -r \"copy('https://getcomposer.org/installer', 'composer-setup.php');\"")
    bash.cmd("php composer-setup.php")
    bash.cmd("php -r \"unlink('composer-setup.php');\"")
    cd=bash.cmd('pwd', capture_output=True).strip()
    bash.cmd("ls")
    bash.pwd()
    print("Current directory:" + bash.working_dir)
    bash.cmd(f"mv {cd}/composer.phar /usr/bin/composer")
    bash.cmd("composer --version")
    bash.cmd("apt-get clean")

    bash.echo(f"PHP configured successfully in {php_ini_fpm_path}")
    
    """Configure PHP settings."""
    settings = """
    memory_limit = 2048M
    max_input_time = 600
    max_execution_time = 600
    realpath_cache_size=4096K
    realpath_cache_ttl=600
    opcache.enable=1
    opcache.enable_cli=0
    opcache.memory_consumption=512
    opcache.interned_strings_buffer=32
    opcache.max_accelerated_files=32531
    opcache.save_comments=1
    """
    bash.write_to_file(php_ini_fpm_path, settings, 'a')
    bash.cmd("php -v", show_output=True)
    bash.echo(f"PHP configured successfully in {php_ini_fpm_path}")


def install_nginx(nginx_conf_path):
    bash.echo("install Nginx...")
    bash.install("nginx")
    bash.cmd("apt-get clean")
    bash.cmd("rm -rf /var/lib/apt/lists/*")
    bash.mkdir("/var/www/html/oro/")
    bash.echo("Nginx installed successfully")

    bash.echo("Configure Nginx...")
    """Configure Nginx."""
    nginx_conf = """
server {
    server_name localhost www.localhost 127.0.0.1;
    root /var/www/html/oro/public;

    location / {
        try_files $uri /index.php$is_args$args;
    }

    location ~ ^/(index|index_dev|config|install)\\.php(/|$) {
        fastcgi_pass unix:/run/php/php8.3-fpm.sock;
        fastcgi_split_path_info ^(.+\\.php)(/.*)$;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_param HTTPS off;
    }

    location ~* ^[^(\\.php)]+\\.(jpg|jpeg|gif|png|ico|css|pdf|ppt|txt|bmp|rtf|js)$ {
        access_log off;
        expires 1h;
        add_header Cache-Control public;
    }

    error_log /var/log/nginx/localhost_error.log;
    access_log /var/log/nginx/localhost_access.log;
}
"""
    bash.write_to_file(nginx_conf_path, nginx_conf, 'w')
    bash.echo(f"Nginx configured successfully in {nginx_conf_path}")


def setup_postgresql(db_name, db_user, db_password):
    """Setup PostgreSQL database."""
    bash.echo("Setup PostgreSQL database...")
    bash.install(["postgresql", "postgresql-contrib"])
    bash.service_start("postgresql")
    bash.cmd(f"sudo -u postgres psql -c \"DROP DATABASE IF EXISTS {db_name};\"")
    bash.cmd(f"sudo -u postgres psql -c \"CREATE DATABASE {db_name};\"")
    bash.cmd(f"sudo -u postgres psql -c \"ALTER USER {db_user} WITH PASSWORD '{db_password}';\"")
    
    bash.cmd(f"sudo -u postgres psql -d {db_name} -c \"CREATE EXTENSION IF NOT EXISTS \\\"uuid-ossp\\\";\"")
    
    bash.echo(f"PostgreSQL database '{db_name}' set up successfully")
    bash.echo(f"{bash.GREEN}PostgreSQL installed successfully{bash.RESET}")
    bash.echo("List all databases in PostgreSQL:")
    # List all databases in PostgreSQL (correct command)
    bash.cmd(f"sudo -u postgres psql -c \"\\l\"")

def install_node(node_version='20'):
    """Install Node.js."""
    bash.cmd(f"curl -sL https://deb.nodesource.com/setup_{node_version}.x -o /tmp/nodesource_setup.sh")

    bash.cmd("bash /tmp/nodesource_setup.sh")
    bash.cmd("apt-get install -y nodejs")

    return bash.cmd("node -v", assert_returncode=0)

def clone_and_setup_orocommerce(repo_url, branch, install_dir, admin_user, admin_email, admin_firstname, admin_lastname, admin_password):
    """Clone and setup OroCommerce."""
    bash.rm("/var/www/html/oro")
    bash.mkdir("/var/www/html/oro")
    bash.cd("/var/www/html/oro")
    bash.cmd("git clone --branch 6.0 https://github.com/oroinc/orocommerce-application.git /var/www/html/oro")
    bash.cd("/var/www/html/oro")
    bash.cmd("ls -la")

    if install_node() != 0:
        bash.echo("Node.js installation failed")
        exit(1)
    
    node_version = bash.cmd("node -v", capture_output=True)
    print(f"Node version: {node_version}")
    bash.env_var("TEST", "test1")
    print("Print TEST:")
    bash.env_var("TEST")

    bash.env_var("COMPOSER_ALLOW_SUPERUSER", "1")
    # Use --no-scripts to avoid npm ci (lock file often out of sync in oro repo)
    bash.composer_install(no_scripts=True, working_dir="/var/www/html/oro")
    # Run npm install to sync assets (npm ci fails when lock file mismatches)
    if bash.exists("/var/www/html/oro/package.json"):
        bash.npm_install(prefix="/var/www/html/oro")
    # Find and run npm install in package subdirs (oro bundles with assets)
    for pkg in bash.find("/var/www/html/oro", "package.json") or []:
        pkg_dir = os.path.dirname(pkg)
        if pkg_dir != "/var/www/html/oro":
            bash.npm_install(prefix=pkg_dir)
    bash.pwd()

    # Set the database URL in the .env-app file becouse ENV doesn't work ... 
    bash.cmd("sed -i '/^ORO_DB_URL=/d' /var/www/html/oro/.env-app")
    ORO_DB_URL="postgres://postgres:postgres@127.0.0.1:5432/oro?sslmode=disable&charset=utf8&serverVersion=13.7"
    bash.replace_in_file("/var/www/html/oro/.env-app", "ORO_DB_DSN=", f"ORO_DB_DSN={ORO_DB_URL}")
    bash.cmd("ln -s /var/www/html/oro/bin/console /usr/local/bin/symfony")
    bash.cmd("chmod 755 /usr/local/bin/symfony")
    bash.cmd("chmod +x /var/www/html/oro/bin/console")
    bash.cmd("ls -la /var/www/html/oro/")
    #bash.cmd("composer clear-cache")
    bash.service_start("postgresql")

    bash.echo("PreInstall Check OroCommerce...")
    bash.cmd("php bin/console oro:check-requirements")  
    ##bash.cmd("php bin/console oro:environment:info")
    bash.cmd("php bin/console doctrine:schema:validate --skip-sync")
    
    bash.echo("Installing OroCommerce...")
 
    print("Installation completed start all services...")
    bash.service_start("nginx")
    bash.service_start("php8.3-fpm")
    bash.service_start("redis-server") 
    bash.service_start("postgresql")
    bash.cd("/var/www/html/oro/")
    # OFFICIAL DOCKER://github.com/oroinc/docker-demo/blob/master/compose.yaml#L121C342-L121C380
    bash.cmd(f"php bin/console oro:install --no-interaction --env=prod --user-name={admin_user} --user-email={admin_email} --user-firstname={admin_firstname} --user-lastname={admin_lastname} --user-password={admin_password} --timeout=2000")
    bash.cmd("php bin/console oro:migration:data:load --fixtures-type=demo --env=prod")
    # Assets: symlinks then build. NODE_OPTIONS increases Node heap for Docker; --npm-install ensures vendor/oro/platform/build has deps
    bash.cmd("php bin/console assets:install --symlink")
    bash.env_var("NODE_OPTIONS", "--max-old-space-size=4096")
    if not bash.run_ok("php bin/console oro:assets:build --env=prod --npm-install", show_output=False):
        bash.echo("Assets build failed, continuing with symlinks only", color="yellow")
    bash.cmd("chmod -R 777 /var/www/html/oro/var")
    bash.cmd("php bin/console cache:clear --env=prod")
    bash.pwd()
    bash.cmd("php bin/console oro:search:reindex")
    bash.cmd("composer set-parameters redis")
    #bash.cmd("rm -rf /var/www/html/oro/var/cache/*")
    #bash.cmd("rm -rf /var/www/html/oro/var/sessions/*")
    #bash.cmd("rm -rf /var/www/html/oro/var/log/*")

    bash.echo("Installation completed")
    bash.cmd("sudo chmod -R 755 /var/www/html/oro/var")

    bash.cmd("php /var/www/html/oro/bin/console oro:message-queue:consume --memory-limit=256M")



def install_packages(packages):
    """Install required packages."""
    # Use Basher's detect_package_manager method
    package_manager = bash.detect_package_manager()
    bash.cmd(f"apt update && apt install sudo -y")
    bash.install(['sudo'])
    bash.install(packages)
    bash.echo(f"Packages installed successfully: {', '.join(packages)}")
    install_supervisord_for_orocommerce(php_version="8.3")

def install_supervisord_for_orocommerce(php_version="8.3"):
    """Install and configure Supervisor."""
    bash.cmd("chmod -R 755 /var/log/")
    if not bash.command_exists("supervisord"):
        bash.cmd("pip3 install supervisor --break-system-packages")
    if bash.command_exists("supervisorctl"):
        bash.run_ok("supervisorctl shutdown")
    bash.cmd("sleep 1")
    bash.cmd("service --status-all")
    php_log = f"/var/log/php{php_version}-fpm.log"
    if bash.exists(php_log):
        bash.cmd(f"chown www-data:www-data {php_log}")
    bash.cmd("rm -rf /etc/supervisord.conf")
    bash.cmd("echo_supervisord_conf > /etc/supervisord.conf")
    bash.rm("/etc/test.conf")
    bash.cmd("touch /etc/test.conf")
    bash.write_to_file("/etc/test.conf", "user=www-data", 'a')

    nginx_conf = """
[program:nginx]
command=/usr/sbin/nginx -g "daemon off;"
autostart=true
autorestart=true
stderr_logfile=/var/log/nginx-supervisor_error.log
stdout_logfile=/var/log/ngin-supervisor_output.log
    """
    bash.write_to_file("/etc/supervisord.conf", nginx_conf, 'a')

    php_fpm_conf = f"""
[program:php-fpm]
command=/usr/sbin/php-fpm{php_version} --nodaemonize 
autostart=true
autorestart=true
stderr_logfile=/var/log/php-fpm-supervisor_error.log
stdout_logfile=/var/log/php-fpm-supervisor_output.log
user=www-data
    """
    bash.write_to_file("/etc/supervisord.conf", php_fpm_conf, 'a')
    
    redis_conf = """
[program:redis-server]
command=/usr/bin/redis-server  /etc/redis/redis.conf --daemonize no
autostart=true
autorestart=true
stderr_logfile=/var/log/redis-supervisor_error.log
stdout_logfile=/var/log/redis-supervisor_output.log
    """
    bash.write_to_file("/etc/supervisord.conf", redis_conf, 'a')

    # Only add elasticsearch if user exists (not installed in basic Oro flow)
    if bash.user_exists("elasticsearch"):
        elasticsearch_conf = """
[program:elasticsearch]
command=/usr/share/elasticsearch/bin/elasticsearch
user=elasticsearch
autostart=true
autorestart=true
stderr_logfile=/var/log/elasticsearch-supervisor_error.log
stdout_logfile=/var/log/elasticsearch-supervisor_output.log
    """
        bash.write_to_file("/etc/supervisord.conf", elasticsearch_conf, 'a')

    postgres_conf = """
[program:postgres]
#command=/usr/lib/postgresql/14/bin/postgres -D /var/lib/postgresql/14/main
command=service postgresql start
autostart=true
autorestart=false
stderr_logfile=/var/log/postgres-supervisor_error.log
stdout_logfile=/var/log/postgres-supervisor_output.log
    """
    ## You will have error when status but it is ok. I don't find how to run postgres in foreground.
    # postgres                         FATAL     Exited too quickly (process log may have details)
    bash.write_to_file("/etc/supervisord.conf", postgres_conf, 'a')

    # Only add mysql if user exists (not installed in basic Oro flow)
    if bash.user_exists("mysql"):
        mysql_conf = """
[program:mysql]
command=/usr/sbin/mysqld
user=mysql
autostart=true
autorestart=false
stderr_logfile=/var/log/mysql-supervisor_error.log
stdout_logfile=/var/log/mysql-supervisor_output.log
    """
        bash.write_to_file("/etc/supervisord.conf", mysql_conf, 'a')

    bash.cmd("supervisord -c /etc/supervisord.conf")
    bash.cmd("supervisorctl status")

def install_redis():
    """Install and configure Redis."""
    bash.echo("Installing Redis...")
    bash.install(["redis-server"])
    bash.service_start("redis-server")
    # Test Redis connection
    bash.cmd("redis-cli ping")
    
    bash.echo("Redis installed and configured successfully", color="green")

def install_mysql():
    """Install and configure MySQL."""
    #Setup MySQL
    bash.install(["mysql-server"])
    bash.cmd("service mysql start")
    bash.cmd("mysql -e \"CREATE DATABASE magento; CREATE USER 'magento'@'localhost' IDENTIFIED BY 'magento'; GRANT ALL ON magento.* TO 'magento'@'localhost'; FLUSH PRIVILEGES;\"")
    bash.cmd("mysql -e \"show databases\"")
    bash.cmd("mysql -e \"SET GLOBAL log_bin_trust_function_creators = 1;\"")
    bash.cmd("mysql -e \"select version()\"")


def install_elsticsearch():
    """Install and configure Elasticsearch."""
    bash.cmd("pkill -u elasticsearch")
    bash.rm("/var/lib/elasticsearch")
    bash.rm("/etc/elasticsearch/")
    bash.cmd("wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -")
    if not bash.string_exists_in_file('/etc/apt/sources.list.d/elastic-7.x.list', "deb https://artifacts.elastic.co/packages/7.x/apt stable main"):
        bash.cmd("echo \"deb https://artifacts.elastic.co/packages/7.x/apt stable main\" | sudo tee -a /etc/apt/sources.list.d/elastic-7.x.list")
    bash.cmd("apt update")
    print(f"{bash.MAGENTA}Install Elasticsearch Version takes time please wait...{bash.RESET}")
    bash.cmd("rm -rf  /var/lib/dpkg/info/elasticsearch.*")
    bash.purge("elasticsearch")
    bash.install("elasticsearch", check_installed=False)
    bash.env_var("ES_JAVA_OPTS", "-Xms1g -Xmx1g")

    elastic_config = """
xpack.security.enabled: false
# Set the node name (optional, but useful for identification)
node.name: "node-1"

# Set the network host to bind to all interfaces or a specific IP
network.host: 0.0.0.0

# Set the HTTP port (default is 9200)
http.port: 9200

# Configure the node to be a single-node cluster
cluster.name: "my-single-node-cluster"
discovery.type: single-node
"""

    if not bash.string_exists_in_file("/etc/elasticsearch/elasticsearch.yml", "xpack.security.enabled: false"):
        bash.write_to_file("/etc/elasticsearch/elasticsearch.yml", elastic_config, 'a')
    if not bash.string_exists_in_file("/etc/elasticsearch/jvm.options", "-Xms2g"):
        bash.write_to_file("/etc/elasticsearch/jvm.options", "-Xms2g", 'a')
        bash.write_to_file("/etc/elasticsearch/jvm.options", "-Xmx2g", 'a')
    # sudo -u elasticsearch /usr/share/elasticsearch/bin/elasticsearch > /dev/null 2>&1 &
    #bash.cmd("sudo -u elasticsearch /usr/share/elasticsearch/bin/elasticsearch > /var/log/#elasticsearch/elasticsearch.log 2>&1 &")
    bash.cmd("service elasticsearch start")
    bash.cmd("sleep 20")
    test_elasticsearch = bash.cmd("curl -X GET \"localhost:9200\"", show_output=True, capture_output=True)
    if test_elasticsearch != 0:
        bash.echo("Elasticsearch installation failed")
        bash.tail("/var/log/elasticsearch/elasticsearch.log")
        exit(1)

    
def install_opensearch():
    """Install and configure OpenSearch."""
    #Setup OpenSearch
    bash.env_var("OPENSEARCH_VERSION", "2.11.0")
    bash.cmd('printenv')
    bash.cmd("curl -o- https://artifacts.opensearch.org/publickeys/opensearch.pgp | sudo gpg --dearmor --batch --yes -o /usr/share/keyrings/opensearch-keyring")
    bash.cmd("echo \"deb [signed-by=/usr/share/keyrings/opensearch-keyring] https://artifacts.opensearch.org/releases/bundle/opensearch/2.x/apt stable main\" | sudo tee /etc/apt/sources.list.d/opensearch-2.x.list")
    bash.cmd("apt update")
    bash.cmd("apt list -a opensearch")
    bash.echo("Install OpenSearch Version $OPENSEARCH_VERSION")
    print(f"{bash.MAGENTA}Install OpenSearch Version takes time please wait...{bash.RESET}")
    bash.install("opensearch=$OPENSEARCH_VERSION")
    bash.rm("/var/lib/dpkg/info/opensearch.postinst")
    # apt purge opensearch -y 
    bash.write_to_file("/etc/opensearch/opensearch.yml", "plugins.security.disabled: true", 'a')
    bash.write_to_file("/etc/opensearch/jvm.options", "-Xms1g", 'a')
    bash.write_to_file("/etc/opensearch/jvm.options", "-Xmx1g", 'a')
    bash.remove("rm /var/lib/dpkg/info/opensearch.postinst")
    bash.cmd("/usr/share/opensearch/bin/opensearch > /dev/null 2>&1 &", user="opensearch")
    bash.cmd("sleep 20")

    # logs : cat  /etc/opensearch/opensearch.yml
    bash.cmd("curl -X GET localhost:9200")



def check_services():
    """Verify all services are running after installation."""
    bash.echo("Checking services status...")
    bash.cmd("supervisorctl status", show_output=True)
    checks = [
        ("Redis", "redis-cli ping"),
        ("Nginx", "curl -s -o /dev/null -w '%{http_code}' http://localhost/"),
        ("PostgreSQL", "pg_isready -U postgres"),
    ]
    for name, cmd in checks:
        if bash.run_ok(cmd, show_output=False):
            bash.echo(f"  {name}: OK", color="green")
        else:
            bash.echo(f"  {name}: FAILED", color="red")
    bash.echo("Services check completed.")


def run_full_installation():
    """Run the full installation process."""
    bash.echo("Starting full installation...")
    
    # Install packages
    install_packages(packages)
    
    # Configure PHP
    install_php(php_ini_path)

    # Configure REDIS
    install_redis()
    
    # Configure Nginx
    install_nginx(nginx_conf_path)
    
    # Setup PostgreSQL
    setup_postgresql(db_name, db_user, db_password)
    
    # Clone and setup OroCommerce
    clone_and_setup_orocommerce(
        repo_url, branch, install_dir, admin_user, admin_email, 
        admin_firstname, admin_lastname, admin_password
    )
    
    bash.echo("Full installation completed successfully!")
    check_services()

def initialize_curses():
    """Initialize curses."""
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.noecho()
    curses.cbreak()
    curses.curs_set(0)
    return curses

def interactive_menu(stdscr):
    """Interactive menu for installation."""
    # Initialize the screen
    stdscr.clear()
    stdscr.bkgd(' ', curses.color_pair(2))
    stdscr.refresh()
    
    # Define color pairs
    curses.start_color()
    curses.use_default_colors()  # Use terminal's default colors
    # Force black background by explicitly setting it
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)    # Selected item
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)   # Normal item
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Title
    curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)   # Completed item
    
    # Set the entire screen to black background with white text
    stdscr.bkgd(' ', curses.color_pair(2))
    
    # Menu items
    menu_items = [
        "1. Install Packages",
        "2. Install PHP",
        "3. Install Nginx",
        "4. Install PostgreSQL",
        "5. Install Redis",
        "6. Install Elasticsearch",
        "7. Setup OroCommerce",
        "8. Run Full Installation",
        "9. Exit"
    ]
    
    # Track visited menu items
    visited_items = [False] * len(menu_items)
    
    # Get screen dimensions
    max_y, max_x = stdscr.getmaxyx()
    
    # Calculate menu position
    menu_y = max(0, (max_y - len(menu_items)) // 2)
    menu_x = max(0, (max_x - max(len(item) for item in menu_items)) // 2)
    
    # Current selected item
    current_item = 0
    
    # Display the menu
    while True:
        stdscr.clear()
        stdscr.bkgd(' ', curses.color_pair(2))  # Reapply background on each refresh
        
        # Draw ASCII art (raw strings to preserve backslashes)
        ascii_art = [
            r"  ___   ____    ___    ____                                                    ",
            r" / _ \ |  _ \  / _ \  / ___| ___   _ __ ___   _ __ ___    ___  _ __  ___  ___  ",
            r"| | | || |_) || | | || |    / _ \ | '_ ` _ \ | '_ ` _ \  / _ \| '__|/ __|/ _ \\",
            r"| |_| ||  _ < | |_| || |___| (_) || | | | | || | | | | ||  __/| |  | (__|  __/",
            r" \___/ |_| \_\_\___/  \____|\___/_|_| |_| |_||_| |_| |_| \___||_|   \___|\___/",
            r" / __| / _ \| '__|\ \ / // _ \| '__|                                            ",
            r" \__ \|  __/| |    \ V /|  __/| |                                               ",
            r" |___/ \___||_|     \_/  \___||_|   v6.0                                         ",
        ]

        # Calculate ASCII art position
        art_y = max(0, menu_y - len(ascii_art) - 3)  # Position above the title
        for i, line in enumerate(ascii_art):
            art_x = max(0, (max_x - len(line)) // 2)
            stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
            stdscr.addstr(art_y + i, art_x, line)
            stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)
        
        # Draw title
        title = "OroCommerce Installation Menu"
        title_x = max(0, (max_x - len(title)) // 2)
        stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
        stdscr.addstr(menu_y - 2, title_x, title)
        stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)
        
        # Draw instructions
        instructions = "Use arrow keys (↑/↓) or numbers (1-8) to navigate, Enter to select, 'q' to quit"
        instr_x = max(0, (max_x - len(instructions)) // 2)
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(max_y - 2, instr_x, instructions)
        stdscr.attroff(curses.color_pair(2))
        
        # Draw menu items
        for i, item in enumerate(menu_items):
            # Add checkmark for visited items
            display_item = f"[{'✓' if visited_items[i] else ' '}] {item}"
            
            if i == current_item:
                stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
                stdscr.addstr(menu_y + i, menu_x, display_item)
                stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)
            elif visited_items[i]:
                stdscr.attron(curses.color_pair(4))  # Green for completed items
                stdscr.addstr(menu_y + i, menu_x, display_item)
                stdscr.attroff(curses.color_pair(4))
            else:
                stdscr.attron(curses.color_pair(2))
                stdscr.addstr(menu_y + i, menu_x, display_item)
                stdscr.attroff(curses.color_pair(2))
        
        # Refresh the screen
        stdscr.refresh()
        
        if inputs:
            key = int(inputs)
        else:
            # Get user input
            key = stdscr.getch()
        
        # Handle navigation
        if key == curses.KEY_UP and current_item > 0:
            current_item -= 1
        elif key == curses.KEY_DOWN and current_item < len(menu_items) - 1:
            current_item += 1
        elif key == curses.KEY_ENTER or key in [10, 13]:  # Enter key
            # If the user pressed Enter (selection)
            if current_item == 8:  # Exit
                return
            
            # Mark the item as visited
            visited_items[current_item] = True
            
            # Exit curses mode temporarily to run the selected action
            curses.endwin()
            
            if current_item == 0:  # Install Packages
                install_packages(packages)
            elif current_item == 1:  # Configure PHP
                install_php(php_ini_path)
            elif current_item == 2:  # Configure Nginx
                install_nginx(nginx_conf_path)
            elif current_item == 3:  # Setup PostgreSQL
                setup_postgresql(db_name, db_user, db_password)
            elif current_item == 4:  # Setup Redis
                install_redis()
            elif current_item == 5:  # Install OpenSearch
                install_elsticsearch()
            elif current_item == 6:  # Clone and Setup OroCommerce
                clone_and_setup_orocommerce(
                    repo_url, branch, install_dir, admin_user, admin_email, 
                    admin_firstname, admin_lastname, admin_password
                )
            elif current_item == 7:  # Run Full Installation
                run_full_installation()
                # Mark all items as visited when running full installation
                visited_items = [True] * (len(menu_items) - 1) + [False]  # All except Exit
            elif current_item == 8:
                return

            if not inputs and not no_interaction:    
                # Wait for user to press a key before returning to the menu
                input("\nPress Enter to return to the menu...")
            else:
                #curses.endwin()
                exit()
            
            # Reinitialize curses
            stdscr = curses.initscr()
            stdscr.keypad(True)

            initialize_curses()
        
        elif key == ord('q') or key == ord('Q'):
            return
        elif key >= ord('1') and key <= ord('9'):
            # Direct selection using number keys
            current_item = key - ord('1')
        #if -i arguments are passed
        elif inputs:
            current_item = key - 1
            
            # If the user pressed Enter (selection)
            if current_item == 8:  # Exit
                return
            
            # Mark the item as visited
            visited_items[current_item] = True
            
            # Exit curses mode temporarily to run the selected action
            curses.endwin()
            
            if current_item == 0:  # Install Packages
                install_packages(packages)
            elif current_item == 1:  # Configure PHP
                install_php(php_ini_path)
            elif current_item == 2:  # Configure Nginx
                install_nginx(nginx_conf_path)
            elif current_item == 3:  # Setup PostgreSQL
                setup_postgresql(db_name, db_user, db_password)
            elif current_item == 4:  # Setup Redis
                install_redis()
            elif current_item == 5:  # Install OpenSearch
                install_elsticsearch()
            elif current_item == 6:  # Clone and Setup OroCommerce
                clone_and_setup_orocommerce(
                    repo_url, branch, install_dir, admin_user, admin_email, 
                    admin_firstname, admin_lastname, admin_password
                )
            elif current_item == 7:  # Run Full Installation
                run_full_installation()
                # Mark all items as visited when running full installation
                visited_items = [True] * (len(menu_items) - 1) + [False]  # All except Exit
            
            if not inputs and not no_interaction:
                # Wait for user to press a key before returning to the menu
                input("\nPress Enter to return to the menu...")
            else:
                #curses.endwin()
                exit()
            
            # Reinitialize curses
            stdscr = curses.initscr()
            stdscr.keypad(True)
            initialize_curses()

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="OroCommerce Installation Script")
    
    # Add verbosity options
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help="Increase verbosity level (use -v, -vv, or -vvv for different levels)")
     # Add no options
    parser.add_argument('-n', '--no-inp', action='store_true',
                        help="Run in non-interactive mode with default values")
    
    parser.add_argument('-i', '--inputs', action='store',
                        help="Input")
    
    # Add no-interaction option
    parser.add_argument('--no-interaction', action='store_true',
                        help="Run in non-interactive mode with default values")
    
    return parser.parse_args()

def main():
    """Main function."""
    # Parse command-line arguments
    args = parse_args()
    
    # Define global variables
    global php_ini_path, nginx_conf_path, db_name, db_user, db_password
    global repo_url, branch, install_dir, admin_user, admin_email, admin_firstname, admin_lastname, admin_password
    global packages, bash, inputs, no_interaction

    inputs = args.inputs

    # Initialize Basher with verbosity level from command-line arguments
    bash = Basher()
    bash.set_raise_exception(True)  # Stop on first command failure

    # Set verbosity level based on command-line arguments
    # -v = 1, -vv = 2, -vvv = 3
    verbosity_level = min(args.verbose, 3)  # Cap at level 3
    bash.set_verbosity(verbosity_level)

    no_inp = args.no_inp
    
    if verbosity_level > 0:
        print(f"Verbosity level set to {verbosity_level}")

    # Use default values for non-interactive mode
    php_ini_path = "/etc/php/8.2/fpm/php.ini"
    nginx_conf_path = "/etc/nginx/conf.d/default.conf"
    db_name = "oro"
    db_user = "postgres"
    db_password = "postgres"
    repo_url = "https://github.com/oroinc/orocommerce-application.git"
    branch = "6.0"
    install_dir = "/var/www/html/oro"
    admin_user = "admin"
    admin_email = "admin@example.com"
    admin_firstname = "Admin"
    admin_lastname = "Adminenko"
    admin_password = "admin123"
    packages = ["curl", "nano", "wget", "htop", "net-tools", "git", "rsync", "python3", "python3-pip"]

    if args.no_interaction:
        no_interaction = True
        run_full_installation()
    else:
        if not no_inp:
            # Interactive mode
            # php_ini_path = get_input("Enter PHP INI path", php_ini_path)
            # nginx_conf_path = get_input("Enter Nginx config path", nginx_conf_path)
            db_name = get_input("Enter database name", db_name)
            db_user = get_input("Enter database user", db_user)
            db_password = get_input("Enter database password", db_password)
            repo_url = get_input("Enter repository URL", repo_url)
            branch = get_input("Enter branch name", branch)
            install_dir = get_input("Enter installation directory", install_dir)
            admin_user = get_input("Enter admin username", admin_user)
            admin_email = get_input("Enter admin email", admin_email)
            admin_firstname = get_input("Enter admin first name", admin_firstname)
            admin_lastname = get_input("Enter admin last name", admin_lastname)
            admin_password = get_input("Enter admin password", admin_password)
            packages = get_input("Enter packages to install", packages)                     
        
        curses.wrapper(interactive_menu)


if __name__ == "__main__":
    main() 