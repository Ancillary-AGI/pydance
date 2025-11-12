"""
Project management commands for Pydance CLI
"""

import os
import argparse
from typing import List, Any



class StartProjectCommand(BaseCommand):
    """Create a new Pydance project command"""

    def __init__(self):
        super().__init__('startproject', 'Create a new Pydance project')

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument('name', help='Project name')
        parser.add_argument('--template', default='basic',
                           choices=['minimal', 'basic', 'api', 'full', 'microservice', 'enterprise'],
                           help='Project template: minimal (simple), basic (standard), api (REST), full (complete), microservice (distributed), enterprise (production-ready)')
        parser.add_argument('--git-repo', help='Git repository URL to clone as template')
        parser.add_argument('--git-branch', default='main', help='Git branch to clone')

    def validate_args(self, args: Any) -> List[str]:
        errors = []

        if not self._validate_app_name_str(args.name):
            errors.append(f"Invalid project name: {args.name} (must be a valid Python identifier)")

        if os.path.exists(args.name):
            errors.append(f"Directory '{args.name}' already exists")

        return errors

    def handle(self, args: Any) -> int:
        project_name = args.name
        template = args.template

        # Interactive mode for template selection
        if getattr(args, 'interactive', False) or template == 'basic':
            print("🚀 Welcome to Pydance Project Creator!")
            print("Let's set up your new project with the perfect template.\n")

            print("Available templates:")
            templates = {
                'minimal': 'Simple, lightweight setup for small projects',
                'basic': 'Standard web application with common features',
                'api': 'REST API focused with authentication and documentation',
                'full': 'Complete application with all Pydance features',
                'microservice': 'Microservice architecture with service discovery',
                'enterprise': 'Production-ready with advanced security and monitoring'
            }

            for key, desc in templates.items():
                marker = "→" if key == template else " "
                print(f"  {marker} {key}: {desc}")

            if getattr(args, 'interactive', False):
                print(f"\nCurrent selection: {template}")
                choice = input("Choose a template (or press Enter to keep current): ").strip().lower()
                if choice and choice in templates:
                    template = choice
                    print(f"✅ Selected template: {template}")
                elif choice:
                    print(f"⚠️  Invalid choice '{choice}', keeping current template: {template}")

        print(f"\n📦 Creating Pydance project '{project_name}' with '{template}' template...")

        # Check if git repo is specified
        if hasattr(args, 'git_repo') and args.git_repo:
            print(f"Cloning template from: {args.git_repo}")
            success = self._clone_git_template(project_name, args.git_repo, args.git_branch)
            if not success:
                return 1
        else:
            # Create project structure from template
            self._create_project_from_template(project_name, template)

        print(f"\n✅ Project '{project_name}' created successfully!")
        print("\n🎯 Next steps:")
        print(f"  cd {project_name}")
        print("  pip install -r requirements.txt")
        print("  python manage.py migrate")
        print("  python manage.py createsuperuser")
        print("  python manage.py runserver")
        print("\n📚 For more information, check the README.md file in your project directory")
        print(f"\n🎉 Happy coding with Pydance!")

        return 0

    def _clone_git_template(self, project_name: str, git_repo: str, branch: str) -> bool:
        """Clone a project template from git repository"""
        import subprocess

        try:
            # Check if git is available
            if not self._check_command_exists('git'):
                print("❌ Git is not installed or not in PATH")
                print("Falling back to basic template...")
                self._create_project_from_template(project_name, 'basic')
                return True

            # Clone the repository
            cmd = ['git', 'clone', '--depth', '1']
            if branch != 'main':
                cmd.extend(['-b', branch])
            cmd.extend([git_repo, project_name])

            print(f"📥 Cloning repository: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"❌ Failed to clone repository: {result.stderr}")
                print("Falling back to basic template...")
                self._create_project_from_template(project_name, 'basic')
                return True

            # Remove .git directory to start fresh
            git_dir = Path(project_name) / '.git'
            if git_dir.exists():
                import shutil
                shutil.rmtree(git_dir)

            print("✅ Template cloned successfully")
            return True

        except Exception as e:
            print(f"❌ Error cloning template: {e}")
            print("Falling back to basic template...")
            self._create_project_from_template(project_name, 'basic')
            return True

    def _create_project_from_template(self, project_name: str, template: str) -> None:
        """Create project structure from built-in template"""
        # Create standard project structure following framework conventions
        project_dirs = [
            project_name,
            f"{project_name}/apps",
            f"{project_name}/static",
            f"{project_name}/static/css",
            f"{project_name}/static/js",
            f"{project_name}/static/images",
            f"{project_name}/templates",
            f"{project_name}/config",
            f"{project_name}/tests",
            f"{project_name}/docs",
        ]

        for dir_path in project_dirs:
            os.makedirs(dir_path, exist_ok=True)

        # Create main application file
        app_content = f'''"""
{project_name} - Pydance  Application
"""


# Create application instance
app = Application()

# Load configuration
config = Config()
config.from_object('config.settings')

# Database setup
db = DatabaseConnection(config.DATABASE_URL)

@app.on_startup
async def startup():
    """Application startup event"""
    await db.connect()
    print("Application started successfully!")

@app.on_shutdown
async def shutdown():
    """Application shutdown event"""
    await db.disconnect()
    print("Application shut down")

# Basic routes
@app.route('/')
async def home(request):
    """Home page"""
    return {{
        'message': f'Welcome to {project_name}!',
        'status': 'running',
        'version': '1.0.0'
    }}

@app.route('/health')
async def health(request):
    """Health check endpoint"""
    return {{
        'status': 'healthy',
        'timestamp': request.headers.get('date', ''),
        'service': '{project_name}'
    }}

@app.route('/api/v1/info')
async def api_info(request):
    """API information"""
    return {{
        'name': '{project_name}',
        'version': '1.0.0',
        'description': 'Pydance  application',
        'endpoints': [
            '/',
            '/health',
            '/api/v1/info'
        ]
    }}

if __name__ == '__main__':
    # Run directly for development
    uvicorn.run(app, host='127.0.0.1', port=8000, reload=True)
'''

        with open(f"{project_name}/app.py", 'w', encoding='utf-8') as f:
            f.write(app_content)

        # Create manage.py for CLI commands
        manage_content = f'''#!/usr/bin/env python3
"""
{project_name} Management Script
"""

import os

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Main entry point"""
    main()

if __name__ == '__main__':
    main()
'''

        with open(f"{project_name}/manage.py", 'w', encoding='utf-8') as f:
            f.write(manage_content)

        # Make manage.py executable
        os.chmod(f"{project_name}/manage.py", 0o755)

        # Create configuration file
        config_content = f'''# {project_name} Configuration

# Application settings
DEBUG = True
SECRET_KEY = "{os.urandom(32).hex()}"
APP_NAME = "{project_name}"

# Server settings
HOST = "127.0.0.1"
PORT = 8000
WORKERS = 1

# Database settings
DATABASE_URL = "mongodb://localhost:27017/{project_name.lower()}"

# Security settings
SESSION_SECRET = "{os.urandom(32).hex()}"
JWT_SECRET = "{os.urandom(32).hex()}"

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "logs/app.log"

# Email settings (optional)
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USER = ""
EMAIL_PASSWORD = ""

# File upload settings
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
UPLOAD_FOLDER = "uploads"

# API settings
API_PREFIX = "/api/v1"
API_VERSION = "1.0.0"
'''

        with open(f"{project_name}/config/settings.py", 'w', encoding='utf-8') as f:
            f.write(config_content)

        # Create __init__.py for config
        with open(f"{project_name}/config/__init__.py", 'w', encoding='utf-8') as f:
            f.write('')

        # Create requirements file
        requirements_content = '''# Core dependencies
pydance >=1.0.0
motor>=3.0.0
pymongo>=4.0.0

# Web server
uvicorn[standard]>=0.20.0
hypercorn>=0.14.0

# Templates
jinja2>=3.0.0

# Utilities
python-dotenv>=0.19.0
click>=8.0.0

# Development dependencies
pytest>=7.0.0
pytest-asyncio>=0.21.0
black>=22.0.0
flake8>=4.0.0
'''

        with open(f"{project_name}/requirements.txt", 'w', encoding='utf-8') as f:
            f.write(requirements_content)

        # Create .env.example file
        env_content = f'''# {project_name} Environment Variables

# Database
DATABASE_URL=mongodb://localhost:27017/{project_name.lower()}

# Application
DEBUG=True
SECRET_KEY={os.urandom(32).hex()}

# Server
HOST=127.0.0.1
PORT=8000

# Security
SESSION_SECRET={os.urandom(32).hex()}
JWT_SECRET={os.urandom(32).hex()}

# Email (configure as needed)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
'''

        with open(f"{project_name}/.env.example", 'w', encoding='utf-8') as f:
            f.write(env_content)

        # Create .gitignore
        gitignore_content = '''# Python
__pycache__/
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

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
*.log
logs/

# Database
*.db
*.sqlite3

# Uploads
uploads/
media/

# Node modules (if using frontend)
node_modules/

# Coverage
.coverage
htmlcov/
.pytest_cache/

# Temporary files
*.tmp
*.temp
'''

        with open(f"{project_name}/.gitignore", 'w', encoding='utf-8') as f:
            f.write(gitignore_content)

        # Create README.md
        readme_content = f'''# {project_name}

A Pydance  web application.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy environment configuration:
```bash
cp .env.example .env
```

4. Run database migrations:
```bash
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

## Project Structure

```
{project_name}/
├── app.py              # Main application file
├── manage.py           # Management script
├── config/             # Configuration files
│   ├── __init__.py
│   └── settings.py
├── apps/               # Application modules
├── static/             # Static files (CSS, JS, images)
├── templates/          # HTML templates
├── tests/              # Test files
└── docs/               # Documentation
```

## Available Commands

- `python manage.py runserver` - Start development server
- `python manage.py migrate` - Run database migrations
- `python manage.py createsuperuser` - Create admin user
- `python manage.py test` - Run tests
- `python manage.py shell` - Start interactive shell

## API Endpoints

- `GET /` - Home page
- `GET /health` - Health check
- `GET /api/v1/info` - API information

## License

MIT License
'''

        with open(f"{project_name}/README.md", 'w', encoding='utf-8') as f:
            f.write(readme_content)

        # Create basic test file
        test_content = f'''"""
Tests for {project_name}
"""



def test_home_endpoint():
    """Test home endpoint"""
    # This is a placeholder test
    # Add your actual tests here
    assert True


def test_health_endpoint():
    """Test health endpoint"""
    # This is a placeholder test
    # Add your actual tests here
    assert True


if __name__ == '__main__':
    pytest.main([__file__])
'''

        with open(f"{project_name}/tests/__init__.py", 'w', encoding='utf-8') as f:
            f.write('')

        with open(f"{project_name}/tests/test_app.py", 'w', encoding='utf-8') as f:
            f.write(test_content)

        # Create logs directory
        os.makedirs(f"{project_name}/logs", exist_ok=True)

        print(f"📁 Created project structure with {len(project_dirs)} directories")
        print("📄 Generated configuration and template files")

    def _validate_app_name_str(self, name: str) -> bool:
        """Validate application name string"""
        if not name:
            return False
        # Must be valid Python identifier
        import re
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name))

    def _check_command_exists(self, command: str) -> bool:
        """Check if system command exists"""
        import subprocess
        try:
            subprocess.run([command, '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False


class StartAppCommand(BaseCommand):
    """Create a new Pydance app command"""

    def __init__(self):
        super().__init__('startapp', 'Create a new Pydance app')

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument('name', help='App name')

    def validate_args(self, args: Any) -> List[str]:
        errors = []

        if not self._validate_app_name_str(args.name):
            errors.append(f"Invalid app name: {args.name} (must be a valid Python identifier)")

        if os.path.exists(args.name):
            errors.append(f"Directory '{args.name}' already exists")

        return errors

    def handle(self, args: Any) -> int:
        app_name = args.name

        print(f"Creating Pydance app '{app_name}'...")

        # Create app structure
        os.makedirs(f"{app_name}/models")
        os.makedirs(f"{app_name}/views")
        os.makedirs(f"{app_name}/controllers")
        os.makedirs(f"{app_name}/templates/{app_name}")
        os.makedirs(f"{app_name}/static/{app_name}")

        # Create __init__.py
        init_content = f'''"""
{app_name} app for Pydance
"""
'''

        with open(f"{app_name}/__init__.py", 'w') as f:
            f.write(init_content)

        # Create models file
        models_content = f'''"""
Models for {app_name} app
"""

from pydance.models.base import BaseModel, Field

class ExampleModel(BaseModel):
    """Example model"""
    name = Field(str, required=True)
    description = Field(str)
    created_at = Field(datetime, default=datetime.now)

    class Meta:
        table_name = "{app_name}_example"
'''

        with open(f"{app_name}/models/__init__.py", 'w') as f:
            f.write(models_content)

        # Create views file
        views_content = f'''"""
Views for {app_name} app
"""


class HomeView(TemplateView):
    template_name = "{app_name}/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['app_name'] = '{app_name}'
        return context
'''

        with open(f"{app_name}/views/__init__.py", 'w') as f:
            f.write(views_content)

        # Create controllers file
        controllers_content = f'''"""
Controllers for {app_name} app
"""


class {app_name.title()}Controller(BaseController):
    """Controller for {app_name}"""

    def index(self, request):
        """Index action"""
        return self.render_template("{app_name}/index.html", {{
            'title': '{app_name.title()}',
            'message': 'Welcome to {app_name}!'
        }})
'''

        with open(f"{app_name}/controllers/__init__.py", 'w') as f:
            f.write(controllers_content)

        print(f"App '{app_name}' created successfully!")

        return 0

    def _validate_app_name_str(self, name: str) -> bool:
        """Validate application name string"""
        if not name:
            return False
        # Must be valid Python identifier
        import re
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name))


class CollectStaticCommand(BaseCommand):
    """Collect static files command"""

    def __init__(self):
        super().__init__('collectstatic', 'Collect static files')

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument('--noinput', action='store_true', help='Do not prompt for input')
        parser.add_argument('--clear', action='store_true', help='Clear the existing files before collecting')
        parser.add_argument('--cdn', action='store_true', help='Deploy to CDN after collecting')
        parser.add_argument('--hash', action='store_true', help='Add hash-based versioning')

    def handle(self, args: Any) -> int:
        # Import directly to avoid circular imports
        import importlib.util
        spec = importlib.util.spec_from_file_location("staticfiles", "src/pydance/utils/staticfiles.py")
        staticfiles = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(staticfiles)

        # Create mock args object for the staticfiles command
        class MockArgs:
            def __init__(self):
                self.clear = args.clear
                self.cdn = args.cdn
                self.hash = args.hash

        mock_args = MockArgs()
        staticfiles.cmd_collectstatic(mock_args)

        return 0


# Register commands

registry.register(StartProjectCommand())
registry.register(StartAppCommand())
registry.register(CollectStaticCommand())
