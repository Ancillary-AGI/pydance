"""
Pydance Management Commands

This module provides the framework for creating and running management commands.
Similar to Django's management system, this allows for both built-in and custom commands.
"""

import os
import sys
from pathlib import Path


def execute_from_command_line(argv=None):
    """
    Execute management commands from the command line.

    This is the main entry point for running management commands.
    It should be called from a project's manage.py script.

    Args:
        argv: Command line arguments (defaults to sys.argv)
    """
    if argv is None:
        argv = sys.argv

    # Import the management command system
    from .base import ManagementUtility

    # Create and run the management utility
    utility = ManagementUtility(argv)
    utility.execute()


def get_commands():
    """
    Get all available management commands.

    Returns:
        Dictionary mapping command names to their help text
    """
    from .base import ManagementUtility
    utility = ManagementUtility()
    return utility.get_commands()


def call_command(command_name, *args, **options):
    """
    Call a management command programmatically.

    Args:
        command_name: Name of the command to call
        *args: Positional arguments
        **options: Keyword arguments/options

    Returns:
        The result of the command execution
    """
    from .base import ManagementUtility
    utility = ManagementUtility()
    return utility.call_command(command_name, *args, **options)
