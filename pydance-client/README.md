# @pydance/client

[![npm version](https://badge.fury.io/js/@pydance/client.svg)](https://badge.fury.io/js/@pydance/client)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![TypeScript](https://img.shields.io/badge/TypeScript-Ready-blue.svg)](https://www.typescriptlang.org/)
[![Bundle Size](https://img.shields.io/bundlephobia/minzip/@pydance/client)](https://bundlephobia.com/package/@pydance/client)
[![Build Status](https://github.com/ancillary-ai/pydance/workflows/CI/badge.svg)](https://github.com/ancillary-ai/pydance/actions)

> **Ultra-lightweight, signal-based frontend framework for Pydance** ⚡

A next-generation frontend framework designed specifically for seamless integration with Pydance backend, featuring signal-based reactivity, function components with hooks, and modern JSX runtime.

## ✨ Features

- **🚀 Ultra-Lightweight**: ~3-8KB gzipped core runtime
- **⚡ Signal-Based Reactivity**: Fine-grained, automatic dependency tracking
- **🎯 Function Components**: Modern hooks-based component system
- **🎨 Modern JSX Runtime**: Optimized JSX with TypeScript support
- **🔧 Zero External Dependencies**: Completely standalone
- **🌐 SSR Support**: Server-side rendering integration
- **📊 Built-in Performance Monitoring**: Real-time performance metrics
- **💾 Automatic Memory Management**: Intelligent cleanup and optimization
- **🔗 Pydance Backend Integration**: Seamless API integration
- **📱 Progressive Web App Ready**: PWA support out of the box

## 📦 Installation

```bash
# npm
npm install @pydance/client

# yarn
yarn add @pydance/client

# pnpm
pnpm add @pydance/client
```

## 🚀 Quick Start

```javascript
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
```

## 📚 Documentation

- **[Getting Started](https://pydance.dev/client/docs/getting-started)**
- **[API Reference](https://pydance.dev/client/docs/api)**
- **[Examples](https://pydance.dev/client/docs/examples)**
- **[Migration Guide](https://pydance.dev/client/docs/migration)**

## 🔧 Core Concepts

### Signals

Signals are the foundation of Pydance Client's reactivity system:

```javascript
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
```

### Components

Function-based components with hooks:

```javascript
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
```

### JSX Runtime

Modern JSX with optimized runtime:

```javascript
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
```

## 🛠️ Development

### Setup

```bash
# Clone the repository
git clone https://github.com/ancillary-ai/pydance.git
cd pydance/pydance-client

# Install dependencies
npm install

# Start development server
npm run dev

# Run tests
npm run test

# Build for production
npm run build
```

### Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run test` - Run tests
- `npm run test:watch` - Watch mode for tests
- `npm run test:coverage` - Generate coverage report
- `npm run lint` - Lint code
- `npm run format` - Format code
- `npm run typecheck` - TypeScript type checking
- `npm run size` - Check bundle size

## 📊 Performance

Pydance Client is designed for maximum performance:

| **Metric** | **Pydance Client** | **React** | **Vue 3** | **Svelte** |
|------------|------------------|-----------|-----------|-----------|
| **Bundle Size** | 3-8KB | 40KB+ | 20KB+ | 5KB+ |
| **Runtime** | Signals | VDOM | Proxy | Compiler |
| **Performance** | ⚡ Fastest | Fast | Fast | Very Fast |
| **Memory** | Optimized | Good | Good | Excellent |

## 🌟 Ecosystem

### Official Packages

- `@pydance/client` - Core framework
- `@pydance/client-devtools` - Development tools
- `@pydance/client-router` - Client-side routing
- `@pydance/client-store` - State management
- `@pydance/client-forms` - Form handling
- `@pydance/client-testing` - Testing utilities

### Community Packages

- `pydance-client-axios` - Axios integration
- `pydance-client-socket` - WebSocket integration
- `pydance-client-i18n` - Internationalization
- `pydance-client-pwa` - PWA utilities

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](https://github.com/ancillary-ai/pydance/blob/main/CONTRIBUTING.md).

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by SolidJS, Preact, and Vue 3
- Built for the Pydance ecosystem
- Thanks to all contributors and the open-source community

## 📞 Support

- **Documentation**: [https://pydance.dev/client](https://pydance.dev/client)
- **Issues**: [GitHub Issues](https://github.com/ancillary-ai/pydance/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ancillary-ai/pydance/discussions)
- **Discord**: [Join our community](https://discord.gg/pydance)

## 🗺️ Roadmap

- [ ] **v3.1.0** - Enhanced SSR support
- [ ] **v3.2.0** - Web Components integration
- [ ] **v4.0.0** - Concurrent rendering
- [ ] **v4.1.0** - Server components
- [ ] **v4.2.0** - Mobile framework

---

**Made with ❤️ by the Pydance Framework Team**
