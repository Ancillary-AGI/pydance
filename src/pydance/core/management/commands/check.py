"""
Check command for Pydance management commands.
"""

import os
from pathlib import Path
from ..base import BaseCommand


class Check(BaseCommand):
    """
    Check the Pydance project for common problems.
    """

    help = "Check the Pydance project for common problems."

    def add_arguments(self, parser):
        parser.add_argument(
            '--deploy',
            action='store_true',
            help='Check deployment settings.',
        )
        parser.add_argument(
            '--settings',
            help='Path to settings module.',
        )

    def handle(self, *args, **options):
        """
        Check the project for common problems.
        """
        parsed_args = args[0] if args else None

        self.stdout.write("Checking Pydance project...\n")

        errors = []
        warnings = []

        # Check Python version
        import sys
        if sys.version_info < (3, 8):
            errors.append("Python 3.8 or higher is required")

        # Check if we're in a project directory
        cwd = Path.cwd()
        if not self._is_pydance_project(cwd):
            warnings.append("Not in a Pydance project directory")

        # Check for common files
        required_files = ['requirements.txt', 'README.md']
        for file in required_files:
            if not (cwd / file).exists():
                warnings.append(f"Missing {file}")

        # Check settings
        if parsed_args and parsed_args.settings:
            settings_module = parsed_args.settings
        else:
            settings_module = self._find_settings_module()

        if settings_module:
            settings_errors = self._check_settings(settings_module)
            errors.extend(settings_errors)
        else:
            warnings.append("No settings module found")

        # Deployment checks
        if parsed_args and parsed_args.deploy:
            deploy_errors = self._check_deployment_settings()
            errors.extend(deploy_errors)

        # Report results
        if errors:
            self.stdout.write("❌ Errors found:\n")
            for error in errors:
                self.stdout.write(f"  • {error}\n")
            self.stdout.write("\n")

        if warnings:
            self.stdout.write("⚠️  Warnings:\n")
            for warning in warnings:
                self.stdout.write(f"  • {warning}\n")
            self.stdout.write("\n")

        if not errors and not warnings:
            self.stdout.write("✅ No problems found!\n")
        elif not errors:
            self.stdout.write("✅ No critical errors found.\n")

    def _is_pydance_project(self, path: Path) -> bool:
        """Check if the given path is a Pydance project."""
        # Look for common Pydance project indicators
        indicators = [
            path / 'manage.py',
            path / 'app.py',
            path / 'config' / 'settings.py',
        ]
        return any(indicator.exists() for indicator in indicators)

    def _find_settings_module(self) -> str:
        """Find the settings module."""
        # Common settings locations
        candidates = [
            'config.settings',
            'settings',
            'app.settings',
        ]

        for candidate in candidates:
            try:
                __import__(candidate)
                return candidate
            except ImportError:
                continue

        return None

    def _check_settings(self, settings_module: str) -> list:
        """Check settings module for common issues."""
        errors = []

        try:
            settings = __import__(settings_module, fromlist=[''])
        except ImportError as e:
            return [f"Cannot import settings module: {e}"]

        # Check for required settings
        required_settings = ['SECRET_KEY', 'DEBUG']
        for setting in required_settings:
            if not hasattr(settings, setting):
                errors.append(f"Missing required setting: {setting}")

        # Check DEBUG setting
        if hasattr(settings, 'DEBUG') and settings.DEBUG:
            errors.append("DEBUG is set to True - not suitable for production")

        # Check SECRET_KEY
        if hasattr(settings, 'SECRET_KEY'):
            if settings.SECRET_KEY == 'your-secret-key-here':
                errors.append("SECRET_KEY is not set to a secure value")

        return errors

    def _check_deployment_settings(self) -> list:
        """Check deployment-related settings."""
        errors = []

        # Check for environment variables
        required_env_vars = ['DATABASE_URL']
        for var in required_env_vars:
            if not os.getenv(var):
                errors.append(f"Environment variable {var} is not set")

        # Check for production settings
        try:
            import settings
            if hasattr(settings, 'DEBUG') and settings.DEBUG:
                errors.append("DEBUG should be False in production")
        except ImportError:
            pass

        return errors
