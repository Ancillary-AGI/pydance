"""
Database management commands for Pydance CLI
"""

import argparse
from typing import List, Any



class MigrateCommand(BaseCommand):
    """Run database migrations command"""

    def __init__(self):
        super().__init__('migrate', 'Run database migrations')

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument('--action', choices=['migrate', 'downgrade', 'reset', 'status', 'list'],
                           default='migrate', help='Action to perform')
        parser.add_argument('--model', help='Specific model to migrate (default: all)')
        parser.add_argument('--version', type=int, help='Target version for downgrade (e.g., --version 2)')
        parser.add_argument('--migration-id', help='Specific migration ID to run (e.g., --migration-id 001)')
        parser.add_argument('--target-version', type=int, help='Target version to migrate to (e.g., --target-version 3)')
        parser.add_argument('--migration', help='Specific migration file to run')
        parser.add_argument('--database-url', help='Database connection URL')
        parser.add_argument('--models-package', default='app.models',
                           help='Python package path to discover models from')
        parser.add_argument('--dry-run', action='store_true',
                           help='Show what would be done without making changes')
        parser.add_argument('--verbose', '-v', action='store_true',
                           help='Verbose output')
        parser.add_argument('--force', action='store_true',
                           help='Force migration even if it may cause data loss')
        parser.add_argument('--specific-model', help='Migrate only this specific model (e.g., --specific-model User)')

    def handle(self, args: Any) -> int:
        import asyncio

        async def run_migrations():
            try:
                # Get database configuration
                db_config = DatabaseConfig.from_env()
                if not db_config:
                    print("❌ No database configuration found")
                    return 1

                # Get app package name
                app_package = getattr(args, 'models_package', 'app')

                # Handle different actions
                if args.action == 'status':
                    print(f"🔍 Checking migration status for app: {app_package}")
                    status = await check_migration_status(db_config, app_package)
                    print("📊 Migration Status:")
                    print(f"  • Total models: {status['total_models']}")
                    print(f"  • Up to date: {status['up_to_date']}")
                    print(f"  • Needs update: {status['needs_update']}")
                    for model in status['models']:
                        status_icon = "✅" if model['up_to_date'] else "⏳"
                        print(f"    {status_icon} {model['name']}: v{model['current_version']} -> v{model['target_version']}")
                    return 0

                elif args.action == 'list':
                    print(f"📋 Listing all migrations for app: {app_package}")
                    status = await check_migration_status(db_config, app_package)
                    print("Available Models and Migrations:")
                    for model in status['models']:
                        print(f"  • {model['name']}: Current v{model['current_version']}, Target v{model['target_version']}")
                    return 0

                elif args.action == 'downgrade':
                    if not args.version and not args.target_version:
                        print("❌ Version required for downgrade action (--version or --target-version)")
                        return 1
                    target_ver = args.target_version or args.version
                    print(f"⬇️  Downgrading migrations to version {target_ver}")

                    # Handle specific migration ID for downgrade
                    if args.migration_id:
                        print(f"🔍 Downgrading specific migration: {args.migration_id}")

                elif args.action == 'reset':
                    print("🔄 Resetting all migrations")
                    if not getattr(args, 'force', False):
                        confirm = input("⚠️  This will reset all migrations. Continue? (y/N): ").lower().strip()
                        if confirm not in ['y', 'yes']:
                            print("Operation cancelled")
                            return 0

                print(f"🔄 Running migrations for app: {app_package}")

                # Run migrations
                results = await migrate_app(
                    db_config,
                    app_package=app_package,
                    dry_run=args.dry_run
                )

                if args.dry_run:
                    print("📋 Dry run results:")
                    print(f"  • Models processed: {results['models_processed']}")
                    print(f"  • Migrations would be applied: {len(results['migrations'])}")
                    for migration in results['migrations']:
                        print(f"    - {migration['model']}: v{migration['from_version']} -> v{migration['to_version']}")
                else:
                    print("✅ Migration complete:")
                    print(f"  • Models processed: {results['models_processed']}")
                    print(f"  • Migrations applied: {results['migrations_applied']}")

                if results['errors']:
                    print("❌ Errors encountered:")
                    for error in results['errors']:
                        print(f"  • {error}")
                    return 1

                return 0

            except Exception as e:
                print(f"❌ Migration failed: {e}")
                import traceback
                traceback.print_exc()
                return 1

        return asyncio.run(run_migrations())


class MakeMigrationsCommand(BaseCommand):
    """Create database migrations command"""

    def __init__(self):
        super().__init__('makemigrations', 'Create database migrations')

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument('--app', help='App to create migrations for')
        parser.add_argument('--name', default='auto', help='Migration name')

    def handle(self, args: Any) -> int:
        import asyncio

        async def create_migrations():
            try:
                print(f"🔍 Creating migrations for app: {args.app}")

                # Discover models from the specified app
                models = []

                if args.app:
                    try:
                        # Import the app module
                        import importlib
                        app_module = importlib.import_module(args.app)

                        # Find all model classes in the module
                        import inspect

                        for name, obj in inspect.getmembers(app_module):
                            if (inspect.isclass(obj) and
                                issubclass(obj, BaseModel) and
                                obj != BaseModel):
                                models.append(obj)
                                print(f"  📝 Found model: {name}")

                    except ImportError as e:
                        print(f"❌ Could not import app '{args.app}': {e}")
                        return 1
                else:
                    # Auto-discover models from common locations
                    search_paths = ['app.models', 'models', 'src.models']

                    for path in search_paths:
                        try:
                            import importlib
                            module = importlib.import_module(path)

                            import inspect

                            for name, obj in inspect.getmembers(module):
                                if (inspect.isclass(obj) and
                                    issubclass(obj, BaseModel) and
                                    obj != BaseModel):
                                    models.append(obj)
                                    print(f"  📝 Found model: {name}")

                        except ImportError:
                            continue  # Module not found, try next path

                if not models:
                    print("❌ No models found to create migrations for")
                    print("💡 Make sure your models inherit from BaseModel and are importable")
                    return 1

                print(f"📊 Found {len(models)} model(s)")

                # Generate migration name
                migration_name = args.name if args.name != 'auto' else None

                # Create migrations
                migration = await make_migrations(models, migration_name)

                print("✅ Migration created successfully!")
                print(f"   ID: {migration.id}")
                print(f"   Name: {migration.name}")
                print(f"   Description: {migration.description}")
                print(f"   Operations: {len(migration.operations)}")

                if migration.migration_file:
                    print(f"   File: {migration.migration_file}")

                print("\n🎯 Next step: Run 'python manage.py migrate' to apply the migration")

                return 0

            except Exception as e:
                print(f"❌ Failed to create migrations: {e}")
                import traceback
                traceback.print_exc()
                return 1

        return asyncio.run(create_migrations())


class ShowMigrationsCommand(BaseCommand):
    """Show migration status command"""

    def __init__(self):
        super().__init__('showmigrations', 'Show migration status')

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument('--app', help='App to show migrations for')

    def handle(self, args: Any) -> int:
        import asyncio

        async def show_migration_status():
            try:
                print("📋 Migration Status")
                print("=" * 60)

                status_text = await show_migrations()

                if not status_text or "No migrations found" in status_text:
                    print("No migrations found")
                    print("\n💡 To create migrations, run: python manage.py makemigrations")
                    return 0

                print(status_text)

                # Show summary
                summary = await get_migration_status()

                print("\n📊 Summary:")
                print(f"  Total migrations: {summary['total']}")
                print(f"  Applied: {summary['applied']}")
                print(f"  Pending: {summary['pending']}")

                if summary['last_applied']:
                    print(f"  Last applied: {summary['last_applied']}")

                return 0

            except Exception as e:
                print(f"❌ Failed to show migration status: {e}")
                import traceback
                traceback.print_exc()
                return 1

        return asyncio.run(show_migration_status())


class DbshellCommand(BaseCommand):
    """Start database shell command"""

    def __init__(self):
        super().__init__('dbshell', 'Start database shell')

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument('--database-url', help='Database connection URL')
        parser.add_argument('--autocomplete', action='store_true',
                           help='Enable auto-completion')
        parser.add_argument('--history', action='store_true',
                           help='Enable command history')
        parser.add_argument('--multi-db', action='store_true',
                           help='Enable multi-database mode')
        parser.add_argument('--query-builder', action='store_true',
                           help='Enable visual query builder')
        parser.add_argument('--visualize', action='store_true',
                           help='Enable query visualization')

    def handle(self, args: Any) -> int:
        import asyncio

        async def run_dbshell():
            try:
                await dbshell()
                return 0
            except Exception as e:
                print(f"❌ Failed to start database shell: {e}")
                return 1

        return asyncio.run(run_dbshell())


# Register commands

registry.register(MigrateCommand())
registry.register(MakeMigrationsCommand())
registry.register(ShowMigrationsCommand())
registry.register(DbshellCommand())
