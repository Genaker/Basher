from .core import BashCommand
from .shell_utils import quote

class SupervisorD(BashCommand):
    """
    A class that provides methods to interact with Supervisor.
    """

    def __init__(self, working_dir=None):
        """Initialize the SupervisorOps object."""
        super().__init__(working_dir)


    def init(self, config_file="/etc/supervisord.conf"):
        """Initialize Supervisor.

        :param config_file: The path to the Supervisor configuration file.
        """
        return self.cmd(f"sudo supervisord -c {quote(config_file)}")

    def start_all(self):
        """Start all programs managed by Supervisor."""
        return self.cmd("sudo supervisorctl start all")

    def stop_all(self):
        """Stop all programs managed by Supervisor."""
        return self.cmd("sudo supervisorctl stop all")

    def restart_all(self):
        """Restart all programs managed by Supervisor."""
        return self.cmd("sudo supervisorctl restart all")

    def status(self):
        """Get the status of all programs managed by Supervisor."""
        return self.cmd("sudo supervisorctl status")

    def start_program(self, program_name):
        """Start a specific program managed by Supervisor."""
        return self.cmd(f"sudo supervisorctl start {quote(program_name)}")

    def stop_program(self, program_name):
        """Stop a specific program managed by Supervisor."""
        return self.cmd(f"sudo supervisorctl stop {quote(program_name)}")

    def restart_program(self, program_name):
        """Restart a specific program managed by Supervisor."""
        return self.cmd(f"sudo supervisorctl restart {quote(program_name)}")

    def reread(self):
        """Reread Supervisor configuration files."""
        return self.cmd("sudo supervisorctl reread")

    def update(self):
        """Update Supervisor with the latest configuration."""
        return self.cmd("sudo supervisorctl update")