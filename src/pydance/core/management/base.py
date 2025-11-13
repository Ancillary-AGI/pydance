"""
Base classes for Pydance management commands.

This module provides the foundation for creating management commands,
similar to Django's management command system.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Type
import importlib
import inspect


class BaseCommand:
    """
    Base class for all management commands.

    Management commands should inherit from this class and implement
    the required methods.
    """

    help = ''  # Help text for the command

    def __init__(self):
        self.stdout = sys.stdout
        self.stderr = sys.stderr

    def create_parser(self, prog_name: str, subcommand: str) -> argparse.ArgumentParser:
        """
        Create and return the ArgumentParser for this command.
        """
        return argparse.ArgumentParser(
            prog=f"{prog_name} {subcommand}",
            description=self.help or None,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """
        Add command-specific arguments to the parser.

        Subclasses should override this method to add their own arguments.
        """
        pass

    def get_version(self) -> str:
        """
        Return the version of the command.
        """
        return "1.0.0"

    def execute(self, *args, **options) -> None:
        """
        Execute the command.

        This method calls handle() with the parsed arguments.
        """
        # Parse arguments if not already parsed
        if args and isinstance(args[0], argparse.Namespace):
            # Already parsed
            parsed_args = args[0]
        else:
            # Need to parse
            parser = self.create_parser('manage.py', self.__class__.__name__.lower())
            self.add_arguments(parser)
            parsed_args = parser.parse_args(args)

        # Execute the command
        self.handle(parsed_args, **options)

    def handle(self, *args, **options) -> None:
        """
        The actual logic of the command.

        Subclasses must implement this method.
        """
        raise NotImplementedError("Subclasses must implement handle()")


class ManagementUtility:
    """
    Utility class for running management commands.

    This class handles command discovery, loading, and execution.
    """

    def __init__(self, argv=None):
        self.argv = argv or sys.argv[:]
        self.prog_name = Path(self.argv[0]).name

    def execute(self) -> None:
        """
        Execute the management command.
        """
        try:
            subcommand = self.argv[1]
        except IndexError:
            subcommand = 'help'

        self.fetch_command(subcommand).execute(*self.argv[2:])

    def fetch_command(self, subcommand: str) -> BaseCommand:
        """
        Fetch the command instance for the given subcommand.
        """
        commands = self.get_commands()
        try:
            command_class = commands[subcommand]
        except KeyError:
            # Command not found
            if subcommand == 'help':
                self.print_help()
                sys.exit(0)
            else:
                self.stderr.write(f"Unknown command: {subcommand}\n")
                self.print_help()
                sys.exit(1)

        # Instantiate the command
        return command_class()

    def get_commands(self) -> Dict[str, Type[BaseCommand]]:
        """
        Get all available commands.
        """
        commands = {}

        # Load built-in commands
        commands.update(self._load_builtin_commands())

        # Load custom commands from apps
        commands.update(self._load_app_commands())

        return commands

    def _load_builtin_commands(self) -> Dict[str, Type[BaseCommand]]:
        """
        Load built-in management commands.
        """
        commands = {}

        # Import built-in commands
        try:
            from . import commands as builtin_commands

            # Find all command classes
            for name, obj in inspect.getmembers(builtin_commands):
                if (inspect.isclass(obj) and
                    issubclass(obj, BaseCommand) and
                    obj != BaseCommand):
                    commands[obj.__name__.lower()] = obj

        except ImportError:
            pass

        return commands

    def _load_app_commands(self) -> Dict[str, Type[BaseCommand]]:
        """
        Load custom commands from installed apps.
        """
        commands = {}

        # Get the current Django settings or equivalent
        # For now, we'll look for commands in common locations
        search_paths = self._get_command_search_paths()

        for path in search_paths:
            commands.update(self._load_commands_from_path(path))

        return commands

    def _get_command_search_paths(self) -> List[Path]:
        """
        Get paths to search for management commands.
        """
        paths = []

        # Current working directory
        cwd = Path.cwd()

        # Common app locations
        possible_paths = [
            cwd / 'apps',  # If apps are in an apps directory
            cwd,           # If apps are in the root
        ]

        # Add any directory that contains a management/commands structure
        for base_path in possible_paths:
            if base_path.exists():
                for item in base_path.iterdir():
                    if item.is_dir():
                        mgmt_path = item / 'management' / 'commands'
                        if mgmt_path.exists() and mgmt_path.is_dir():
                            paths.append(mgmt_path)

        return paths

    def _load_commands_from_path(self, path: Path) -> Dict[str, Type[BaseCommand]]:
        """
        Load commands from a specific path.
        """
        commands = {}

        if not path.exists():
            return commands

        # Find all Python files in the commands directory
        for py_file in path.glob('*.py'):
            if py_file.name.startswith('_'):
                continue

            try:
                commands.update(self._load_command_from_file(py_file))
            except Exception as e:
                self.stderr.write(f"Error loading command from {py_file}: {e}\n")

        return commands

    def _load_command_from_file(self, file_path: Path) -> Dict[str, Type[BaseCommand]]:
        """
        Load command classes from a Python file.
        """
        commands = {}

        try:
            # Import the module
            module_name = f"management.commands.{file_path.stem}"
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                return commands

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find command classes
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and
                    issubclass(obj, BaseCommand) and
                    obj != BaseCommand):

                    # Use the file name as the command name
                    command_name = file_path.stem.lower()
                    commands[command_name] = obj

        except Exception as e:
            raise Exception(f"Failed to load command from {file_path}: {e}")

        return commands

    def call_command(self, command_name: str, *args, **options) -> Any:
        """
        Call a command programmatically.
        """
        command = self.fetch_command(command_name)
        return command.execute(*args, **options)

    def print_help(self) -> None:
        """
        Print help information.
        """
        commands = self.get_commands()

        self.stdout.write(f"{self.prog_name} - Pydance Management Commands\n\n")

        if commands:
            self.stdout.write("Available commands:\n")
            for name, command_class in sorted(commands.items()):
                help_text = getattr(command_class, 'help', '') or 'No description available'
                self.stdout.write(f"  {name:<20} {help_text}\n")
        else:
            self.stdout.write("No commands available.\n")

        self.stdout.write(f"\nUse '{self.prog_name} <command> --help' for help on a specific command.\n")
