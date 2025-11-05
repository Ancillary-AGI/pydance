Pydance Framework Documentation
===============================

.. image:: https://img.shields.io/badge/Pydance-Web--Framework-blue?style=for-the-badge
   :alt: Pydance Framework
.. image:: https://img.shields.io/badge/Python-3.8+-green?style=flat-square
   :alt: Python 3.8+
.. image:: https://img.shields.io/badge/License-MIT-red?style=flat-square
   :alt: MIT License

**Pydance** is a modern, enterprise-grade Python web framework with ASGI support, comprehensive middleware system, database ORM, and advanced features for building scalable web applications and microservices.

🎯 **Framework Status: Production Ready**

The Pydance framework has been completely refactored with a modern architecture that provides enterprise-grade features while maintaining simplicity and developer experience.

Overview
--------

Pydance provides a complete web development ecosystem:

🚀 **Core Features**
   - **ASGI-compliant** web applications with high-performance C/C++ extensions
   - **Advanced middleware system** with flexible configuration and priorities
   - **Database ORM** with multiple backend support (SQLite, PostgreSQL, MySQL, MongoDB)
   - **Template engine** with Jinja2 integration and custom Lean template language
   - **Session management** with multiple storage backends and encryption
   - **WebSocket support** for real-time applications
   - **GraphQL API** support with schema management
   - **RESTful API** generation tools

🔒 **Security Features**
   - **Enterprise security layer** with multi-method authentication
   - **CSRF protection** middleware with customizable tokens
   - **Session security** with AES-256 encryption and integrity verification
   - **Input validation** and sanitization with comprehensive error handling
   - **Rate limiting** with multiple algorithms (fixed window, sliding window, token bucket)
   - **Security headers** middleware with CSP, HSTS, and other protections

🏗️ **Architecture**
   - **MVC pattern** support with clean separation of concerns
   - **Dependency injection** container with service registration and resolution
   - **Plugin system** for extensibility and modular development
   - **Event-driven architecture** with publish-subscribe messaging
   - **Microservices architecture** support with service discovery
   - **Database migrations** with schema versioning and rollback

⚡ **Performance Features**
   - **C/C++ HTTP server** with epoll/kqueue support for maximum performance
   - **SIMD-optimized** cryptographic operations
   - **Memory pooling** and efficient resource management
   - **Connection pooling** for database and external services
   - **Advanced caching** with multiple backends (Redis, Memcached, in-memory)
   - **Real-time monitoring** and performance metrics

Quick Start
-----------

Installation
~~~~~~~~~~~~

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

Basic Application
~~~~~~~~~~~~~~~~~

**Simple HTTP Server:**

.. code-block:: python

   from pydance import Application

   # Create application
   app = Application()

   # Add routes
   @app.route('/')
   async def home(request):
       return {'message': 'Hello, World!', 'framework': 'Pydance'}

   @app.route('/api/users', methods=['POST'])
   async def create_user(request):
       data = await request.json()
       # Process user creation logic here
       return {'user': data, 'status': 'created'}, 201

   @app.route('/api/users/{user_id}', methods=['GET'])
   async def get_user(request, user_id: int):
       # Fetch user by ID
       return {'user_id': user_id, 'name': 'John Doe'}

   # Start server
   if __name__ == '__main__':
       app.run(host='0.0.0.0', port=8000)

**MVC Application:**

.. code-block:: python

   from pydance.controllers import Controller
   from pydance.models import Model, Field
   from pydance.views import TemplateView
   from pydance import Application

   # Define model
   class User(Model):
       __table__ = 'users'

       id = Field(int, primary_key=True)
       username = Field(str, unique=True, max_length=50)
       email = Field(str, unique=True)
       created_at = Field(datetime, default=datetime.utcnow)

   # Define controller
   class UserController(Controller):
       @route('/users', methods=['GET'])
       async def index(self):
           users = await User.all()
           return self.json({'users': users})

       @route('/users', methods=['POST'])
       async def create(self):
           data = await self.request.json()
           user = await User.create(data)
           return self.json({'user': user}, status_code=201)

       @route('/users/{id}', methods=['GET'])
       async def show(self, id: int):
           user = await User.find(id)
           if not user:
               return self.not_found({'error': 'User not found'})
           return self.json({'user': user})

   # Define view
   class HomeView(TemplateView):
       template_name = 'home.html'

       def get_context_data(self, **kwargs):
           context = super().get_context_data(**kwargs)
           context['title'] = 'Welcome to Pydance'
           context['framework_version'] = '1.0.0'
           return context

   # Create application
   app = Application()

   # Register routes
   UserController.register_routes(app)
   app.add_route('/', HomeView.as_view())

   # Run application
   if __name__ == "__main__":
       app.run()

Advanced Features
-----------------

**Dependency Injection:**

.. code-block:: python

   from pydance.core.di import Container, service, inject
   from pydance import Application

   # Define services
   @service()
   class UserService:
       def get_user(self, user_id: int):
           # Database logic here
           return {'id': user_id, 'name': 'John Doe'}

   @service()
   class EmailService:
       def send_welcome_email(self, email: str):
           # Email sending logic here
           print(f"Sending welcome email to {email}")

   # Inject services into controller
   class UserController(Controller):
       @inject
       def __init__(self, user_service: UserService, email_service: EmailService):
           self.user_service = user_service
           self.email_service = email_service

       @route('/users/{id}', methods=['GET'])
       async def show(self, id: int):
           user = self.user_service.get_user(id)
           return self.json({'user': user})

**Middleware System:**

.. code-block:: python

   from pydance.middleware.base import HTTPMiddleware
   from pydance import Application

   class LoggingMiddleware(HTTPMiddleware):
       async def process_request(self, request):
           print(f"Request: {request.method} {request.path}")
           return request

       async def process_response(self, request, response):
           print(f"Response: {response.status_code}")
           return response

   class AuthMiddleware(HTTPMiddleware):
       async def process_request(self, request):
           auth_header = request.headers.get('authorization')
           if not auth_header:
               from pydance.exceptions import Unauthorized
               raise Unauthorized("Authentication required")
           return request

   # Create application with middleware
   app = Application()

   # Add middleware with priorities
   app.use(LoggingMiddleware(), priority=1)  # Execute first
   app.use(AuthMiddleware(), priority=2)     # Execute second

**Database Operations:**

.. code-block:: python

   from pydance.models import Model, Field
   from pydance.db.connections import DatabaseConnection
   from pydance import Application

   # Define model
   class Article(Model):
       __table__ = 'articles'

       id = Field(int, primary_key=True, auto_increment=True)
       title = Field(str, max_length=200)
       content = Field(str)
       author_id = Field(int)
       published = Field(bool, default=False)
       created_at = Field(datetime, default=datetime.utcnow)

       # Define relationships
       author = Relationship(User, foreign_key='author_id')

   # Usage in controller
   class ArticleController(Controller):
       @route('/articles', methods=['GET'])
       async def index(self):
           # Query with filters and relationships
           articles = await Article.filter(published=True).order_by('-created_at').limit(10)
           return self.json({'articles': articles})

       @route('/articles', methods=['POST'])
       async def create(self):
           data = await self.request.json()

           # Create with validation
           article = await Article.create(data)

           # Load relationships
           await article.load('author')

           return self.json({'article': article}, status_code=201)

       @route('/articles/{id}', methods=['PUT'])
       async def update(self, id: int):
           data = await self.request.json()
           article = await Article.find(id)

           if not article:
               return self.not_found({'error': 'Article not found'})

           # Update with validation
           await article.update(data)
           return self.json({'article': article})

**Template Engine:**

.. code-block:: python

   from pydance.templating.engine import TemplateEngine
   from pydance.views import TemplateView

   # Using Lean template engine
   class ArticleView(TemplateView):
       template_name = 'article.html'

       async def get_context_data(self, **kwargs):
           context = await super().get_context_data(**kwargs)
           article_id = kwargs.get('id')
           article = await Article.find(article_id)

           if not article:
               raise NotFound()

           context.update({
               'article': article,
               'title': article.title,
               'author': await article.author,
               'related_articles': await Article.filter(published=True).exclude(id=article.id).limit(5)
           })

           return context

   # article.html (Lean template)
   <!-- Article template -->
   <div class="article">
       <h1>{{ article.title }}</h1>
       <div class="meta">
           By {{ author.name }} on {{ article.created_at|date:'M j, Y' }}
       </div>
       <div class="content">
           {{ article.content|safe }}
       </div>

       {% if related_articles %}
       <div class="related">
           <h3>Related Articles</h3>
           <ul>
           {% for related in related_articles %}
               <li><a href="/articles/{{ related.id }}">{{ related.title }}</a></li>
           {% endfor %}
           </ul>
       </div>
       {% endif %}
   </div>

**GraphQL API:**

.. code-block:: python

   from pydance.graphql import Schema, Query, Mutation, ObjectType, Field, String, Int, List
   from pydance import Application

   # Define GraphQL types
   class UserType(ObjectType):
       def __init__(self):
           super().__init__('User', {
               'id': Field(Int()),
               'username': Field(String()),
               'email': Field(String()),
               'articles': Field(List(ArticleType), resolver=self.resolve_articles)
           })

       async def resolve_articles(self, parent, info):
           return await Article.filter(author_id=parent['id'])

   class ArticleType(ObjectType):
       def __init__(self):
           super().__init__('Article', {
               'id': Field(Int()),
               'title': Field(String()),
               'content': Field(String()),
               'author': Field(UserType, resolver=self.resolve_author)
           })

       async def resolve_author(self, parent, info):
           return await User.find(parent['author_id'])

   # Define queries
   class QueryType(Query):
       def __init__(self):
           super().__init__({
               'users': Field(List(UserType), resolver=self.resolve_users),
               'user': Field(UserType, args={'id': Int()}, resolver=self.resolve_user),
               'articles': Field(List(ArticleType), resolver=self.resolve_articles),
               'article': Field(ArticleType, args={'id': Int()}, resolver=self.resolve_article)
           })

       async def resolve_users(self, parent, info):
           return await User.all()

       async def resolve_user(self, parent, info, id):
           return await User.find(id)

       async def resolve_articles(self, parent, info):
           return await Article.all()

       async def resolve_article(self, parent, info, id):
           return await Article.find(id)

   # Define mutations
   class MutationType(Mutation):
       def __init__(self):
           super().__init__({
               'create_user': Field(UserType, args={
                   'username': String(),
                   'email': String()
               }, resolver=self.resolve_create_user)
           })

       async def resolve_create_user(self, parent, info, username, email):
           user_data = {'username': username, 'email': email}
           user = await User.create(user_data)
           return user

   # Create schema
   schema = Schema(query=QueryType(), mutation=MutationType())

   # Add to application
   app = Application()
   app.add_graphql_route('/graphql', schema)

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: 🚀 Getting Started:

   installation
   quickstart
   configuration

.. toctree::
   :maxdepth: 2
   :caption: 🏗️ Architecture & Design:

   architecture

.. toctree::
   :maxdepth: 2
   :caption: 📚 Core Concepts:

   application
   routing
   middleware
   dependency-injection
   models
   controllers
   views
   database
   templates

.. toctree::
   :maxdepth: 2
   :caption: ⚡ Advanced Features:

   sessions
   authentication
   authorization
   graphql
   websockets
   caching
   monitoring
   security
   deployment
   performance
   scaling

.. toctree::
   :maxdepth: 2
   :caption: 🔧 Development Tools:

   testing
   debugging
   profiling
   cli-tools

.. toctree::
   :maxdepth: 2
   :caption: 📖 API Reference:

   api-core
   api-database
   api-security
   api-middleware

.. toctree::
   :maxdepth: 2
   :caption: 🌐 Ecosystem:

   pydance-client
   plugins
   extensions
   integrations

.. toctree::
   :maxdepth: 2
   :caption: 📋 Best Practices:

   best-practices
   security-guide
   performance-guide
   deployment-guide

.. toctree::
   :maxdepth: 2
   :caption: ❓ Troubleshooting:

   faq
   common-issues
   migration-guide

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
