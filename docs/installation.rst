Installation Guide
==================

This guide covers all aspects of installing and setting up Pydance for development and production environments.

System Requirements
-------------------

**Minimum Requirements:**

- **Python**: 3.8 or higher
- **Operating System**: Linux, macOS, or Windows
- **Memory**: 512MB RAM (1GB recommended)
- **Disk Space**: 100MB for installation

**Recommended for Production:**

- **Python**: 3.9 or higher
- **Memory**: 2GB RAM or more
- **CPU**: Multi-core processor
- **Database**: PostgreSQL 12+, MySQL 8+, or MongoDB 4.4+

**Supported Platforms:**

- **Linux**: Ubuntu 18.04+, CentOS 7+, Debian 9+, Fedora 30+
- **macOS**: 10.14 (Mojave) or later
- **Windows**: Windows 10 or later (Windows Server 2019+ for production)

Installation Methods
--------------------

Basic Installation
~~~~~~~~~~~~~~~~~~

**Using pip (Recommended):**

.. code-block:: bash

   # Install basic Pydance framework
   pip install pydance

   # Verify installation
   python -c "import pydance; print(f'Pydance {pydance.__version__} installed successfully')"

**Using poetry:**

.. code-block:: bash

   # Add to existing project
   poetry add pydance

   # Or create new project
   poetry new my-pydance-app
   cd my-pydance-app
   poetry add pydance

**Using pipenv:**

.. code-block:: bash

   # Add to existing project
   pipenv install pydance

   # Or create new project
   mkdir my-pydance-app && cd my-pydance-app
   pipenv install pydance
   pipenv shell

Full Installation (All Features)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For development with all optional dependencies:

.. code-block:: bash

   # Install with all optional dependencies
   pip install pydance[full]

   # Or install specific feature groups
   pip install pydance[database,security,monitoring,performance]

Available feature groups:

- ``database``: Database backends (PostgreSQL, MySQL, MongoDB)
- ``security``: Advanced security features and cryptography
- ``monitoring``: Performance monitoring and metrics
- ``performance``: C/C++ extensions for maximum performance
- ``web3``: Blockchain and Web3 integrations
- ``testing``: Additional testing utilities
- ``docs``: Documentation generation tools

Development Installation
~~~~~~~~~~~~~~~~~~~~~~~~

**From Source (GitHub):**

.. code-block:: bash

   # Clone the repository
   git clone https://github.com/ancillary-ai/pydance.git
   cd pydance

   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install in development mode with all dependencies
   pip install -e .[dev,security,performance,database,web3,monitoring,testing]

   # Run tests to verify installation
   python -m pytest tests/

**Using Docker:**

.. code-block:: bash

   # Clone and build
   git clone https://github.com/ancillary-ai/pydance.git
   cd pydance

   # Build Docker image
   docker build -t pydance-dev .

   # Run development container
   docker run -it -v $(pwd):/app -p 8000:8000 pydance-dev

Production Installation
~~~~~~~~~~~~~~~~~~~~~~~

**Using Docker (Recommended for Production):**

.. code-block:: dockerfile

   # Dockerfile for production
   FROM python:3.11-slim

   # Set environment variables
   ENV PYTHONDONTWRITEBYTECODE=1
   ENV PYTHONUNBUFFERED=1
   ENV PYTHONPATH=/app

   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       gcc \
       g++ \
       libpq-dev \
       libmysqlclient-dev \
       pkg-config \
       && rm -rf /var/lib/apt/lists/*

   # Create app directory
   WORKDIR /app

   # Install Python dependencies
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   # Copy application code
   COPY . .

   # Create non-root user
   RUN useradd --create-home --shell /bin/bash pydance
   RUN chown -R pydance:pydance /app
   USER pydance

   # Expose port
   EXPOSE 8000

   # Health check
   HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
       CMD curl -f http://localhost:8000/health || exit 1

   # Start application
   CMD ["python", "main.py"]

**Using Docker Compose:**

.. code-block:: yaml

   # docker-compose.yml
   version: '3.8'

   services:
     pydance-app:
       build: .
       ports:
         - "8000:8000"
       environment:
         - DATABASE_URL=postgresql://user:password@db:5432/pydance
         - REDIS_URL=redis://redis:6379
       depends_on:
         - db
         - redis
       restart: unless-stopped

     db:
       image: postgres:14
       environment:
         POSTGRES_DB: pydance
         POSTGRES_USER: user
         POSTGRES_PASSWORD: password
       volumes:
         - postgres_data:/var/lib/postgresql/data

     redis:
       image: redis:7-alpine
       volumes:
         - redis_data:/data

   volumes:
     postgres_data:
     redis_data:

Database Setup
--------------

PostgreSQL Setup
~~~~~~~~~~~~~~~~~

**Ubuntu/Debian:**

.. code-block:: bash

   # Install PostgreSQL
   sudo apt update
   sudo apt install postgresql postgresql-contrib

   # Start and enable PostgreSQL
   sudo systemctl start postgresql
   sudo systemctl enable postgresql

   # Create database and user
   sudo -u postgres psql
   CREATE DATABASE pydance_db;
   CREATE USER pydance_user WITH PASSWORD 'secure_password';
   GRANT ALL PRIVILEGES ON DATABASE pydance_db TO pydance_user;
   \q

**Docker:**

.. code-block:: bash

   # Run PostgreSQL container
   docker run --name pydance-postgres \
       -e POSTGRES_DB=pydance_db \
       -e POSTGRES_USER=pydance_user \
       -e POSTGRES_PASSWORD=secure_password \
       -p 5432:5432 \
       -d postgres:14

MySQL Setup
~~~~~~~~~~~

**Ubuntu/Debian:**

.. code-block:: bash

   # Install MySQL
   sudo apt update
   sudo apt install mysql-server

   # Secure installation
   sudo mysql_secure_installation

   # Create database and user
   sudo mysql
   CREATE DATABASE pydance_db;
   CREATE USER 'pydance_user'@'localhost' IDENTIFIED BY 'secure_password';
   GRANT ALL PRIVILEGES ON pydance_db.* TO 'pydance_user'@'localhost';
   FLUSH PRIVILEGES;
   EXIT;

**Docker:**

.. code-block:: bash

   # Run MySQL container
   docker run --name pydance-mysql \
       -e MYSQL_DATABASE=pydance_db \
       -e MYSQL_USER=pydance_user \
       -e MYSQL_PASSWORD=secure_password \
       -e MYSQL_ROOT_PASSWORD=root_password \
       -p 3306:3306 \
       -d mysql:8

MongoDB Setup
~~~~~~~~~~~~~

**Ubuntu/Debian:**

.. code-block:: bash

   # Install MongoDB
   sudo apt update
   sudo apt install mongodb

   # Start MongoDB
   sudo systemctl start mongodb
   sudo systemctl enable mongodb

   # Create database (MongoDB creates databases automatically)
   mongosh
   use pydance_db
   db.createUser({
     user: "pydance_user",
     pwd: "secure_password",
     roles: ["readWrite"]
   })

**Docker:**

.. code-block:: bash

   # Run MongoDB container
   docker run --name pydance-mongo \
       -e MONGO_INITDB_DATABASE=pydance_db \
       -e MONGO_INITDB_ROOT_USERNAME=pydance_user \
       -e MONGO_INITDB_ROOT_PASSWORD=secure_password \
       -p 27017:27017 \
       -d mongo:6

Redis Setup
~~~~~~~~~~~

**Ubuntu/Debian:**

.. code-block:: bash

   # Install Redis
   sudo apt update
   sudo apt install redis-server

   # Start Redis
   sudo systemctl start redis-server
   sudo systemctl enable redis-server

**Docker:**

.. code-block:: bash

   # Run Redis container
   docker run --name pydance-redis \
       -p 6379:6379 \
       -d redis:7-alpine

Configuration
-------------

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

Create a ``.env`` file in your project root:

.. code-block:: bash

   # Application Settings
   APP_NAME=PydanceApp
   APP_VERSION=1.0.0
   DEBUG=True
   SECRET_KEY=your-super-secret-key-here

   # Database Configuration
   DATABASE_URL=postgresql://user:password@localhost:5432/pydance_db
   # Or for MySQL: mysql://user:password@localhost:3306/pydance_db
   # Or for MongoDB: mongodb://user:password@localhost:27017/pydance_db
   # Or for SQLite: sqlite:///pydance.db

   # Redis Configuration
   REDIS_URL=redis://localhost:6379

   # Session Configuration
   SESSION_SECRET=another-secret-key
   SESSION_TIMEOUT=3600

   # Security Settings
   CSRF_SECRET=csrf-secret-key
   JWT_SECRET=jwt-secret-key

   # Email Configuration (optional)
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password

   # Monitoring (optional)
   SENTRY_DSN=your-sentry-dsn
   LOG_LEVEL=INFO

Configuration File
~~~~~~~~~~~~~~~~~~

Create ``config.py`` in your project root:

.. code-block:: python

   from pydance.config import Config
   import os

   class DevelopmentConfig(Config):
       DEBUG = True
       DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///dev.db')
       LOG_LEVEL = 'DEBUG'

   class ProductionConfig(Config):
       DEBUG = False
       DATABASE_URL = os.getenv('DATABASE_URL')
       LOG_LEVEL = 'WARNING'

       # Security settings
       SESSION_COOKIE_SECURE = True
       SESSION_COOKIE_HTTPONLY = True

   class TestingConfig(Config):
       TESTING = True
       DATABASE_URL = 'sqlite:///:memory:'
       WTF_CSRF_ENABLED = False

   config = {
       'development': DevelopmentConfig,
       'production': ProductionConfig,
       'testing': TestingConfig,
       'default': DevelopmentConfig
   }

Application Structure
--------------------

Recommended Project Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   my-pydance-app/
   ├── app/
   │   ├── __init__.py
   │   ├── models/
   │   │   ├── __init__.py
   │   │   ├── user.py
   │   │   └── article.py
   │   ├── controllers/
   │   │   ├── __init__.py
   │   │   ├── user_controller.py
   │   │   └── article_controller.py
   │   ├── services/
   │   │   ├── __init__.py
   │   │   ├── user_service.py
   │   │   └── email_service.py
   │   ├── middleware/
   │   │   ├── __init__.py
   │   │   └── custom_middleware.py
   │   ├── templates/
   │   │   ├── base.html
   │   │   ├── home.html
   │   │   └── user/
   │   │       └── profile.html
   │   └── static/
   │       ├── css/
   │       ├── js/
   │       └── images/
   ├── migrations/
   │   └── versions/
   ├── tests/
   │   ├── __init__.py
   │   ├── test_models.py
   │   ├── test_controllers.py
   │   └── test_services.py
   ├── config.py
   ├── requirements.txt
   ├── Dockerfile
   ├── docker-compose.yml
   ├── .env
   ├── .gitignore
   └── main.py

Main Application File
~~~~~~~~~~~~~~~~~~~~~

``main.py``:

.. code-block:: python

   from app import create_app
   import os

   def main():
       # Get configuration from environment
       config_name = os.getenv('FLASK_ENV', 'development')

       # Create and configure application
       app = create_app(config_name)

       # Run the application
       app.run(
           host=os.getenv('HOST', '0.0.0.0'),
           port=int(os.getenv('PORT', 8000)),
           debug=config_name == 'development'
       )

   if __name__ == '__main__':
       main()

Application Factory
~~~~~~~~~~~~~~~~~~~

``app/__init__.py``:

.. code-block:: python

   from pydance import Application
   from pydance.core.di import Container
   from .config import config

   def create_app(config_name='development'):
       # Create application
       app = Application(__name__)

       # Load configuration
       config_class = config[config_name]
       app.config.from_object(config_class)

       # Initialize database
       from .models import db
       db.init_app(app)

       # Register blueprints/controllers
       from .controllers import user_controller, article_controller
       app.register_blueprint(user_controller.bp)
       app.register_blueprint(article_controller.bp)

       # Initialize dependency injection
       container = Container()
       container.register_service('user_service', UserService)
       container.register_service('email_service', EmailService)

       # Register middleware
       from .middleware import CustomMiddleware
       app.use(CustomMiddleware())

       return app

Troubleshooting Installation
----------------------------

Common Issues
~~~~~~~~~~~~~

**C Extension Compilation Errors:**

.. code-block:: bash

   # Install build dependencies
   sudo apt install build-essential python3-dev

   # Or on macOS
   xcode-select --install

   # Reinstall Pydance
   pip uninstall pydance
   pip install --no-cache-dir pydance

**Database Connection Issues:**

.. code-block:: python

   # Test database connection
   from pydance.db import create_engine
   from sqlalchemy import text

   engine = create_engine('postgresql://user:pass@localhost/db')
   with engine.connect() as conn:
       result = conn.execute(text('SELECT 1'))
       print("Database connection successful!")

**Import Errors:**

.. code-block:: bash

   # Check Python path
   python -c "import sys; print(sys.path)"

   # Verify installation
   python -c "import pydance; print(pydance.__version__)"

   # Reinstall if necessary
   pip install --force-reinstall --no-deps pydance

**Permission Errors:**

.. code-block:: bash

   # Install in user directory
   pip install --user pydance

   # Or use virtual environment
   python -m venv venv
   source venv/bin/activate
   pip install pydance

Performance Optimization
------------------------

**C Extensions:**

.. code-block:: bash

   # Ensure C extensions are compiled
   pip install pydance[performance]

   # Verify extensions are loaded
   python -c "import pydance.core.extensions; print('Extensions loaded')"

**Database Connection Pooling:**

.. code-block:: python

   from pydance.db import create_engine

   # Configure connection pool
   engine = create_engine(
       'postgresql://user:pass@localhost/db',
       pool_size=10,
       max_overflow=20,
       pool_timeout=30,
       pool_recycle=3600
   )

**Caching Setup:**

.. code-block:: python

   from pydance.cache import Cache

   # Redis cache
   cache = Cache(config={
       'CACHE_TYPE': 'redis',
       'CACHE_REDIS_URL': 'redis://localhost:6379'
   })

   # Use in application
   app.cache = cache

Next Steps
----------

After installation, you can:

1. **Read the Quick Start Guide** to create your first application
2. **Explore the Core Concepts** to understand Pydance architecture
3. **Check out Examples** for real-world usage patterns
4. **Join the Community** for support and contributions

For more detailed information, see the relevant documentation sections.
