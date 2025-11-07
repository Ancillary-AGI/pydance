"""
Pydance CLI Commands

Modular command system for the Pydance CLI.
"""

from abc import ABC, abstractmethod
from typing import List, Any, Optional
import argparse


class BaseCommand(ABC):
    """Base class for all CLI commands"""

    def __init__(self, name: str, help_text: str):
        self.name = name
        self.help_text = help_text

    @abstractmethod
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments to the parser"""
        pass

    @abstractmethod
    def handle(self, args: Any) -> int:
        """Execute the command. Return exit code (0 for success)"""
        pass

    def validate_args(self, args: Any) -> List[str]:
        """Validate command arguments. Return list of error messages."""
        return []


class CommandRegistry:
    """Registry for CLI commands"""

    def __init__(self):
        self.commands: dict[str, BaseCommand] = {}

    def register(self, command: BaseCommand) -> None:
        """Register a command"""
        self.commands[command.name] = command

    def get_command(self, name: str) -> Optional[BaseCommand]:
        """Get a command by name"""
        return self.commands.get(name)

    def list_commands(self) -> List[str]:
        """List all registered command names"""
        return list(self.commands.keys())


# Global command registry
registry = CommandRegistry()
