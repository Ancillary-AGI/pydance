"""
Server management commands for Pydance CLI
"""

import os
import sys
import signal
import subprocess
import time
import argparse
from pathlib import Path
from typing import List, Any

from . import BaseCommand


class StartCommand(BaseCommand):
    """Start the server command"""

    def __init__(self):
        super().__init__('start', 'Start the server')

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
        parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
        parser.add_argument('--workers', type=int, default=1, help='Number of workers')
        parser.add_argument('--reload', action='store_true', help='Enable auto-reload')
        parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    def validate_args(self, args: Any) -> List[str]:
        errors = []

        if not self._validate_host(args.host):
            errors.append(f"Invalid host address: {args.host}")

        if not self._validate_port(args.port):
            errors.append(f"Invalid port number: {args.port} (must be 1-65535)")

        if not self._validate_workers(args.workers):
            errors.append(f"Invalid worker count: {args.workers} (must be 1-100)")

        if not self._validate_module_path(args.app):
            errors.append(f"Invalid app module path: {args.app}")

        if not self._check_module_exists(args.app):
            errors.append(f"App module not found: {args.app}")

        if not self._check_command_exists('hypercorn'):
            errors.append("Hypercorn is not installed or not in PATH")

        return errors

    def handle(self, args: Any) -> int:
        print(f"Starting Pydance server on {args.host}:{args.port}")

        # Set environment variables
        env = os.environ.copy()
        env['PYDANCE_HOST'] = args.host
        env['PYDANCE_PORT'] = str(args.port)
        env['PYDANCE_WORKERS'] = str(args.workers)
        env['PYDANCE_RELOAD'] = '1' if args.reload else '0'
        env['PYDANCE_DEBUG'] = '1' if args.debug else '0'

        # Add current directory to Python path
        env['PYTHONPATH'] = os.getcwd() + os.pathsep + env.get('PYTHONPATH', '')

        # Build command
        cmd = [
            sys.executable, '-m', 'hypercorn',
            f'{args.app}',
            '--bind', f'{args.host}:{args.port}',
        ]

        if args.workers > 1:
            cmd.extend(['--workers', str(args.workers)])

        if args.reload:
            cmd.append('--reload')

        if args.debug:
            cmd.extend(['--log-level', 'debug'])

        # Save PID for management
        try:
            self._save_pid()
        except Exception as e:
            print(f"Warning: Could not save PID file: {e}")

        try:
            subprocess.run(cmd, env=env)
        except KeyboardInterrupt:
            print("\nServer stopped")
        except subprocess.CalledProcessError as e:
            print(f"❌ Server failed to start: {e}")
            return 1
        except Exception as e:
            print(f"❌ Unexpected error starting server: {e}")
            return 1
        finally:
            try:
                self._remove_pid()
            except Exception as e:
                print(f"Warning: Could not remove PID file: {e}")

        return 0

    # Utility methods (extracted from original CLI)
    def _validate_host(self, host: str) -> bool:
        """Validate host address"""
        if not host:
            return False
        # Allow localhost, 127.0.0.1, 0.0.0.0, or valid IP addresses
        if host in ['localhost', '127.0.0.1', '0.0.0.0']:
            return True
        # Check for valid IP address format
        import re
        ip_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
        if not ip_pattern.match(host):
            return False
        # Check each octet is 0-255
        octets = host.split('.')
        return all(0 <= int(octet) <= 255 for octet in octets)

    def _validate_port(self, port: int) -> bool:
        """Validate port number"""
        return 1 <= port <= 65535

    def _validate_workers(self, workers: int) -> bool:
        """Validate worker count"""
        return 1 <= workers <= 100

    def _validate_module_path(self, module_path: str) -> bool:
        """Validate Python module path"""
        if not module_path:
            return False
        # Allow module paths like 'app', 'myapp.core', 'myapp:app'
        import re
        pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*(?::[a-zA-Z_][a-zA-Z0-9_]*)*$')
        return bool(pattern.match(module_path))

    def _check_module_exists(self, module_path: str) -> bool:
        """Check if Python module exists"""
        try:
            if ':' in module_path:
                module_path, _ = module_path.split(':', 1)
            import importlib
            importlib.import_module(module_path)
            return True
        except ImportError:
            return False

    def _check_command_exists(self, command: str) -> bool:
        """Check if system command exists"""
        try:
            subprocess.run([command, '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _get_pid_file(self) -> Path:
        """Get PID file path"""
        return Path('.pydance.pid')

    def _save_pid(self) -> None:
        """Save current process PID"""
        pid_file = self._get_pid_file()
        try:
            pid_file.write_text(str(os.getpid()))
        except (OSError, PermissionError) as e:
            raise Exception(f"Cannot write PID file: {e}")

    def _remove_pid(self) -> None:
        """Remove PID file"""
        pid_file = self._get_pid_file()
        if pid_file.exists():
            try:
                pid_file.unlink()
            except OSError as e:
                print(f"Warning: Could not remove PID file: {e}")


class StopCommand(BaseCommand):
    """Stop the server command"""

    def __init__(self):
        super().__init__('stop', 'Stop the server')

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        pass  # No additional arguments needed

    def handle(self, args: Any) -> int:
        pid = self._get_pid()
        if not pid:
            print("No server process found")
            return 1

        try:
            os.kill(pid, signal.SIGTERM)
            print("Server stopped")
            self._remove_pid()
            return 0
        except ProcessLookupError:
            print("Server process not found")
            self._remove_pid()
            return 1
        except Exception as e:
            print(f"Error stopping server: {e}")
            return 1

    def _get_pid_file(self) -> Path:
        """Get PID file path"""
        return Path('.pydance.pid')

    def _get_pid(self) -> int:
        """Get saved PID"""
        pid_file = self._get_pid_file()
        if not pid_file.exists():
            return 0

        try:
            content = pid_file.read_text().strip()
            if not content:
                return 0
            pid = int(content)
            if pid <= 0:
                return 0
            return pid
        except (ValueError, OSError) as e:
            print(f"Warning: Invalid PID file content: {e}")
            return 0

    def _remove_pid(self) -> None:
        """Remove PID file"""
        pid_file = self._get_pid_file()
        if pid_file.exists():
            try:
                pid_file.unlink()
            except OSError as e:
                print(f"Warning: Could not remove PID file: {e}")


class RestartCommand(BaseCommand):
    """Restart the server command"""

    def __init__(self):
        super().__init__('restart', 'Restart the server')

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
        parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
        parser.add_argument('--workers', type=int, default=1, help='Number of workers')
        parser.add_argument('--reload', action='store_true', help='Enable auto-reload')
        parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    def handle(self, args: Any) -> int:
        print("Restarting server...")

        # Stop the server
        stop_cmd = StopCommand()
        stop_cmd.handle(args)

        # Wait for shutdown
        time.sleep(2)

        # Start the server
        start_cmd = StartCommand()
        return start_cmd.handle(args)


class StatusCommand(BaseCommand):
    """Show server status command"""

    def __init__(self):
        super().__init__('status', 'Show server status')

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        pass  # No additional arguments needed

    def handle(self, args: Any) -> int:
        pid = self._get_pid()
        if pid:
            try:
                os.kill(pid, 0)  # Check if process exists
                print(f"Server is running (PID: {pid})")
                return 0
            except ProcessLookupError:
                print("Server process not found (stale PID file)")
                self._remove_pid()
                return 1
        else:
            print("Server is not running")
            return 1

    def _get_pid_file(self) -> Path:
        """Get PID file path"""
        return Path('.pydance.pid')

    def _get_pid(self) -> int:
        """Get saved PID"""
        pid_file = self._get_pid_file()
        if not pid_file.exists():
            return 0

        try:
            content = pid_file.read_text().strip()
            if not content:
                return 0
            pid = int(content)
            if pid <= 0:
                return 0
            return pid
        except (ValueError, OSError) as e:
            print(f"Warning: Invalid PID file content: {e}")
            return 0

    def _remove_pid(self) -> None:
        """Remove PID file"""
        pid_file = self._get_pid_file()
        if pid_file.exists():
            try:
                pid_file.unlink()
            except OSError as e:
                print(f"Warning: Could not remove PID file: {e}")


# Register commands
from . import registry

registry.register(StartCommand())
registry.register(StopCommand())
registry.register(RestartCommand())
registry.register(StatusCommand())
