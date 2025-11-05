@pydance/client Documentation
===========================

.. image:: https://img.shields.io/npm/v/@pydance/client.svg
   :alt: npm version
.. image:: https://img.shields.io/npm/dm/@pydance/client.svg
   :alt: npm downloads
.. image:: https://img.shields.io/bundlephobia/minzip/@pydance/client
   :alt: bundle size

**@pydance/client** is the official frontend framework for Pydance applications, providing a modern, signal-based reactive framework with JSX support and seamless backend integration.

Overview
--------

@pydance/client is designed specifically for Pydance backend applications, offering:

- **Ultra-lightweight**: ~3-8KB gzipped core runtime
- **Signal-based reactivity**: Fine-grained, automatic dependency tracking
- **Modern JSX runtime**: Optimized JSX with full TypeScript support
- **Function components**: Hooks-based component system
- **SSR integration**: Server-side rendering support
- **Performance monitoring**: Built-in real-time metrics
- **Zero external dependencies**: Completely standalone

Installation
------------

.. code-block:: bash

   npm install @pydance/client

   # or with yarn
   yarn add @pydance/client

   # or with pnpm
   pnpm add @pydance/client

Quick Start
-----------

Create your first @pydance/client application:

.. code-block:: javascript

   import { createComponent, signal, useState, jsx } from '@pydance/client';

   // Create a reactive signal
   const count = signal(0);

   // Create a component
   const Counter = createComponent(() => {
     const [state, setState] = useState({ name: 'World' });

     return jsx('div', {
       className: 'counter',
       children: [
         jsx('h1', {
           children: [`Hello ${state.name}!`]
         }),
         jsx('p', {
           children: [`Count: ${count.value}`]
         }),
         jsx('button', {
           onClick: () => count.value++,
           children: 'Increment'
         }),
         jsx('button', {
           onClick: () => setState(prev => ({ ...prev, name: 'Pydance' })),
           children: 'Change Name'
         })
       ]
     });
   });

   // Mount the component
   const app = new Counter();
   app.mount('#app');

Core Concepts
-------------

Signals
~~~~~~~

Signals are the foundation of @pydance/client's reactivity system:

.. code-block:: javascript

   import { signal, computed, effect } from '@pydance/client';

   // Create a signal
   const name = signal('Pydance');
   const age = signal(1);

   // Create a computed signal
   const description = computed(() => `${name.value} is ${age.value} years old`);

   // Create an effect
   effect(() => {
     console.log(description.value);
   });

   // Update signals (triggers reactivity)
   name.value = 'Pydance Client';
   age.value = 2;

Components
~~~~~~~~~~

Function-based components with hooks:

.. code-block:: javascript

   import { createComponent, useState, useEffect } from '@pydance/client';

   const Timer = createComponent(() => {
     const [time, setTime] = useState(0);

     useEffect(() => {
       const interval = setInterval(() => {
         setTime(prev => prev + 1);
       }, 1000);

       return () => clearInterval(interval);
     }, []);

     return jsx('div', {
       children: `Time: ${time}s`
     });
   });

JSX Runtime
~~~~~~~~~~~

Modern JSX with optimized runtime:

.. code-block:: javascript

   import { jsx, jsxs, Fragment } from '@pydance/client';

   // JSX Elements
   const element = jsx('div', {
     className: 'container',
     children: jsx('h1', { children: 'Hello World' })
   });

   // JSX Fragments
   const fragment = jsx(Fragment, {
     children: [
       jsx('h1', { children: 'Title' }),
       jsx('p', { children: 'Description' })
     ]
   });

Hooks
~~~~~

@pydance/client provides essential React-like hooks:

**useState**

.. code-block:: javascript

   import { createComponent, useState } from '@pydance/client';

   const Counter = createComponent(() => {
     const [count, setCount] = useState(0);

     return jsx('div', {
       children: [
         jsx('p', { children: `Count: ${count}` }),
         jsx('button', {
           onClick: () => setCount(count + 1),
           children: 'Increment'
         })
       ]
     });
   });

**useEffect**

.. code-block:: javascript

   import { createComponent, useEffect } from '@pydance/client';

   const DataFetcher = createComponent(() => {
     const [data, setData] = useState(null);

     useEffect(() => {
       fetch('/api/data')
         .then(res => res.json())
         .then(setData);
     }, []); // Empty dependency array = run once

     return jsx('div', {
       children: data ? `Data: ${JSON.stringify(data)}` : 'Loading...'
     });
   });

**useMemo**

.. code-block:: javascript

   import { createComponent, useMemo } from '@pydance/client';

   const ExpensiveComponent = createComponent(() => {
     const [count, setCount] = useState(0);

     const expensiveValue = useMemo(() => {
       console.log('Computing expensive value...');
       return count * 2;
     }, [count]); // Only recompute when count changes

     return jsx('div', {
       children: `Expensive value: ${expensiveValue}`
     });
   });

**useCallback**

.. code-block:: javascript

   import { createComponent, useCallback } from '@pydance/client';

   const ButtonComponent = createComponent(() => {
     const handleClick = useCallback(() => {
       console.log('Button clicked');
     }, []); // Stable reference

     return jsx('button', {
       onClick: handleClick,
       children: 'Click me'
     });
   });

Advanced Features
-----------------

Server-Side Rendering (SSR)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

@pydance/client supports server-side rendering with Pydance backend:

.. code-block:: javascript

   import { createSSRComponent, hydrate } from '@pydance/client';

   // Server-side component
   const ServerComponent = createSSRComponent(() => {
     const [data, setData] = useState(window.__SSR_DATA__ || []);

     return jsx('div', {
       children: data.map(item =>
         jsx('div', { key: item.id, children: item.title })
       )
     });
   });

   // Client-side hydration
   if (typeof window !== 'undefined') {
     const app = new ServerComponent();
     hydrate(app, '#app');
   }

Examples
--------

Complete Todo Application
~~~~~~~~~~~~~~~~~~~~~~~~~

A comprehensive example showing signals, computed values, context, JSX, and component lifecycle:

.. code-block:: javascript

   import { createComponent, signal, computed, jsx, useState, useEffect, Context } from '@pydance/client';

   // Create a theme context
   const ThemeContext = new Context('light');

   // Todo App Component
   const TodoApp = createComponent(() => {
     const [todos, setTodos] = useState([]);
     const [filter, setFilter] = useState('all');
     const [newTodo, setNewTodo] = useState('');
     const [theme, setTheme] = useState('light');

     // Computed values
     const filteredTodos = computed(() => {
       switch (filter) {
         case 'active':
           return todos.filter(todo => !todo.completed);
         case 'completed':
           return todos.filter(todo => todo.completed);
         default:
           return todos;
       }
     });

     const stats = computed(() => {
       const total = todos.length;
       const active = todos.filter(todo => !todo.completed).length;
       const completed = total - active;
       return { total, active, completed };
     });

     // Add new todo
     const addTodo = () => {
       if (newTodo.trim()) {
         setTodos(prev => [...prev, {
           id: Date.now(),
           text: newTodo.trim(),
           completed: false,
           createdAt: new Date().toISOString()
         }]);
         setNewTodo('');
       }
     };

     // Toggle todo completion
     const toggleTodo = (id) => {
       setTodos(prev => prev.map(todo =>
         todo.id === id ? { ...todo, completed: !todo.completed } : todo
       ));
     };

     // Remove todo
     const removeTodo = (id) => {
       setTodos(prev => prev.filter(todo => todo.id !== id));
     };

     // Clear completed todos
     const clearCompleted = () => {
       setTodos(prev => prev.filter(todo => !todo.completed));
     };

     // Toggle theme
     const toggleTheme = () => {
       const newTheme = theme === 'light' ? 'dark' : 'light';
       setTheme(newTheme);
       document.body.className = `theme-${newTheme}`;
     };

     return jsx('div', {
       className: 'todo-app',
       children: [
         jsx('div', {
           className: 'demo-header',
           children: jsx('h2', { children: '🚀 Pydance Client - Complete Demo' })
         }),

         // Theme Toggle
         jsx('div', {
           className: 'controls',
           children: jsx('button', {
             onClick: toggleTheme,
             children: `Switch to ${theme === 'light' ? 'Dark' : 'Light'} Theme`
           })
         }),

         // Stats
         jsx('div', {
           className: 'stats',
           children: [
             jsx('div', {
               className: 'stat-card',
               children: [
                 jsx('div', {
                   className: 'stat-number',
                   children: stats.value.total
                 }),
                 jsx('div', { children: 'Total Todos' })
               ]
             }),
             jsx('div', {
               className: 'stat-card',
               children: [
                 jsx('div', {
                   className: 'stat-number',
                   children: stats.value.active
                 }),
                 jsx('div', { children: 'Active' })
               ]
             }),
             jsx('div', {
               className: 'stat-card',
               children: [
                 jsx('div', {
                   className: 'stat-number',
                   children: stats.value.completed
                 }),
                 jsx('div', { children: 'Completed' })
               ]
             })
           ]
         }),

         // Add Todo Form
         jsx('div', {
           className: 'demo-container',
           children: [
             jsx('h3', { children: '📝 Add New Todo' }),
             jsx('div', {
               className: 'form-group',
               children: [
                 jsx('label', {
                   htmlFor: 'new-todo-input',
                   children: 'Todo Text:'
                 }),
                 jsx('input', {
                   id: 'new-todo-input',
                   type: 'text',
                   value: newTodo,
                   onInput: (e) => setNewTodo(e.target.value),
                   onKeyDown: (e) => {
                     if (e.key === 'Enter') {
                       addTodo();
                     }
                   },
                   placeholder: 'Enter a new todo...'
                 })
               ]
             }),
             jsx('div', {
               className: 'controls',
               children: jsx('button', {
                 onClick: addTodo,
                 className: 'success',
                 children: 'Add Todo'
               })
             })
           ]
         }),

         // Filter Controls
         jsx('div', {
           className: 'demo-container',
           children: [
             jsx('h3', { children: '🔍 Filter Todos' }),
             jsx('div', {
               className: 'controls',
               children: [
                 jsx('button', {
                   onClick: () => setFilter('all'),
                   children: 'All',
                   style: filter === 'all' ? { background: '#007acc' } : {}
                 }),
                 jsx('button', {
                   onClick: () => setFilter('active'),
                   children: 'Active',
                   style: filter === 'active' ? { background: '#007acc' } : {}
                 }),
                 jsx('button', {
                   onClick: () => setFilter('completed'),
                   children: 'Completed',
                   style: filter === 'completed' ? { background: '#007acc' } : {}
                 }),
                 jsx('button', {
                   onClick: clearCompleted,
                   className: 'danger',
                   children: 'Clear Completed'
                 })
               ]
             })
           ]
         }),

         // Todo List
         jsx('div', {
           className: 'demo-container',
           children: [
             jsx('h3', { children: `📋 Todos (${filteredTodos.value.length})` }),
             jsx('div', {
               className: 'todo-list',
               children: filteredTodos.value.length === 0
                 ? jsx('p', {
                     children: filter === 'all'
                       ? 'No todos yet. Add one above!'
                       : `No ${filter} todos.`
                   })
                 : filteredTodos.value.map(todo =>
                     jsx('div', {
                       key: todo.id,
                       className: `todo-item ${todo.completed ? 'completed' : ''}`,
                       children: [
                         jsx('div', {
                           className: 'todo-text',
                           onClick: () => toggleTodo(todo.id),
                           children: todo.text
                         }),
                         jsx('div', {
                           className: 'todo-actions',
                           children: [
                             jsx('button', {
                               onClick: () => toggleTodo(todo.id),
                               children: todo.completed ? '✓' : '○'
                             }),
                             jsx('button', {
                               onClick: () => removeTodo(todo.id),
                               className: 'danger',
                               children: '×'
                             })
                           ]
                         })
                       ]
                     })
                   )
             })
           ]
         })
       ]
     });
   });

   // Mount the application
   const app = new TodoApp();
   app.mount('#app');

Signal-Based Counter
~~~~~~~~~~~~~~~~~~~~

Simple counter demonstrating signal reactivity:

.. code-block:: javascript

   import { createComponent, signal, jsx } from '@pydance/client';

   // Counter component using signals
   const Counter = createComponent(() => {
     const count = signal(0);

     // Update counter display
     effect(() => {
       const display = document.getElementById('counter');
       if (display) {
         display.textContent = count.value;
       }
     });

     // Event listeners
     const increment = () => count.value++;
     const decrement = () => count.value--;

     document.getElementById('increment')?.addEventListener('click', increment);
     document.getElementById('decrement')?.addEventListener('click', decrement);

     return { count, increment, decrement };
   });

State Management Patterns
~~~~~~~~~~~~~~~~~~~~~~~~~

Different state management approaches:

**Zustand-style Store:**

.. code-block:: javascript

   import { create } from '@pydance/client';

   const useCounterStore = create((set, get) => ({
     count: 0,
     increment: () => set(state => ({ count: state.count + 1 })),
     decrement: () => set(state => ({ count: state.count - 1 })),
     reset: () => set({ count: 0 })
   }));

**Redux Toolkit (RTK) Style:**

.. code-block:: javascript

   import { createSlice, configureStore } from '@pydance/client';

   const counterSlice = createSlice({
     name: 'counter',
     initialState: { value: 0 },
     reducers: {
       increment: (state) => ({ ...state, value: state.value + 1 }),
       decrement: (state) => ({ ...state, value: state.value - 1 }),
       incrementByAmount: (state, action) => ({ ...state, value: state.value + action.payload })
     }
   });

   const rtkStore = configureStore({
     reducer: { counter: counterSlice }
   });

**Immer Integration:**

.. code-block:: javascript

   import { create, immer } from '@pydance/client';

   const useImmerStore = create(
     immer((set) => ({
       nested: { deep: { value: 0 } },
       updateDeep: () => set(state => {
         state.nested.deep.value += 1; // Mutate directly!
       })
     }))
   );

**Persistent Store with DevTools:**

.. code-block:: javascript

   import { create, persist, devtools } from '@pydance/client';

   const usePersistStore = create(
     devtools(
       persist(
         (set) => ({
           count: 0,
           increment: () => set(state => ({ count: state.count + 1 })),
           decrement: () => set(state => ({ count: state.count - 1 }))
         }),
         { name: 'persist-demo' }
       ),
       { name: 'Pydance Demo Store' }
     )
   );

Advanced Scaling Features
~~~~~~~~~~~~~~~~~~~~~~~~~

Virtual scrolling for large datasets:

.. code-block:: javascript

   import { createComponent, VirtualList, jsx } from '@pydance/client';

   const LargeListDemo = createComponent(() => {
     // Create large dataset
     const items = Array.from({ length: 100000 }, (_, i) => ({
       id: i,
       name: `Item ${i}`,
       value: Math.random() * 1000,
       category: ['A', 'B', 'C'][Math.floor(Math.random() * 3)]
     }));

     return jsx('div', {
       className: 'virtual-list-container',
       children: jsx(VirtualList, {
         items: items,
         renderItem: (item, index) => jsx('div', {
           key: item.id,
           className: 'virtual-item',
           children: [
             jsx('span', { className: 'item-id', children: `#${item.id}` }),
             jsx('span', { className: 'item-data', children: `${item.name} - ${item.category} - $${item.value.toFixed(2)}` }),
             jsx('button', {
               onClick: () => selectItem(item.id),
               children: 'Select'
             })
           ]
         }),
         itemHeight: 60,
         containerHeight: 400,
         overscan: 10
       })
     });
   });

Real-time Chat Application
~~~~~~~~~~~~~~~~~~~~~~~~~

WebSocket-based chat with real-time updates:

.. code-block:: javascript

   import { createComponent, useState, useEffect, jsx } from '@pydance/client';

   const ChatApp = createComponent(() => {
     const [messages, setMessages] = useState([]);
     const [inputValue, setInputValue] = useState('');
     const [isConnected, setIsConnected] = useState(false);

     useEffect(() => {
       // WebSocket connection
       const ws = new WebSocket('ws://localhost:8000/ws/chat?room=general');

       ws.onopen = () => setIsConnected(true);
       ws.onmessage = (event) => {
         const data = JSON.parse(event.data);
         setMessages(prev => [...prev, {
           id: Date.now(),
           type: data.type === 'chat_message' ? 'user' : 'system',
           message: data.message,
           timestamp: data.timestamp
         }]);
       };
       ws.onclose = () => setIsConnected(false);

       return () => ws.close();
     }, []);

     const sendMessage = () => {
       if (inputValue.trim() && isConnected) {
         // Send via WebSocket
         ws.send(JSON.stringify({
           type: 'chat_message',
           message: inputValue.trim(),
           room: 'general'
         }));
         setInputValue('');
       }
     };

     return jsx('div', {
       className: 'chat-container',
       children: [
         jsx('div', {
           className: 'chat-messages',
           children: messages.map(msg =>
             jsx('div', {
               key: msg.id,
               className: `chat-message ${msg.type}`,
               children: msg.message
             })
           )
         }),
         jsx('div', {
           className: 'chat-input-container',
           children: [
             jsx('input', {
               type: 'text',
               className: 'chat-input',
               value: inputValue,
               onChange: (e) => setInputValue(e.target.value),
               onKeyDown: (e) => e.key === 'Enter' && sendMessage(),
               placeholder: 'Type your message...'
             }),
             jsx('button', {
               onClick: sendMessage,
               children: 'Send'
             })
           ]
         })
       ]
     });
   });

API Integration
~~~~~~~~~~~~~~~

Seamless integration with Pydance backend APIs:

.. code-block:: javascript

   import { createComponent, useState, useEffect } from '@pydance/client';

   const UserList = createComponent(() => {
     const [users, setUsers] = useState([]);
     const [loading, setLoading] = useState(true);

     useEffect(() => {
       fetch('/api/users')
         .then(res => res.json())
         .then(data => {
           setUsers(data.users);
           setLoading(false);
         });
     }, []);

     if (loading) {
       return jsx('div', { children: 'Loading...' });
     }

     return jsx('ul', {
       children: users.map(user =>
         jsx('li', { key: user.id, children: user.name })
       )
     });
   });

Forms and Validation
~~~~~~~~~~~~~~~~~~~~

Built-in form handling with validation:

.. code-block:: javascript

   import { createComponent, useState, useForm } from '@pydance/client';

   const ContactForm = createComponent(() => {
     const { values, errors, handleChange, handleSubmit } = useForm({
       initialValues: { name: '', email: '', message: '' },
       validate: (values) => {
         const errors = {};
         if (!values.name) errors.name = 'Name is required';
         if (!values.email) errors.email = 'Email is required';
         if (!values.message) errors.message = 'Message is required';
         return errors;
       },
       onSubmit: async (values) => {
         const response = await fetch('/api/contact', {
           method: 'POST',
           headers: { 'Content-Type': 'application/json' },
           body: JSON.stringify(values)
         });
         console.log('Form submitted:', await response.json());
       }
     });

     return jsx('form', {
       onSubmit: handleSubmit,
       children: [
         jsx('input', {
           type: 'text',
           name: 'name',
           value: values.name,
           onChange: handleChange,
           placeholder: 'Your name'
         }),
         errors.name && jsx('div', { className: 'error', children: errors.name }),

         jsx('input', {
           type: 'email',
           name: 'email',
           value: values.email,
           onChange: handleChange,
           placeholder: 'Your email'
         }),
         errors.email && jsx('div', { className: 'error', children: errors.email }),

         jsx('textarea', {
           name: 'message',
           value: values.message,
           onChange: handleChange,
           placeholder: 'Your message'
         }),
         errors.message && jsx('div', { className: 'error', children: errors.message }),

         jsx('button', { type: 'submit', children: 'Send' })
       ]
     });
   });

Routing
~~~~~~~

Client-side routing with @pydance/client-router:

.. code-block:: javascript

   import { createComponent, useState } from '@pydance/client';
   import { Router, Route, Link } from '@pydance/client-router';

   const Home = createComponent(() => jsx('h1', { children: 'Home' }));
   const About = createComponent(() => jsx('h1', { children: 'About' }));
   const Contact = createComponent(() => jsx('h1', { children: 'Contact' }));

   const App = createComponent(() => {
     return jsx(Router, {
       children: [
         jsx('nav', {
           children: [
             jsx(Link, { to: '/', children: 'Home' }),
             jsx(Link, { to: '/about', children: 'About' }),
             jsx(Link, { to: '/contact', children: 'Contact' })
           ]
         }),
         jsx(Route, { path: '/', component: Home }),
         jsx(Route, { path: '/about', component: About }),
         jsx(Route, { path: '/contact', component: Contact })
       ]
     });
   });

State Management
~~~~~~~~~~~~~~~~

Advanced state management with @pydance/client-store:

.. code-block:: javascript

   import { createStore } from '@pydance/client-store';

   // Create a store
   const counterStore = createStore({
     state: { count: 0 },
     actions: {
       increment: (state) => ({ count: state.count + 1 }),
       decrement: (state) => ({ count: state.count - 1 }),
       reset: () => ({ count: 0 })
     }
   });

   // Use in component
   const CounterApp = createComponent(() => {
     const { state, actions } = counterStore.useStore();

     return jsx('div', {
       children: [
         jsx('p', { children: `Count: ${state.count}` }),
         jsx('button', { onClick: actions.increment, children: '+' }),
         jsx('button', { onClick: actions.decrement, children: '-' }),
         jsx('button', { onClick: actions.reset, children: 'Reset' })
       ]
     });
   });

Performance Optimization
------------------------

@pydance/client includes several performance optimization features:

Lazy Loading
~~~~~~~~~~~~

.. code-block:: javascript

   import { lazy, Suspense } from '@pydance/client';

   const LazyComponent = lazy(() => import('./LazyComponent.js'));

   const App = createComponent(() => {
     return jsx(Suspense, {
       fallback: jsx('div', { children: 'Loading...' }),
       children: jsx(LazyComponent, {})
     });
   });

Memoization
~~~~~~~~~~~

.. code-block:: javascript

   import { createComponent, memo } from '@pydance/client';

   const ExpensiveChild = memo(createComponent(({ value }) => {
     console.log('ExpensiveChild rendered');
     return jsx('div', { children: `Value: ${value}` });
   }));

   const Parent = createComponent(() => {
     const [count, setCount] = useState(0);

     return jsx('div', {
       children: [
         jsx(ExpensiveChild, { value: count }),
         jsx('button', { onClick: () => setCount(count + 1), children: 'Increment' })
       ]
     });
   });

Development Tools
-----------------

@pydance/client includes powerful development tools:

DevTools Integration
~~~~~~~~~~~~~~~~~~~~

.. code-block:: javascript

   import { enableDevTools } from '@pydance/client-devtools';

   // Enable development tools
   if (process.env.NODE_ENV === 'development') {
     enableDevTools();
   }

Performance Monitoring
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: javascript

   import { performanceMonitor } from '@pydance/client';

   // Monitor component performance
   const MonitoredComponent = performanceMonitor(createComponent(() => {
     // Your component logic
     return jsx('div', { children: 'Monitored component' });
   }));

   // Get performance metrics
   const metrics = performanceMonitor.getMetrics();
   console.log('Component render times:', metrics);

Testing
-------

@pydance/client provides testing utilities:

.. code-block:: javascript

   import { render, fireEvent, screen } from '@pydance/client-testing';

   test('counter increments', () => {
     const { container } = render(Counter);
     const button = screen.getByText('Increment');

     fireEvent.click(button);
     expect(screen.getByText('Count: 1')).toBeInTheDocument();
   });

Migration from Other Frameworks
-------------------------------

Migrating from React
~~~~~~~~~~~~~~~~~~~~

.. code-block:: javascript

   // React
   const Component = () => {
     const [state, setState] = useState(initialState);
     return <div>{state}</div>;
   };

   // @pydance/client
   const Component = createComponent(() => {
     const [state, setState] = useState(initialState);
     return jsx('div', { children: state });
   });

Migrating from Vue
~~~~~~~~~~~~~~~~~~

.. code-block:: javascript

   // Vue
   <template>
     <div>{{ count }}</div>
   </template>

   // @pydance/client
   const Component = createComponent(() => {
     const count = signal(0);
     return jsx('div', { children: count.value });
   });

Migrating from Svelte
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: javascript

   // Svelte
   <script>
     let count = 0;
   </script>
   <div>{count}</div>

   // @pydance/client
   const Component = createComponent(() => {
     const count = signal(0);
     return jsx('div', { children: count.value });
   });

API Reference
-------------

Core API
~~~~~~~~

**createComponent(componentFunction)**

Creates a component from a function.

**Parameters:**
- ``componentFunction``: Function that returns JSX

**Returns:** Component class

**signal(initialValue)**

Creates a reactive signal.

**Parameters:**
- ``initialValue``: Initial value for the signal

**Returns:** Signal object with ``.value`` property

**computed(computeFunction)**

Creates a computed signal.

**Parameters:**
- ``computeFunction``: Function that computes the value

**Returns:** Computed signal

**effect(effectFunction)**

Creates a side effect that runs when dependencies change.

**Parameters:**
- ``effectFunction``: Function to run on dependency changes

**jsx(tag, props)**

Creates JSX elements.

**Parameters:**
- ``tag``: HTML tag name or component
- ``props``: Object with properties and children

**Returns:** JSX element

Hooks API
~~~~~~~~~

**useState(initialValue)**

State management hook.

**useEffect(effectFunction, dependencies)**

Side effect hook.

**useMemo(computeFunction, dependencies)**

Memoization hook.

**useCallback(callbackFunction, dependencies)**

Callback memoization hook.

**useContext(context)**

Context consumption hook.

**useReducer(reducer, initialState)**

Reducer hook for complex state.

Advanced API
~~~~~~~~~~~~

**createStore(config)**

Creates a centralized store.

**lazy(importFunction)**

Lazy loading utility.

**memo(component)**

Memoization for components.

**Suspense**

Suspense component for async operations.

**Fragment**

JSX fragment component.

Ecosystem
---------

Official Packages
~~~~~~~~~~~~~~~~~

- ``@pydance/client`` - Core framework
- ``@pydance/client-devtools`` - Development tools
- ``@pydance/client-router`` - Client-side routing
- ``@pydance/client-store`` - State management
- ``@pydance/client-forms`` - Form handling
- ``@pydance/client-testing`` - Testing utilities
- ``@pydance/client-ssr`` - Server-side rendering
- ``@pydance/client-i18n`` - Internationalization

Community Packages
~~~~~~~~~~~~~~~~~~

- ``pydance-client-axios`` - Axios integration
- ``pydance-client-socket`` - WebSocket integration
- ``pydance-client-pwa`` - PWA utilities
- ``pydance-client-charts`` - Chart components
- ``pydance-client-icons`` - Icon components

Browser Support
---------------

@pydance/client supports all modern browsers:

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

For older browsers, include polyfills for:

- ``Promise``
- ``Object.assign``
- ``Array.prototype.includes``
- ``String.prototype.includes``

Contributing
------------

We welcome contributions! Please see our `Contributing Guide <https://github.com/ancillary-ai/pydance/blob/main/CONTRIBUTING.md>`_.

License
-------

MIT License - see the `LICENSE <https://github.com/ancillary-ai/pydance/blob/main/LICENSE>`_ file for details.

Support
-------

- **Documentation**: https://pydance.dev/client
- **GitHub Issues**: https://github.com/ancillary-ai/pydance/issues
- **Discord**: https://discord.gg/pydance

---

**Made with ❤️ by the Pydance Framework Team**
