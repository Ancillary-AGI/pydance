import argparse
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional


class CLICommand:
    """Base CLI command class."""

    name = 'command'
    help = 'No help available'
    description = 'No description available'

    def __init__(self):
        self.parser = argparse.ArgumentParser(
            prog=f'pydance {self.name}',
            description=self.description
        )
        self.add_arguments()

    def add_arguments(self):
        """Add command arguments."""
        pass

    def handle(self, args: argparse.Namespace):
        """Handle command execution."""
        raise NotImplementedError("Subclasses must implement handle() method")


class StartProjectCommand(CLICommand):
    """Start new Pydance project command."""

    name = 'startproject'
    help = 'Create a new Pydance project'
    description = 'Create a new Pydance project with default structure'

    def add_arguments(self):
        self.parser.add_argument(
            'project_name',
            help='Name of the project to create'
        )
        self.parser.add_argument(
            '--template',
            default='basic',
            help='Project template to use'
        )

    def handle(self, args: argparse.Namespace):
        """Create new project."""
        project_name = args.project_name
        template = args.template

        print(f"Creating new Pydance project: {project_name}")

        # Create project directory
        project_dir = Path(project_name)
        if project_dir.exists():
            print(f"Error: Directory '{project_name}' already exists")
            return

        try:
            # Create basic project structure
            self._create_project_structure(project_dir, template)
            print(f"Successfully created project '{project_name}'")
            print(f"Run 'cd {project_name} && python manage.py runserver' to start development")

        except Exception as e:
            print(f"Error creating project: {e}")

    def _create_project_structure(self, project_dir: Path, template: str):
        """Create project directory structure."""
        # Create main directories
        directories = [
            project_dir,
            project_dir / 'src',
            project_dir / 'static',
            project_dir / 'templates',
            project_dir / 'migrations',
            project_dir / 'tests',
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

        # Create basic files
        self._create_project_files(project_dir)

    def _create_project_files(self, project_dir: Path):
        """Create basic project files."""
        # Create main application file
        main_py = project_dir / 'src' / 'main.py'
        main_py.write_text('''"""
Main application file for Pydance project.
"""

from pydance.server.application import Application
from pydance.http.response import Response
from pydance.http.request import Request

# Create application
app = Application()

@app.route('/')
async def hello_world(request: Request) -> Response:
    """Hello world endpoint."""
    return Response.html('<h1>Hello, Pydance!</h1>')

if __name__ == '__main__':
    app.run(debug=True)
''')

        # Create manage.py
        manage_py = project_dir / 'manage.py'
        manage_py.write_text('''#!/usr/bin/env python
"""
Management script for Pydance project.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == '__main__':
    from pydance.management import execute_from_command_line
    execute_from_command_line(sys.argv)
''')

        # Create requirements.txt
        requirements_txt = project_dir / 'requirements.txt'
        requirements_txt.write_text('''pydance>=0.1.0
''')

        # Create .gitignore
        gitignore = project_dir / '.gitignore'
        gitignore.write_text('''__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/
''')

        # Make manage.py executable
        os.chmod(manage_py, 0o755)


class RunServerCommand(CLICommand):
    """Run development server command."""

    name = 'runserver'
    help = 'Start development server'
    description = 'Start the Pydance development server'

    def add_arguments(self):
        self.parser.add_argument(
            '--host',
            default='127.0.0.1',
            help='Host to bind to'
        )
        self.parser.add_argument(
            '--port',
            type=int,
            default=8000,
            help='Port to bind to'
        )
        self.parser.add_argument(
            '--debug',
            action='store_true',
            help='Enable debug mode'
        )

    def handle(self, args: argparse.Namespace):
        """Start development server."""
        host = args.host
        port = args.port
        debug = args.debug

        print(f"Starting development server at http://{host}:{port}")
        if debug:
            print("Debug mode enabled")

        # This would start the actual server
        # For now, just show that the command was called
        print(f"Server would start on {host}:{port}")


class CommandRegistry:
    """Registry for CLI commands."""

    def __init__(self):
        self.commands: Dict[str, type] = {}
        self._load_default_commands()

    def _load_default_commands(self):
        """Load default commands."""
        self.register_command(StartProjectCommand)
        self.register_command(RunServerCommand)

    def register_command(self, command_class: type):
        """Register a command."""
        self.commands[command_class.name] = command_class

    def get_command(self, name: str) -> Optional[type]:
        """Get command by name."""
        return self.commands.get(name)

    def get_commands(self) -> Dict[str, type]:
        """Get all commands."""
        return self.commands.copy()


# Global command registry
command_registry = CommandRegistry()


def execute_from_command_line(argv: Optional[List[str]] = None):
    """Execute CLI command from command line."""
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print("Pydance CLI")
        print("Available commands:")
        for name, command_class in command_registry.get_commands().items():
            print(f"  {name} - {command_class.help}")
        return

    command_name = argv[0]
    command_class = command_registry.get_command(command_name)

    if not command_class:
        print(f"Unknown command: {command_name}")
        print("Available commands:")
        for name, cmd_class in command_registry.get_commands().items():
            print(f"  {name} - {cmd_class.help}")
        return

    # Parse and execute command
    command = command_class()
    args = command.parser.parse_args(argv[1:])

    try:
        command.handle(args)
    except Exception as e:
        print(f"Command failed: {e}")
        raise


def call_command(command_name: str, *args, **options):
    """Call command programmatically."""
    command_class = command_registry.get_command(command_name)

    if not command_class:
        raise ValueError(f"Unknown command: {command_name}")

    command = command_class()

    # Create namespace with options
    namespace = argparse.Namespace()
    for key, value in options.items():
        setattr(namespace, key, value)

    command.handle(namespace)


__all__ = [
    'CLICommand',
    'StartProjectCommand',
    'RunServerCommand',
    'CommandRegistry',
    'command_registry',
    'execute_from_command_line',
    'call_command'
]
