Quick Start Guide
=================

This guide will get you up and running with Pydance in minutes. We'll cover installation, basic usage, and some advanced features.

Installation
------------

**Basic Installation:**

.. code-block:: bash

   pip install pydance

**With All Features:**

.. code-block:: bash

   pip install pydance[full]

**From Source (with C extensions):**

.. code-block:: bash

   git clone https://github.com/ancillary-ai/pydance.git
   cd pydance
   pip install -e .[dev,security,performance,database,web3,monitoring]

Your First Application
----------------------

Let's create a simple "Hello World" application:

.. code-block:: python

   # app.py
   from pydance import Application

   # Create application
   app = Application()

   # Add a route
   @app.route('/')
   async def home(request):
       return {'message': 'Hello, World!', 'framework': 'Pydance'}

   # Add another route with parameters
   @app.route('/greet/{name}')
   async def greet(request, name: str):
       return {'greeting': f'Hello, {name}!', 'timestamp': request.query_params.get('time')}

   # Start the server
   if __name__ == '__main__':
       app.run()

Run the application:

.. code-block:: bash

   python app.py

Visit http://localhost:8000/ and http://localhost:8000/greet/Alice to see your app in action!

Working with JSON
-----------------

Pydance makes it easy to work with JSON data:

.. code-block:: python

   from pydance import Application

   app = Application()

   @app.route('/api/users', methods=['POST'])
   async def create_user(request):
       # Parse JSON data
       user_data = await request.json()

       # Validate data (basic example)
       if not user_data.get('name'):
           return {'error': 'Name is required'}, 400

       # Process data
       user = {
           'id': 1,
           'name': user_data['name'],
           'email': user_data.get('email'),
           'created': True
       }

       return user, 201

   @app.route('/api/users/{user_id}', methods=['GET'])
   async def get_user(request, user_id: int):
       # Simulate database lookup
       users = {
           1: {'id': 1, 'name': 'Alice', 'email': 'alice@example.com'},
           2: {'id': 2, 'name': 'Bob', 'email': 'bob@example.com'}
       }

       user = users.get(user_id)
       if not user:
           return {'error': 'User not found'}, 404

       return user

Working with Templates
----------------------

Pydance includes a powerful template engine:

.. code-block:: python

   from pydance import Application
   from pydance.views import TemplateView

   app = Application()

   class HomeView(TemplateView):
       template_name = 'home.html'

       def get_context_data(self, **kwargs):
           context = super().get_context_data(**kwargs)
           context.update({
               'title': 'Welcome to Pydance',
               'users': ['Alice', 'Bob', 'Charlie'],
               'current_year': 2025
           })
           return context

   # Add the view
   app.add_route('/', HomeView.as_view())

Create the template file ``templates/home.html``:

.. code-block:: html

   <!DOCTYPE html>
   <html>
   <head>
       <title>{{ title }}</title>
       <style>
           body { font-family: Arial, sans-serif; margin: 40px; }
           .user-list { background: #f0f0f0; padding: 20px; border-radius: 8px; }
       </style>
   </head>
   <body>
       <h1>{{ title }}</h1>
       <p>Welcome to the Pydance framework! Current year: {{ current_year }}</p>

       <div class="user-list">
           <h2>Users:</h2>
           <ul>
           {% for user in users %}
               <li>{{ user }}</li>
           {% endfor %}
           </ul>
       </div>
   </body>
   </html>

Database Integration
--------------------

Pydance includes a powerful ORM:

.. code-block:: python

   from pydance import Application
   from pydance.models import Model, Field
   from datetime import datetime

   # Define a model
   class User(Model):
       __table__ = 'users'

       id = Field(int, primary_key=True, auto_increment=True)
       username = Field(str, unique=True, max_length=50)
       email = Field(str, unique=True)
       created_at = Field(datetime, default=datetime.utcnow)

   app = Application()

   @app.route('/users', methods=['GET'])
   async def list_users(request):
       users = await User.all()
       return {'users': users}

   @app.route('/users', methods=['POST'])
   async def create_user(request):
       data = await request.json()
       user = await User.create(data)
       return {'user': user}, 201

   @app.route('/users/{user_id}', methods=['GET'])
   async def get_user(request, user_id: int):
       user = await User.find(user_id)
       if not user:
           return {'error': 'User not found'}, 404
       return {'user': user}

Middleware
----------

Add cross-cutting concerns with middleware:

.. code-block:: python

   from pydance import Application
   from pydance.middleware.base import HTTPMiddleware

   class LoggingMiddleware(HTTPMiddleware):
       async def process_request(self, request):
           print(f"Request: {request.method} {request.path}")
           return request

       async def process_response(self, request, response):
           print(f"Response: {response.status_code}")
           return response

   class CORSMiddleware(HTTPMiddleware):
       async def process_response(self, request, response):
           response.headers['Access-Control-Allow-Origin'] = '*'
           response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE'
           response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
           return response

   app = Application()

   # Add middleware
   app.use(LoggingMiddleware())
   app.use(CORSMiddleware())

Configuration
-------------

Configure your application using environment variables or settings:

.. code-block:: python

   # settings.py or via environment variables
   import os

   # Basic configuration
   DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
   SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')

   # Database configuration
   DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///app.db')

   # Server configuration
   HOST = os.getenv('HOST', '0.0.0.0')
   PORT = int(os.getenv('PORT', '8000'))

   # Template configuration
   TEMPLATES_DIRS = ['templates']
   TEMPLATE_ENGINE = 'pydance.templating.languages.lean.LeanTemplateEngine'

Create a ``.env`` file:

.. code-block:: bash

   DEBUG=True
   SECRET_KEY=your-super-secret-key-change-in-production
   DATABASE_URL=sqlite:///app.db
   HOST=0.0.0.0
   PORT=8000

Advanced Routing
----------------

Pydance supports advanced routing patterns:

.. code-block:: python

   from pydance import Application

   app = Application()

   # Basic routes
   @app.route('/')
   async def home(request):
       return {'page': 'home'}

   # Routes with parameters
   @app.route('/users/{user_id}')
   async def user_profile(request, user_id: int):
       return {'user_id': user_id}

   # Routes with multiple parameters
   @app.route('/posts/{year}/{month}/{slug}')
   async def blog_post(request, year: int, month: int, slug: str):
       return {
           'year': year,
           'month': month,
           'slug': slug
       }

   # Routes with query parameters
   @app.route('/search')
   async def search(request):
       query = request.query_params.get('q', '')
       limit = int(request.query_params.get('limit', '10'))
       return {
           'query': query,
           'limit': limit,
           'results': []  # Your search logic here
       }

   # Routes with specific HTTP methods
   @app.route('/api/data', methods=['GET', 'POST'])
   async def api_data(request):
       if request.method == 'GET':
           return {'data': 'GET request'}
       elif request.method == 'POST':
           data = await request.json()
           return {'received': data}, 201

   # WebSocket routes
   @app.websocket_route('/ws/chat')
   async def chat_websocket(websocket):
       await websocket.accept()
       await websocket.send_json({'message': 'Connected to chat'})

       try:
           while True:
               data = await websocket.receive_json()
               await websocket.send_json({'echo': data})
       except Exception:
           pass

Error Handling
--------------

Handle errors gracefully:

.. code-block:: python

   from pydance import Application
   from pydance.exceptions import HTTPException, ValidationError

   app = Application()

   @app.exception_handler(ValidationError)
   async def handle_validation_error(exc: ValidationError):
       return {
           'error': 'Validation failed',
           'details': exc.details
       }, 400

   @app.exception_handler(HTTPException)
   async def handle_http_error(exc: HTTPException):
       return {
           'error': exc.detail,
           'status_code': exc.status_code
       }, exc.status_code

   @app.route('/api/test-error')
   async def test_error(request):
       # Simulate an error
       raise ValidationError('This is a test validation error')

Static Files
------------

Serve static files:

.. code-block:: python

   from pydance import Application
   from pydance.static import StaticFiles

   app = Application()

   # Serve static files from 'static' directory at '/static' URL
   app.mount('/static', StaticFiles(directory='static'))

   # Or serve from multiple directories
   app.mount('/assets', StaticFiles(directory='assets'))
   app.mount('/uploads', StaticFiles(directory='uploads'))

Testing Your Application
------------------------

Pydance includes testing utilities:

.. code-block:: python

   import pytest
   from pydance.test import TestClient

   def test_home_page():
       client = TestClient(app)

       response = client.get('/')
       assert response.status_code == 200
       assert 'message' in response.json()

   def test_create_user():
       client = TestClient(app)

       user_data = {'name': 'Test User', 'email': 'test@example.com'}
       response = client.post('/api/users', json=user_data)

       assert response.status_code == 201
       assert response.json()['name'] == 'Test User'

   def test_user_not_found():
       client = TestClient(app)

       response = client.get('/api/users/999')
       assert response.status_code == 404
       assert 'error' in response.json()

Run tests:

.. code-block:: bash

   pytest test_app.py -v

Deployment
----------

Deploy your Pydance application:

**Using Gunicorn (recommended for production):**

.. code-block:: bash

   pip install gunicorn
   gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker

**Using Uvicorn directly:**

.. code-block:: bash

   pip install uvicorn
   uvicorn app:app --host 0.0.0.0 --port 8000

**Docker deployment:**

.. code-block:: dockerfile

   FROM python:3.11-slim

   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt

   COPY . .
   EXPOSE 8000

   CMD ["gunicorn", "app:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker"]

Next Steps
----------

Now that you have a basic Pydance application running, you can explore:

- :doc:`middleware` - Learn about middleware and request processing
- :doc:`database` - Deep dive into the ORM and database operations
- :doc:`templates` - Master the template engine
- :doc:`authentication` - Add user authentication
- :doc:`graphql` - Build GraphQL APIs
- :doc:`deployment` - Deploy to production

Check out the :doc:`api` reference for detailed API documentation.

Happy coding with Pydance! 🚀
