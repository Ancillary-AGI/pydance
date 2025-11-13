# Pydance Management Commands

Pydance provides a powerful command-line interface (CLI) system that allows you to create custom management commands, similar to Django's management commands.

## Overview

The Pydance CLI system consists of:

1. **Framework commands**: Commands available at the framework level (e.g., `pydance startproject`)
2. **Management commands**: Commands available within projects via `manage.py`
3. **Built-in commands**: Pre-defined commands that come with Pydance
4. **Custom commands**: User-defined commands that can be easily created and registered

## Framework Commands

Framework-level commands are available globally and don't require a project:

```bash
# Create a new project
pydance startproject myproject

# Show framework version
pydance version

# Show help
pydance --help
```

## Management Commands

Management commands are available within Pydance projects and are run using `manage.py`:

```bash
# In your project directory
python manage.py check
python manage.py version
python manage.py help
```

## Creating Custom Commands

### Project Structure

To create custom management commands in your Pydance project:

```
myproject/
├── manage.py              # Management script (created by startproject)
├── app.py                 # Your main application
├── config/
│   └── settings.py        # Project settings
├── management/            # Custom commands directory
│   └── commands/          # Command files go here
│       ├── __init__.py
│       └── mycommand.py   # Your custom command
└── requirements.txt
```

### Basic Command Structure

Create a Python file in `management/commands/` with a class that inherits from `BaseCommand`:

```python
from pydance.core.management.base import BaseCommand

class MyCommand(BaseCommand):
    """
    A custom management command.
    """

    help = "Description of what this command does"

    def add_arguments(self, parser):
        parser.add_argument('--name', help='Name parameter')
        parser.add_argument('--count', type=int, default=1, help='Count parameter')

    def handle(self, *args, **options):
        """Execute the command"""
        # Your command logic here
        name = options.get('name', 'World')
        count = options.get('count', 1)

        for i in range(count):
            self.stdout.write(f"Hello {name}! (#{i+1})")
```

### Command Registration

Commands are automatically discovered and registered when placed in the correct directory structure. The system scans for Python files in `management/commands/` directories and loads any classes that inherit from `BaseCommand`.

## Built-in Commands

Pydance comes with several built-in management commands:

### General
- `version`: Show the version of Pydance
- `check`: Check the project for common problems
- `help`: Show available commands

### Future Commands
Additional commands will be added for:
- Database management (`migrate`, `makemigrations`, etc.)
- Server management (`runserver`, `startapp`, etc.)
- Testing and deployment

## Usage Examples

### Running Commands

```bash
# Framework commands (anywhere)
pydance startproject myproject
pydance version

# Management commands (in project directory)
cd myproject
python manage.py check
python manage.py version
python manage.py help
```

### Creating a Custom Command

1. Create the management commands directory:
```bash
mkdir -p management/commands
touch management/commands/__init__.py
```

2. Create a custom command file:
```python
# management/commands/greet.py
from pydance.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Greet someone nicely"

    def add_arguments(self, parser):
        parser.add_argument('name', help='Person to greet')
        parser.add_argument('--style', choices=['formal', 'casual'], default='casual')

    def handle(self, *args, **options):
        name = options['name']
        style = options['style']

        if style == 'formal':
            greeting = f"Good day, {name}!"
        else:
            greeting = f"Hey {name}!"

        self.stdout.write(greeting)
```

3. Run your custom command:
```bash
python manage.py greet Alice --style formal
```

## Advanced Features

### Command Arguments

Commands can accept various types of arguments:

```python
def add_arguments(self, parser):
    # Positional arguments
    parser.add_argument('name', help='Required name')

    # Optional arguments
    parser.add_argument('--count', type=int, default=1, help='Number of times')

    # Boolean flags
    parser.add_argument('--verbose', action='store_true', help='Verbose output')

    # Choices
    parser.add_argument('--style', choices=['formal', 'casual'], default='casual')
```

### Accessing Settings

Commands can access your project's settings:

```python
from django.conf import settings

class MyCommand(BaseCommand):
    def handle(self, *args, **options):
        debug_mode = settings.DEBUG
        database_url = settings.DATABASE_URL
        # Use settings in your command logic
```

### Database Operations

Commands can interact with the database:

```python
from myapp.models import MyModel

class CleanupCommand(BaseCommand):
    help = "Clean up old data"

    def handle(self, *args, **options):
        # Query and manipulate data
        old_records = MyModel.objects.filter(created_at__lt='2023-01-01')
        count = old_records.delete()
        self.stdout.write(f"Deleted {count} old records")
```

### File Operations

Commands can work with files:

```python
import os
from pathlib import Path

class GenerateFilesCommand(BaseCommand):
    help = "Generate project files"

    def handle(self, *args, **options):
        project_root = Path.cwd()

        # Create directories
        static_dir = project_root / 'static'
        static_dir.mkdir(exist_ok=True)

        # Create files
        readme = project_root / 'README.md'
        if not readme.exists():
            readme.write_text("# My Project\n\nGenerated by management command.")
```

## Command Discovery

Pydance automatically discovers commands from:

1. Built-in commands in `src/pydance/core/management/commands/`
2. Custom commands in project `management/commands/` directories
3. Commands in installed apps that follow the same structure

The discovery process happens when the management system is initialized.

## Error Handling

Commands should handle errors gracefully:

```python
class SafeCommand(BaseCommand):
    def handle(self, *args, **options):
        try:
            # Your command logic
            risky_operation()
        except Exception as e:
            self.stderr.write(f"Error: {e}")
            return 1  # Return non-zero exit code

        self.stdout.write("Command completed successfully")
        return 0
```

## Best Practices

1. **Descriptive names**: Use clear, descriptive command names
2. **Help text**: Provide helpful descriptions for commands and arguments
3. **Error handling**: Handle errors gracefully and provide meaningful messages
4. **Modularity**: Keep commands focused on single responsibilities
5. **Documentation**: Document complex commands with docstrings and comments
6. **Testing**: Test your commands to ensure they work correctly

## Integration with Pydance Apps

Commands can integrate with Pydance applications by importing and using app components:

```python
# In your command
from myapp.services import MyService
from myapp.utils import helper_function

class MyAppCommand(BaseCommand):
    def handle(self, *args, **options):
        service = MyService()
        result = service.do_something()
        helper_function(result)
        self.stdout.write("App integration complete")
```

This allows commands to interact with your application's services, models, and utilities.
