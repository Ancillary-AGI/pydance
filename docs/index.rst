Pydance Documentation
=====================

Welcome to Pydance, a modern Python web framework with ASGI support, middleware system, and database ORM.

Overview
--------

Pydance is a production-ready web framework that provides:

- **ASGI-compliant** web applications
- **Middleware system** with flexible configuration
- **Database ORM** with multiple backend support
- **Template engine** with Jinja2 integration
- **Session management** with multiple storage backends
- **WebSocket support** for real-time applications

Quick Start
-----------

Installation
~~~~~~~~~~~~

.. code-block:: bash

   pip install pydance

Basic Application
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pydance import Application

   app = Application()

   @app.route('/')
   async def hello(request):
       return {'message': 'Hello, World!'}

   @app.route('/users', methods=['POST'])
   async def create_user(request):
       data = await request.json()
       return {'user': data, 'status': 'created'}, 201

   if __name__ == '__main__':
       app.run()

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: User Guide:

   installation
   quickstart
   middleware
   database
   templates
   deployment

.. toctree::
   :maxdepth: 2
   :caption: API Reference:

   api

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`