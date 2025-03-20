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
from basher import Basher
import argparse

def get_input(prompt, default):
    """Get user input with a default value."""
    response = input(f"{prompt} [{default}]: ")
    return response if response else default


def install_php(php_ini_path):

    bash.echo("install PHP...")

    bash.install("software-properties-common ");
    bash.cmd("add-apt-repository -y ppa:ondrej/php");
    bash.cmd("apt update");
    bash.rm("/etc/php/8.3/cli/php.ini");
    bash.rm("/etc/php/8.3/fpm/php.ini");
    bash.install("php8.3 php8.3-fpm php8.3-cli php8.3-pdo php8.3-mysqlnd php8.3-redis php8.3-xml php8.3-soap php8.3-gd php8.3-zip php8.3-intl php8.3-mbstring php8.3-opcache php8.3-curl php8.3-bcmath php8.3-ldap php8.3-pgsql php8.3-dev php8.3-mongodb");
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
    php_ini_fpm_path =  "/etc/php/8.3/fpm/php.ini"
    php_ini_cli_path = "/etc/php/8.3/cli/php.ini"
    bash.write_to_file(php_ini_fpm_path, php_settings, 'a')
    php_settings_cli = "memory_limit = 2048M"
    bash.write_to_file(php_ini_cli_path, php_settings_cli, 'a')

    bash.cmd("php -r \"copy('https://getcomposer.org/installer', 'composer-setup.php');\"")
    bash.cmd("php composer-setup.php")
    bash.cmd("php -r \"unlink('composer-setup.php');\"")
    bash.cmd("mv composer.phar /usr/bin/composer")
    bash.cmd("apt-get clean")

    bash.echo(f"PHP configured successfully in {php_ini_path}")
    
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
    bash.write_to_file(php_ini_path, settings, 'a')
    bash.cmd("php -v", show_output=True)
    print("Test Error output with the wrong command")
    bash.cmd("php9 -v", show_output=True)
    bash.echo(f"PHP configured successfully in {php_ini_path}")


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

    location ~* ^[^(\.php)]+\\.(jpg|jpeg|gif|png|ico|css|pdf|ppt|txt|bmp|rtf|js)$ {
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
    bash.cmd("sudo service postgresql start")
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

    bash.cmd("composer install")
    bash.pwd();
    bash.env_var("COMPOSER_ALLOW_SUPERUSER", "1")

    # Set the database URL in the .env-app file becouse ENV doesn't work ... 
    bash.cmd("sed -i '/^ORO_DB_URL=/d' /var/www/html/oro/.env-app")
    ORO_DB_URL="postgres://postgres:postgres@127.0.0.1:5432/oro?sslmode=disable&charset=utf8&serverVersion=13.7"
    bash.replace_in_file("/var/www/html/oro/.env-app", "ORO_DB_DSN=", f"ORO_DB_DSN={ORO_DB_URL}")
    bash.cmd("ln -s /var/www/html/oro/bin/console /usr/local/bin/symfony")
    bash.cmd("chmod 755 /usr/local/bin/symfony")
    bash.cmd("chmod +x /var/www/html/oro/bin/console")
    bash.cmd("ls -la /var/www/html/oro/")
    #bash.cmd("composer clear-cache")
    bash.cmd("service postgresql start")

    bash.echo("PreInstall Check OroCommerce...")
    bash.cmd("php bin/console oro:check-requirements")  
    ##bash.cmd("php bin/console oro:environment:info")
    bash.cmd("php bin/console doctrine:schema:validate --skip-sync")
    
    bash.echo("Installing OroCommerce...")
 
    print("Installation completed start all services...")
    bash.cmd("service nginx start")
    bash.cmd("service php8.3-fpm start")
    bash.cmd("service redis-server start") 
    bash.cmd("service postgresql start")
    bash.cd("/var/www/html/oro/")
    # OFFICIAL DOCKER://github.com/oroinc/docker-demo/blob/master/compose.yaml#L121C342-L121C380
    bash.cmd(f"php bin/console oro:install --no-interaction --env=prod --user-name={admin_user} --user-email={admin_email} --user-firstname={admin_firstname} --user-lastname={admin_lastname} --user-password={admin_password} --timeout=2000")
    bash.cmd("php bin/console oro:migration:data:load --fixtures-type=demo --env=prod")
    bash.cmd("php bin/console oro:assets:install --symlink")
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


def install_redis():
    """Install and configure Redis."""
    bash.echo("Installing Redis...")
    bash.install(["redis-server"])
    bash.cmd("service redis-server start")
    # Test Redis connection
    bash.cmd("redis-cli ping")
    
    bash.echo("Redis installed and configured successfully", color="green")


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
        "5. Setup Redis",
        "6. Setup OroCommerce",
        "7. Run Full Installation",
        "8. Exit"
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
        
        # Draw ASCII art
        ascii_art = [
            "   ____  _____   ____   ____                                           ",
            "  / __ \\|  __ \\ / __ \\ / ____| v6.0                                   ",
            " | |  | | |__) | |  | | |     ___  _ __ ___  _ __ ___   ___ _ __ ___ ",
            " | |  | |  _  /| |  | | |    / _ \\| '_ ` _ \\| '_ ` _ \\ / _ \\ '__/ __|",
            " | |__| | | \\ \\| |__| | |___| (_) | | | | | | | | | |  __/ |  \\__ \\",
            "  \\____/|_|  \\_\\\\____/ \\_____\\___/|_| |_| |_|_| |_| |_|\\___|_|  |___/"
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
        
        # Get user input
        key = stdscr.getch()
        
        # Handle navigation
        if key == curses.KEY_UP and current_item > 0:
            current_item -= 1
        elif key == curses.KEY_DOWN and current_item < len(menu_items) - 1:
            current_item += 1
        elif key == curses.KEY_ENTER or key in [10, 13]:  # Enter key
            # If the user pressed Enter (selection)
            if current_item == 7:  # Exit
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
            elif current_item == 5:  # Clone and Setup OroCommerce
                clone_and_setup_orocommerce(
                    repo_url, branch, install_dir, admin_user, admin_email, 
                    admin_firstname, admin_lastname, admin_password
                )
            elif current_item == 6:  # Run Full Installation
                run_full_installation()
                # Mark all items as visited when running full installation
                visited_items = [True] * (len(menu_items) - 1) + [False]  # All except Exit
            
            # Wait for user to press a key before returning to the menu
            input("\nPress Enter to return to the menu...")
            
            # Reinitialize curses
            stdscr = curses.initscr()
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
            curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
            curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.noecho()
            curses.cbreak()
            stdscr.keypad(True)
            curses.curs_set(0)
            
        elif key == ord('q') or key == ord('Q'):
            return
        elif key >= ord('1') and key <= ord('8'):
            # Direct selection using number keys
            current_item = key - ord('1')
            
            # If the user pressed Enter (selection)
            if current_item == 7:  # Exit
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
            elif current_item == 5:  # Clone and Setup OroCommerce
                clone_and_setup_orocommerce(
                    repo_url, branch, install_dir, admin_user, admin_email, 
                    admin_firstname, admin_lastname, admin_password
                )
            elif current_item == 6:  # Run Full Installation
                run_full_installation()
                # Mark all items as visited when running full installation
                visited_items = [True] * (len(menu_items) - 1) + [False]  # All except Exit
            
            # Wait for user to press a key before returning to the menu
            input("\nPress Enter to return to the menu...")
            
            # Reinitialize curses
            stdscr = curses.initscr()
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
            curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
            curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.noecho()
            curses.cbreak()
            stdscr.keypad(True)
            curses.curs_set(0)

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="OroCommerce Installation Script")
    
    # Add verbosity options
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help="Increase verbosity level (use -v, -vv, or -vvv for different levels)")
    
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
    global packages, bash

    # Initialize Basher with verbosity level from command-line arguments
    bash = Basher()
    
    # Set verbosity level based on command-line arguments
    # -v = 1, -vv = 2, -vvv = 3
    verbosity_level = min(args.verbose, 3)  # Cap at level 3
    bash.set_verbosity(verbosity_level)
    
    if verbosity_level > 0:
        print(f"Verbosity level set to {verbosity_level}")

    # Use default values for non-interactive mode
    php_ini_path = "/etc/php/8.3/fpm/php.ini"
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
        run_full_installation()
    else:
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