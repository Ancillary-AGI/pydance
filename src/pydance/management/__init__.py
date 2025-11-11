import argparse
import sys
from typing import Dict, List, Any, Optional

from pydance.db.migrations.migrator import MigrationManager


class ManagementCommand:
    """Base class for management commands."""

    help = "No help available"

    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.add_arguments()

    def add_arguments(self):
        """Add command arguments."""
        pass

    def handle(self, *args, **options):
        """Handle command execution."""
        raise NotImplementedError("Subclasses must implement handle() method")


class MigrateCommand(ManagementCommand):
    """Database migration command."""

    help = "Apply database migrations"

    def add_arguments(self):
        self.parser.add_argument(
            '--database',
            default='default',
            help='Database to migrate'
        )
        self.parser.add_argument(
            '--fake',
            action='store_true',
            help='Mark migrations as applied without running them'
        )

    def handle(self, *args, **options):
        print(f"Migrating database: {options['database']}")

        # Get migration manager
        migrator = MigrationManager()

        if options['fake']:
            print("Running in fake mode - marking migrations as applied")
            # Fake migration logic would go here
        else:
            print("Applying migrations...")
            # Real migration logic would go here


class CreateMigrationCommand(ManagementCommand):
    """Create new migration command."""

    help = "Create a new database migration"

    def add_arguments(self):
        self.parser.add_argument(
            'name',
            help='Name of the migration'
        )
        self.parser.add_argument(
            '--empty',
            action='store_true',
            help='Create an empty migration'
        )

    def handle(self, *args, **options):
        migration_name = options['name']
        print(f"Creating migration: {migration_name}")

        # Migration creation logic would go here
        print(f"Created migration: {migration_name}")


class CommandRegistry:
    """Registry for management commands."""

    def __init__(self):
        self.commands: Dict[str, type] = {}
        self._load_default_commands()

    def _load_default_commands(self):
        """Load default commands."""
        self.commands.update({
            'migrate': MigrateCommand,
            'makemigrations': CreateMigrationCommand,
        })

    def register_command(self, name: str, command_class: type):
        """Register a new command."""
        self.commands[name] = command_class

    def get_command(self, name: str) -> Optional[type]:
        """Get command by name."""
        return self.commands.get(name)

    def get_commands(self) -> Dict[str, type]:
        """Get all registered commands."""
        return self.commands.copy()


# Global command registry
command_registry = CommandRegistry()


def execute_from_command_line(argv: Optional[List[str]] = None):
    """Execute management command from command line."""
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print("No command provided")
        return

    command_name = argv[0]
    command_class = command_registry.get_command(command_name)

    if not command_class:
        print(f"Unknown command: {command_name}")
        print("Available commands:")
        for name in command_registry.get_commands():
            print(f"  {name}")
        return

    # Parse arguments
    command = command_class()
    options = command.parser.parse_args(argv[1:])

    # Execute command
    try:
        command.handle(*argv[2:], **vars(options))
    except Exception as e:
        print(f"Command failed: {e}")
        raise


def call_command(command_name: str, *args, **options):
    """Call management command programmatically."""
    command_class = command_registry.get_command(command_name)

    if not command_class:
        raise ValueError(f"Unknown command: {command_name}")

    command = command_class()
    command.handle(*args, **options)


__all__ = [
    'ManagementCommand',
    'MigrateCommand',
    'CreateMigrationCommand',
    'CommandRegistry',
    'command_registry',
    'execute_from_command_line',
    'call_command'
]
