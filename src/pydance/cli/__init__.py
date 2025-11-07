"""
Pydance CLI - Command Line Interface for Pydance Framework

This module provides the main entry point for the CLI system.
"""

# Import the main function directly from the cli module
def main():
    """Main CLI entry point"""
    try:
        from .cli import PydanceCLI
    except ImportError:
        # Fallback for different import contexts
        import cli as cli_module
        PydanceCLI = cli_module.PydanceCLI

    cli = PydanceCLI()
    cli.run()

__all__ = ['main']
