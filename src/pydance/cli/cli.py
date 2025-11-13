#!/usr/bin/env python3
"""
Pydance CLI - Command Line Interface for Pydance Framework

Provides access to management commands and framework utilities.
"""

import os
import sys
from pathlib import Path


class PydanceCLI:
    """Command Line Interface for Pydance Framework"""

    def __init__(self):
        self.prog_name = Path(sys.argv[0]).name

    def run(self) -> int:
        """
        Run the CLI.

        If we're in a project directory (has manage.py), delegate to management commands.
        Otherwise, show framework-level help.
        """
        # Check if we're in a project directory
        if self._is_project_directory():
            return self._run_management_commands()

        # Framework-level CLI
        return self._run_framework_cli()

    def _is_project_directory(self) -> bool:
        """Check if current directory is a Pydance project."""
        cwd = Path.cwd()
        indicators = [
            cwd / 'manage.py',
            cwd / 'app.py',
            cwd / 'config' / 'settings.py',
        ]
        return any(indicator.exists() for indicator in indicators)

    def _run_management_commands(self) -> int:
        """Run management commands for the current project."""
        try:
            from ..core.management import execute_from_command_line
            execute_from_command_line()
            return 0
        except Exception as e:
            print(f"❌ Error running management commands: {e}")
            return 1

    def _run_framework_cli(self) -> int:
        """Run framework-level CLI commands."""
        if len(sys.argv) < 2:
            self._show_framework_help()
            return 0

        command = sys.argv[1]

        if command == 'startproject':
            return self._create_project()
        elif command == 'version':
            return self._show_version()
        elif command == '--help' or command == '-h':
            self._show_framework_help()
            return 0
        else:
            print(f"Unknown command: {command}")
            self._show_framework_help()
            return 1

    def _create_project(self) -> int:
        """Create a new Pydance project."""
        if len(sys.argv) < 3:
            print("❌ Project name required")
            print("Usage: pydance startproject <project_name>")
            return 1

        project_name = sys.argv[2]

        try:
            from .commands.project import StartProjectCommand
            cmd = StartProjectCommand()
            # Parse additional arguments
            import argparse
            parser = argparse.ArgumentParser()
            cmd.add_arguments(parser)
            args = parser.parse_args(sys.argv[3:])
            args.name = project_name
            return cmd.handle(args)
        except Exception as e:
            print(f"❌ Error creating project: {e}")
            return 1

    def _show_version(self) -> int:
        """Show framework version."""
        try:
            import pydance
            version = getattr(pydance, '__version__', '1.0.0')
        except (ImportError, AttributeError):
            version = '1.0.0'

        print(f"Pydance {version}")
        return 0

    def _show_framework_help(self) -> None:
        """Show framework-level help."""
        help_text = f"""
{self.prog_name} - Pydance Framework CLI

Framework Commands:
  startproject <name>    Create a new Pydance project
  version               Show framework version
  --help                Show this help

Project Commands:
  When in a project directory, use: python manage.py <command>

For more information, see: https://pydance.readthedocs.io/
"""
        print(help_text)


def main():
    """Main CLI entry point"""
    cli = PydanceCLI()
    sys.exit(cli.run())


if __name__ == '__main__':
    main()
