Application Architecture Guide
============================

This guide provides comprehensive architectural patterns and best practices for building scalable, maintainable Pydance applications.

Application Structure Patterns
------------------------------

Layered Architecture
~~~~~~~~~~~~~~~~~~~~

Pydance applications follow a clean layered architecture:

.. code-block:: text

   ┌─────────────────┐
   │   Presentation │  ← Controllers, Views, Templates
   │     Layer      │
   ├─────────────────┤
   │   Business     │  ← Services, Domain Logic
   │     Layer      │
   ├─────────────────┤
   │   Data Access  │  ← Models, Repositories
   │     Layer      │
   ├─────────────────┤
   │ Infrastructure │  ← Database, Cache, External APIs
   │     Layer      │
   └─────────────────┘

**Presentation Layer:**

.. code-block:: python

   # controllers/user_controller.py
   from pydance.controllers import Controller
   from pydance.responses import JSONResponse
   from ..services import UserService

   class UserController(Controller):
       def __init__(self, user_service: UserService):
           self.user_service = user_service

       @route('/users', methods=['GET'])
       async def index(self):
           users = await self.user_service.get_all_users()
           return JSONResponse({'users': users})

       @route('/users/{id}', methods=['GET'])
       async def show(self, id: int):
           user = await self.user_service.get_user_by_id(id)
           if not user:
               return JSONResponse({'error': 'User not found'}, status=404)
           return JSONResponse({'user': user})

**Business Layer:**

.. code-block:: python

   # services/user_service.py
   from ..repositories import UserRepository
   from ..domain.user import User

   class UserService:
       def __init__(self, user_repository: UserRepository):
           self.user_repository = user_repository

       async def get_all_users(self) -> List[User]:
           return await self.user_repository.find_all()

       async def get_user_by_id(self, user_id: int) -> Optional[User]:
           return await self.user_repository.find_by_id(user_id)

       async def create_user(self, user_data: dict) -> User:
           user = User(**user_data)
           await user.validate()
           return await self.user_repository.save(user)

**Data Access Layer:**

.. code-block:: python

   # repositories/user_repository.py
   from pydance.models import Model
   from ..domain.user import User

   class UserRepository:
       async def find_all(self) -> List[User]:
           return await User.all()

       async def find_by_id(self, user_id: int) -> Optional[User]:
           return await User.find(user_id)

       async def save(self, user: User) -> User:
           return await user.save()

**Domain Layer:**

.. code-block:: python

   # domain/user.py
   from pydance.domain import Entity
   from pydance.exceptions import ValidationError

   class User(Entity):
       def __init__(self, id=None, username=None, email=None, **kwargs):
           super().__init__(id)
           self.username = username
           self.email = email

       async def validate(self):
           if not self.username or len(self.username) < 3:
               raise ValidationError("Username must be at least 3 characters")
           if not self.email or '@' not in self.email:
               raise ValidationError("Invalid email address")

           # Check uniqueness
           existing = await User.find_by_email(self.email)
           if existing and existing.id != self.id:
               raise ValidationError("Email already exists")

Domain-Driven Design (DDD)
~~~~~~~~~~~~~~~~~~~~~~~~~~

Implementing DDD patterns in Pydance:

**Aggregates:**

.. code-block:: python

   # domain/aggregates/order.py
   from pydance.domain import AggregateRoot
   from .order_item import OrderItem
   from .customer import Customer

   class Order(AggregateRoot):
       def __init__(self, customer: Customer, items: List[OrderItem] = None):
           super().__init__()
           self.customer = customer
           self.items = items or []
           self.status = 'pending'
           self.total = 0.0

       def add_item(self, item: OrderItem):
           self.items.append(item)
           self._recalculate_total()

       def remove_item(self, item_id: str):
           self.items = [item for item in self.items if item.id != item_id]
           self._recalculate_total()

       def confirm(self):
           if not self.items:
               raise ValueError("Cannot confirm empty order")
           self.status = 'confirmed'
           self.add_domain_event(OrderConfirmedEvent(self.id))

       def _recalculate_total(self):
           self.total = sum(item.quantity * item.price for item in self.items)

**Value Objects:**

.. code-block:: python

   # domain/value_objects/money.py
   from pydance.domain import ValueObject

   class Money(ValueObject):
       def __init__(self, amount: float, currency: str = 'USD'):
           self.amount = amount
           self.currency = currency

       def add(self, other: 'Money') -> 'Money':
           if self.currency != other.currency:
               raise ValueError("Cannot add different currencies")
           return Money(self.amount + other.amount, self.currency)

       def multiply(self, factor: float) -> 'Money':
           return Money(self.amount * factor, self.currency)

**Domain Events:**

.. code-block:: python

   # domain/events/order_events.py
   from pydance.domain import DomainEvent

   class OrderConfirmedEvent(DomainEvent):
       def __init__(self, order_id: str):
           super().__init__(order_id)
           self.order_id = order_id

   class OrderShippedEvent(DomainEvent):
       def __init__(self, order_id: str, tracking_number: str):
           super().__init__(order_id)
           self.order_id = order_id
           self.tracking_number = tracking_number

**Domain Services:**

.. code-block:: python

   # domain/services/pricing_service.py
   from .money import Money

   class PricingService:
       def calculate_discount(self, order_total: Money, customer_loyalty_years: int) -> Money:
           discount_rate = min(customer_loyalty_years * 0.01, 0.20)  # Max 20% discount
           return order_total.multiply(discount_rate)

       def calculate_tax(self, subtotal: Money, tax_rate: float) -> Money:
           return subtotal.multiply(tax_rate)

CQRS Pattern
~~~~~~~~~~~~

Command Query Responsibility Segregation:

**Commands:**

.. code-block:: python

   # application/commands/create_order_command.py
   from pydance.cqrs import Command

   class CreateOrderCommand(Command):
       def __init__(self, customer_id: str, items: List[dict]):
           self.customer_id = customer_id
           self.items = items

**Command Handlers:**

.. code-block:: python

   # application/handlers/create_order_handler.py
   from pydance.cqrs import CommandHandler
   from ..commands.create_order_command import CreateOrderCommand
   from ...domain.order import Order

   class CreateOrderCommandHandler(CommandHandler):
       async def handle(self, command: CreateOrderCommand):
           # Create order aggregate
           order = Order(command.customer_id)

           # Add items
           for item_data in command.items:
               order.add_item(OrderItem(**item_data))

           # Save to write database
           await self.order_repository.save(order)

           # Publish domain events
           for event in order.domain_events:
               await self.event_publisher.publish(event)

           return order.id

**Queries:**

.. code-block:: python

   # application/queries/get_order_details_query.py
   from pydance.cqrs import Query

   class GetOrderDetailsQuery(Query):
       def __init__(self, order_id: str):
           self.order_id = order_id

**Query Handlers:**

.. code-block:: python

   # application/handlers/get_order_details_handler.py
   from pydance.cqrs import QueryHandler
   from ..queries.get_order_details_query import GetOrderDetailsQuery

   class GetOrderDetailsQueryHandler(QueryHandler):
       async def handle(self, query: GetOrderDetailsQuery):
           # Read from read database (potentially different schema)
           order_data = await self.read_order_repository.find_by_id(query.order_id)

           # Transform to DTO
           return OrderDetailsDTO.from_dict(order_data)

Microservices Architecture
-------------------------

Service Decomposition
~~~~~~~~~~~~~~~~~~~~~

Strategies for decomposing monolithic applications:

**Business Capability Decomposition:**

.. code-block:: text

   E-commerce Application
   ├── Order Service (Order management, fulfillment)
   ├── Product Service (Catalog, inventory)
   ├── User Service (Authentication, profiles)
   ├── Payment Service (Payment processing)
   ├── Notification Service (Email, SMS)
   ├── Recommendation Service (Product recommendations)

**Subdomain Decomposition:**

.. code-block:: text

   Insurance Application
   ├── Policy Service (Policy management)
   ├── Claims Service (Claims processing)
   ├── Underwriting Service (Risk assessment)
   ├── Billing Service (Premium calculation)
   ├── Document Service (Document management)
   ├── Customer Service (Customer management)

Service Communication Patterns
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Synchronous Communication:**

.. code-block:: python

   # services/order_service.py
   import httpx
   from pydance.microservices import ServiceClient

   class OrderService:
       def __init__(self):
           self.product_client = ServiceClient('product-service')
           self.user_client = ServiceClient('user-service')

       async def create_order(self, order_data):
           # Validate product availability
           product_response = await self.product_client.post(
               '/products/validate-stock',
               json={'items': order_data['items']}
           )

           if not product_response['available']:
               raise ValueError("Insufficient stock")

           # Get user details
           user_response = await self.user_client.get(f"/users/{order_data['user_id']}")

           # Create order
           order = await self.order_repository.create({
               **order_data,
               'user': user_response,
               'status': 'confirmed'
           })

           return order

**Asynchronous Communication:**

.. code-block:: python

   # services/notification_service.py
   from pydance.events import EventPublisher
   from pydance.messaging import MessageBroker

   class NotificationService:
       def __init__(self, event_publisher: EventPublisher, message_broker: MessageBroker):
           self.event_publisher = event_publisher
           self.message_broker = message_broker

           # Subscribe to events
           event_publisher.subscribe('order.created', self.handle_order_created)
           event_publisher.subscribe('payment.completed', self.handle_payment_completed)

       async def handle_order_created(self, event):
           # Send order confirmation email
           await self.send_email(
               event.user_email,
               'Order Confirmation',
               f'Your order {event.order_id} has been created'
           )

       async def handle_payment_completed(self, event):
           # Send payment confirmation
           await self.send_email(
               event.user_email,
               'Payment Confirmed',
               f'Payment for order {event.order_id} has been processed'
           )

       async def send_email(self, to_email: str, subject: str, body: str):
           # Queue email for sending
           await self.message_broker.publish('email_queue', {
               'to': to_email,
               'subject': subject,
               'body': body
           })

API Gateway Pattern
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # gateway/api_gateway.py
   from pydance.gateway import APIGateway
   from pydance.middleware import RateLimitMiddleware, AuthMiddleware

   class EcommerceAPIGateway(APIGateway):
       def __init__(self):
           super().__init__()

           # Configure service routes
           self.add_service_route('order', 'order-service', '/api/orders')
           self.add_service_route('product', 'product-service', '/api/products')
           self.add_service_route('user', 'user-service', '/api/users')

           # Add middleware
           self.use(RateLimitMiddleware(limit='1000/hour'))
           self.use(AuthMiddleware())

       async def handle_request(self, request):
           # Route to appropriate service
           service_name = self.get_service_from_path(request.path)

           if service_name == 'order':
               # Add user context for order service
               request.headers['X-User-ID'] = request.user.id

           elif service_name == 'product':
               # Add caching headers for product service
               request.headers['X-Cache-TTL'] = '300'

           return await super().handle_request(request)

Saga Pattern for Distributed Transactions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # sagas/order_saga.py
   from pydance.saga import Saga, SagaStep
   from pydance.messaging import MessageBroker

   class OrderSaga(Saga):
       def __init__(self, message_broker: MessageBroker):
           super().__init__(message_broker)
           self.order_id = None

       def define_steps(self):
           return [
               SagaStep(
                   name='reserve_inventory',
                   action=self.reserve_inventory,
                   compensation=self.release_inventory
               ),
               SagaStep(
                   name='process_payment',
                   action=self.process_payment,
                   compensation=self.refund_payment
               ),
               SagaStep(
                   name='create_shipment',
                   action=self.create_shipment,
                   compensation=self.cancel_shipment
               ),
               SagaStep(
                   name='send_confirmation',
                   action=self.send_confirmation,
                   compensation=self.send_failure_notification
               )
           ]

       async def reserve_inventory(self, order_data):
           # Call inventory service
           response = await self.call_service('inventory-service', 'reserve', order_data)
           self.inventory_reservation_id = response['reservation_id']
           return response

       async def release_inventory(self, order_data):
           # Compensate inventory reservation
           await self.call_service('inventory-service', 'release', {
               'reservation_id': self.inventory_reservation_id
           })

       async def process_payment(self, order_data):
           # Call payment service
           response = await self.call_service('payment-service', 'charge', {
               'amount': order_data['total'],
               'card_token': order_data['payment_token']
           })
           self.payment_id = response['payment_id']
           return response

       async def refund_payment(self, order_data):
           # Compensate payment
           await self.call_service('payment-service', 'refund', {
               'payment_id': self.payment_id
           })

Circuit Breaker Pattern
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # services/circuit_breaker_client.py
   from pydance.resilience import CircuitBreaker
   import httpx

   class CircuitBreakerClient:
       def __init__(self, service_url: str):
           self.service_url = service_url
           self.circuit_breaker = CircuitBreaker(
               failure_threshold=5,      # Open after 5 failures
               recovery_timeout=60,      # Try to close after 60 seconds
               expected_exception=httpx.HTTPError
           )

       async def call_service(self, endpoint: str, data: dict = None):
           async def service_call():
               async with httpx.AsyncClient() as client:
                   response = await client.post(f"{self.service_url}{endpoint}", json=data)
                   response.raise_for_status()
                   return response.json()

           return await self.circuit_breaker.call(service_call)

Event-Driven Architecture
-------------------------

Event Sourcing
~~~~~~~~~~~~~~

.. code-block:: python

   # eventsourcing/aggregate.py
   from pydance.eventsourcing import EventSourcedAggregate
   from .events import AccountCreated, MoneyDeposited, MoneyWithdrawn

   class BankAccount(EventSourcedAggregate):
       def __init__(self, account_id: str):
           super().__init__(account_id)
           self.balance = 0
           self.owner = None

       def create_account(self, owner: str, initial_balance: float = 0):
           self.apply(AccountCreated(self.id, owner, initial_balance))

       def deposit(self, amount: float):
           if amount <= 0:
               raise ValueError("Deposit amount must be positive")
           self.apply(MoneyDeposited(self.id, amount))

       def withdraw(self, amount: float):
           if amount <= 0:
               raise ValueError("Withdrawal amount must be positive")
           if self.balance < amount:
               raise ValueError("Insufficient funds")
           self.apply(MoneyWithdrawn(self.id, amount))

       def apply_account_created(self, event: AccountCreated):
           self.owner = event.owner
           self.balance = event.initial_balance

       def apply_money_deposited(self, event: MoneyDeposited):
           self.balance += event.amount

       def apply_money_withdrawn(self, event: MoneyWithdrawn):
           self.balance -= event.amount

**Event Store:**

.. code-block:: python

   # eventsourcing/event_store.py
   from pydance.eventsourcing import EventStore
   from typing import List
   import json

   class PostgresEventStore(EventStore):
       def __init__(self, connection_string: str):
           self.connection_string = connection_string

       async def save_events(self, aggregate_id: str, events: List, expected_version: int):
           async with self.get_connection() as conn:
               # Check for concurrency conflicts
               current_version = await self.get_current_version(aggregate_id)
               if current_version != expected_version:
                   raise ConcurrencyException(f"Version conflict for {aggregate_id}")

               # Save events
               for event in events:
                   await conn.execute("""
                       INSERT INTO events (aggregate_id, event_type, event_data, version)
                       VALUES ($1, $2, $3, $4)
                   """, aggregate_id, type(event).__name__, json.dumps(event.__dict__), expected_version)

       async def get_events(self, aggregate_id: str) -> List:
           async with self.get_connection() as conn:
               rows = await conn.fetch("""
                   SELECT event_type, event_data
                   FROM events
                   WHERE aggregate_id = $1
                   ORDER BY version
               """, aggregate_id)

               events = []
               for row in rows:
                   event_class = self.get_event_class(row['event_type'])
                   event_data = json.loads(row['event_data'])
                   events.append(event_class(**event_data))

               return events

Event Streaming
~~~~~~~~~~~~~~~

.. code-block:: python

   # streaming/event_stream.py
   from pydance.streaming import EventStream
   import asyncio

   class OrderEventStream(EventStream):
       def __init__(self):
           super().__init__('orders')
           self.processors = []

       def add_processor(self, processor):
           self.processors.append(processor)

       async def process_event(self, event):
           # Process event with all registered processors
           tasks = []
           for processor in self.processors:
               tasks.append(processor.process(event))

           await asyncio.gather(*tasks)

   # Usage
   order_stream = OrderEventStream()

   # Add processors
   order_stream.add_processor(OrderAnalyticsProcessor())
   order_stream.add_processor(InventoryUpdateProcessor())
   order_stream.add_processor(NotificationProcessor())

   # Publish events
   await order_stream.publish(OrderCreatedEvent(order_id='123'))

Message-Driven Architecture
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # messaging/order_processor.py
   from pydance.messaging import MessageConsumer, MessagePublisher
   from .order_service import OrderService

   class OrderMessageProcessor(MessageConsumer):
       def __init__(self, order_service: OrderService, publisher: MessagePublisher):
           super().__init__('order_commands')
           self.order_service = order_service
           self.publisher = publisher

       async def process_message(self, message):
           try:
               command_type = message['type']

               if command_type == 'create_order':
                   order = await self.order_service.create_order(message['data'])
                   await self.publisher.publish('order_events', {
                       'type': 'order_created',
                       'order_id': order.id,
                       'user_id': order.user_id
                   })

               elif command_type == 'cancel_order':
                   await self.order_service.cancel_order(message['order_id'])
                   await self.publisher.publish('order_events', {
                       'type': 'order_cancelled',
                       'order_id': message['order_id']
                   })

               # Acknowledge successful processing
               await self.acknowledge(message)

           except Exception as e:
               # Handle processing errors
               await self.reject(message, str(e))

Scalability Patterns
--------------------

Database Sharding
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # sharding/user_shard_manager.py
   from pydance.sharding import ShardManager

   class UserShardManager(ShardManager):
       def __init__(self):
           super().__init__(num_shards=4)

       def get_shard_key(self, user_id: str) -> int:
           # Simple hash-based sharding
           return hash(user_id) % self.num_shards

       def get_shard_for_user(self, user_id: str) -> str:
           shard_id = self.get_shard_key(user_id)
           return f"user_shard_{shard_id}"

   # Usage
   shard_manager = UserShardManager()

   # Route queries to appropriate shard
   user_id = "user_123"
   shard = shard_manager.get_shard_for_user(user_id)

   # Execute query on specific shard
   user_data = await database.query_on_shard(shard, "SELECT * FROM users WHERE id = ?", user_id)

Read Replicas
~~~~~~~~~~~~~

.. code-block:: python

   # replication/read_replica_manager.py
   from pydance.replication import ReadReplicaManager
   import random

   class PostgreSQLReadReplicaManager(ReadReplicaManager):
       def __init__(self, master_url: str, replica_urls: List[str]):
           super().__init__(master_url, replica_urls)

       def get_read_connection(self) -> str:
           # Round-robin load balancing
           if not hasattr(self, '_replica_index'):
               self._replica_index = 0

           replica_url = self.replica_urls[self._replica_index]
           self._replica_index = (self._replica_index + 1) % len(self.replica_urls)
           return replica_url

       async def execute_read_query(self, query: str, params: tuple = None):
           connection_url = self.get_read_connection()
           return await self.execute_on_connection(connection_url, query, params)

       async def execute_write_query(self, query: str, params: tuple = None):
           # Always use master for writes
           return await self.execute_on_connection(self.master_url, query, params)

Caching Strategies
~~~~~~~~~~~~~~~~~~

**Multi-Level Caching:**

.. code-block:: python

   # caching/multi_level_cache.py
   from pydance.caching import CacheManager, MemoryCache, RedisCache, DatabaseCache

   class MultiLevelCache(CacheManager):
       def __init__(self):
           super().__init__()

           # L1: In-memory cache (fastest, smallest)
           self.l1_cache = MemoryCache(max_size=10000, ttl=60)

           # L2: Redis cache (medium speed, larger)
           self.l2_cache = RedisCache(ttl=3600)

           # L3: Database cache (slowest, largest)
           self.l3_cache = DatabaseCache(ttl=86400)

       async def get(self, key: str):
           # Try L1 cache first
           value = await self.l1_cache.get(key)
           if value is not None:
               return value

           # Try L2 cache
           value = await self.l2_cache.get(key)
           if value is not None:
               # Populate L1 cache
               await self.l1_cache.set(key, value)
               return value

           # Try L3 cache
           value = await self.l3_cache.get(key)
           if value is not None:
               # Populate L1 and L2 caches
               await self.l1_cache.set(key, value)
               await self.l2_cache.set(key, value)
               return value

           return None

       async def set(self, key: str, value, ttl: int = None):
           # Set in all levels
           await self.l1_cache.set(key, value, ttl=min(ttl or 3600, 60))  # L1 has shorter TTL
           await self.l2_cache.set(key, value, ttl=ttl)
           await self.l3_cache.set(key, value, ttl=ttl)

**Cache-Aside Pattern:**

.. code-block:: python

   # caching/cache_aside_service.py
   from pydance.caching import Cache

   class CacheAsideService:
       def __init__(self, cache: Cache, repository):
           self.cache = cache
           self.repository = repository

       async def get_user(self, user_id: str):
           # Try cache first
           cache_key = f"user:{user_id}"
           user = await self.cache.get(cache_key)

           if user is None:
               # Cache miss - fetch from database
               user = await self.repository.find_by_id(user_id)

               if user:
                   # Populate cache
                   await self.cache.set(cache_key, user, ttl=3600)

           return user

       async def update_user(self, user_id: str, user_data: dict):
           # Update database first
           updated_user = await self.repository.update(user_id, user_data)

           if updated_user:
               # Update cache
               cache_key = f"user:{user_id}"
               await self.cache.set(cache_key, updated_user, ttl=3600)

           return updated_user

       async def delete_user(self, user_id: str):
           # Delete from database
           deleted = await self.repository.delete(user_id)

           if deleted:
               # Remove from cache
               cache_key = f"user:{user_id}"
               await self.cache.delete(cache_key)

           return deleted

Load Balancing
~~~~~~~~~~~~~~

.. code-block:: python

   # loadbalancing/load_balancer.py
   from pydance.loadbalancing import LoadBalancer
   import random

   class RoundRobinLoadBalancer(LoadBalancer):
       def __init__(self, servers: List[str]):
           super().__init__(servers)
           self.current_index = 0

       def get_next_server(self) -> str:
           server = self.servers[self.current_index]
           self.current_index = (self.current_index + 1) % len(self.servers)
           return server

   class LeastConnectionsLoadBalancer(LoadBalancer):
       def __init__(self, servers: List[str]):
           super().__init__(servers)
           self.connections = {server: 0 for server in servers}

       def get_next_server(self) -> str:
           # Find server with least connections
           server = min(self.connections.keys(), key=lambda s: self.connections[s])
           self.connections[server] += 1
           return server

       def release_connection(self, server: str):
           if server in self.connections:
               self.connections[server] = max(0, self.connections[server] - 1)

   # Usage
   load_balancer = LeastConnectionsLoadBalancer([
       'app-server-1:8000',
       'app-server-2:8000',
       'app-server-3:8000'
   ])

   # Route request to least loaded server
   server = load_balancer.get_next_server()
   response = await make_request(server, request)

   # Release connection when done
   load_balancer.release_connection(server)

This comprehensive architecture guide provides the foundation for building scalable, maintainable Pydance applications using proven patterns and best practices.
