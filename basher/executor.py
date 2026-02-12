"""Command execution interface for Basher components."""

from typing import Protocol, Optional


class CommandExecutor(Protocol):
    """
    Protocol for command execution.
    Implemented by BashCommand; used by FileOps for cmd/error.
    """

    def cmd(self, command: str, **kwargs) -> Optional[str]:
        """Execute a shell command."""
        ...

    def error(self, message: str) -> None:
        """Display an error message."""
        ...


class FilesystemContext(Protocol):
    """
    Protocol for filesystem operations.
    Implemented by SystemOps; used by ArchiveOps for exists/folder_exists/mkdir/error.
    """

    def exists(self, path: str) -> bool:
        """Check if path exists."""
        ...

    def folder_exists(self, path: str) -> bool:
        """Check if path is an existing directory."""
        ...

    def mkdir(self, path: str, exist_ok: bool = True) -> bool:
        """Create directory."""
        ...

    def error(self, message: str) -> None:
        """Display an error message."""
        ...
