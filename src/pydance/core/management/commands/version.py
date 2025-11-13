"""
Version command for Pydance management commands.
"""

from ..base import BaseCommand


class Version(BaseCommand):
    """
    Show the version of Pydance.
    """

    help = "Show the version of Pydance."

    def handle(self, *args, **options):
        """
        Show version information.
        """
        try:
            import pydance
            version = getattr(pydance, '__version__', '1.0.0')
        except (ImportError, AttributeError):
            version = '1.0.0'

        self.stdout.write(f"Pydance {version}\n")
