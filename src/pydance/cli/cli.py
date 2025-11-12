#!/usr/bin/env python3
"""
Pydance CLI - Command Line Interface for Pydance Framework

Refactored to use modular command system for better maintainability.
"""

import argparse



class PydanceCLI:
    """Command Line Interface for Pydance Framework"""

    def __init__(self):
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create and configure the argument parser"""
        parser = argparse.ArgumentParser(
            description="Pydance Framework CLI",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""Examples:
  pydance start --host 0.0.0.0 --port 8000
  pydance start --reload
  pydance stop
  pydance restart
  pydance shell
  pydance migrate
  pydance startproject myproject
  pydance startapp myapp
  pydance runserver
  pydance makemigrations
  pydance test
            """
        )

        # Global arguments
        parser.add_argument('--config', help='Path to config file', default='config.py')
        parser.add_argument('--app', help='Application module path (e.g., myapp:app)', default='app:app')

        # Add interactive flag for better UX
        parser.add_argument('--interactive', '-i', action='store_true',
                           help='Run in interactive mode with prompts')

        # Subparsers for commands
        subparsers = parser.add_subparsers(dest='command', help='Available commands')

        # Register all commands from the registry
        for command_name in registry.list_commands():
            command = registry.get_command(command_name)
            if command:
                command_parser = subparsers.add_parser(command.name, help=command.help_text)
                command.add_arguments(command_parser)

        # Help command
        subparsers.add_parser('help', help='Show help')

        return parser

    def run(self) -> int:
        """Run the CLI"""
        args = self.parser.parse_args()

        if not hasattr(args, 'command') or not args.command:
            self.parser.print_help()
            return 0

        if args.command == 'help':
            self.parser.print_help()
            return 0

        # Get the command from registry
        command = registry.get_command(args.command)
        if not command:
            print(f"Unknown command: {args.command}")
            self.parser.print_help()
            return 1

        # Validate arguments
        validation_errors = command.validate_args(args)
        if validation_errors:
            print("❌ Validation errors:")
            for error in validation_errors:
                print(f"  • {error}")
            return 1

        # Execute the command
        return command.handle(args)


def main():
    """Main CLI entry point"""
    cli = PydanceCLI()
    cli.run()


if __name__ == '__main__':
    main()
