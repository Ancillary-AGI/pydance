/**
 * Code Splitting and Lazy Loading
 * Preserves all existing functionality while adding dynamic imports
 */

/**
 * Lazy load component with loading state
 */
export function lazy(loader, options = {}) {
  const {
    loading: LoadingComponent = null,
    error: ErrorComponent = null,
    delay = 200,
    timeout = 10000
  } = options;
  
  let loadPromise = null;
  let loadedModule = null;
  let loadError = null;
  
  return function LazyComponent(props = {}) {
    // Return loaded component
    if (loadedModule) {
      const Component = loadedModule.default || loadedModule;
      return Component(props);
    }
    
    // Return error component
    if (loadError && ErrorComponent) {
      return ErrorComponent({ error: loadError, retry: () => {
        loadError = null;
        loadPromise = null;
        return LazyComponent(props);
      }});
    }
    
    // Start loading if not already
    if (!loadPromise) {
      loadPromise = Promise.race([
        loader(),
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Load timeout')), timeout)
        )
      ])
      .then(module => {
        loadedModule = module;
        return module;
      })
      .catch(error => {
        loadError = error;
        throw error;
      });
    }
    
    // Return loading component
    if (LoadingComponent) {
      return LoadingComponent(props);
    }
    
    // Default loading
    return {
      $$typeof: Symbol.for('pydance.element'),
      tagName: 'div',
      props: { className: 'loading' },
      children: ['Loading...']
    };
  };
}

/**
 * Preload component for faster loading
 */
export function preload(loader) {
  let loadPromise = null;
  
  return {
    load: () => {
      if (!loadPromise) {
        loadPromise = loader();
      }
      return loadPromise;
    },
    component: lazy(loader)
  };
}

/**
 * Route-based code splitting
 */
export class RouteLoader {
  constructor() {
    this.routes = new Map();
    this.preloadQueue = new Set();
  }
  
  register(path, loader) {
    this.routes.set(path, {
      loader,
      component: lazy(loader),
      preloaded: false
    });
  }
  
  get(path) {
    const route = this.routes.get(path);
    return route ? route.component : null;
  }
  
  preload(path) {
    const route = this.routes.get(path);
    if (route && !route.preloaded) {
      route.loader().then(() => {
        route.preloaded = true;
      });
    }
  }
  
  preloadAll(paths) {
    paths.forEach(path => this.preload(path));
  }
  
  // Preload on hover
  onHover(path) {
    if (!this.preloadQueue.has(path)) {
      this.preloadQueue.add(path);
      setTimeout(() => {
        this.preload(path);
        this.preloadQueue.delete(path);
      }, 100);
    }
  }
}

/**
 * Dynamic import with retry
 */
export async function dynamicImport(path, retries = 3, delay = 1000) {
  for (let i = 0; i < retries; i++) {
    try {
      return await import(path);
    } catch (error) {
      if (i === retries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, delay * (i + 1)));
    }
  }
}

/**
 * Bundle analyzer for development
 */
export class BundleAnalyzer {
  constructor() {
    this.chunks = new Map();
    this.loadTimes = new Map();
  }
  
  track(chunkName, size, loadTime) {
    this.chunks.set(chunkName, { size, loadTime });
    this.loadTimes.set(chunkName, loadTime);
  }
  
  getStats() {
    const chunks = Array.from(this.chunks.entries());
    const totalSize = chunks.reduce((sum, [, { size }]) => sum + size, 0);
    const avgLoadTime = Array.from(this.loadTimes.values())
      .reduce((sum, time) => sum + time, 0) / this.loadTimes.size;
    
    return {
      totalChunks: chunks.length,
      totalSize,
      averageLoadTime: avgLoadTime,
      chunks: chunks.map(([name, data]) => ({
        name,
        ...data
      }))
    };
  }
  
  getLargestChunks(n = 5) {
    return Array.from(this.chunks.entries())
      .sort(([, a], [, b]) => b.size - a.size)
      .slice(0, n)
      .map(([name, data]) => ({ name, ...data }));
  }
  
  getSlowestChunks(n = 5) {
    return Array.from(this.chunks.entries())
      .sort(([, a], [, b]) => b.loadTime - a.loadTime)
      .slice(0, n)
      .map(([name, data]) => ({ name, ...data }));
  }
}

/**
 * Prefetch resources
 */
export function prefetch(url, as = 'script') {
  const link = document.createElement('link');
  link.rel = 'prefetch';
  link.as = as;
  link.href = url;
  document.head.appendChild(link);
}

/**
 * Preconnect to origin
 */
export function preconnect(origin) {
  const link = document.createElement('link');
  link.rel = 'preconnect';
  link.href = origin;
  document.head.appendChild(link);
}

/**
 * Module federation for micro-frontends
 */
export class ModuleFederation {
  constructor() {
    this.remotes = new Map();
  }
  
  registerRemote(name, url) {
    this.remotes.set(name, url);
  }
  
  async loadRemote(name, module) {
    const url = this.remotes.get(name);
    if (!url) {
      throw new Error(`Remote "${name}" not registered`);
    }
    
    // Load remote container
    const container = await this.loadContainer(url);
    
    // Initialize container
    await container.init(__webpack_share_scopes__.default);
    
    // Get module
    const factory = await container.get(module);
    return factory();
  }
  
  async loadContainer(url) {
    // Load script
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = url;
      script.onload = () => {
        const container = window[this.getContainerName(url)];
        resolve(container);
      };
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }
  
  getContainerName(url) {
    // Extract container name from URL
    const match = url.match(/\/([^\/]+)\.js$/);
    return match ? match[1] : 'remoteEntry';
  }
}

// Global instances
export const routeLoader = new RouteLoader();
export const bundleAnalyzer = new BundleAnalyzer();
export const moduleFederation = new ModuleFederation();

// Helper for route-based splitting
export function defineRoutes(routes) {
  Object.entries(routes).forEach(([path, loader]) => {
    routeLoader.register(path, loader);
  });
  return routeLoader;
}

// Example usage:
/*
const routes = defineRoutes({
  '/': () => import('./pages/Home.js'),
  '/about': () => import('./pages/About.js'),
  '/dashboard': () => import('./pages/Dashboard.js')
});

// Preload on hover
document.querySelector('a[href="/about"]').addEventListener('mouseenter', () => {
  routes.onHover('/about');
});
*/
