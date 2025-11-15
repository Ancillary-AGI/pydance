/**
 * Tailwind CSS Integration for Pydance JavaScript Components
 *
 * Provides comprehensive Tailwind CSS support for React-like components,
 * including utility classes, component styling, responsive design, and dark mode.
 */

export class TailwindConfig {
  constructor(options = {}) {
    this.enabled = options.enabled || false;
    this.cdnUrl = options.cdnUrl || 'https://cdn.tailwindcss.com';
    this.version = options.version || '3.4.0';
    this.customCss = options.customCss || '';
    this.darkMode = options.darkMode || 'media'; // 'media', 'class', or false
    this.theme = options.theme || {};
  }
}

export class TailwindCSS {
  constructor(config = new TailwindConfig()) {
    this.config = config;
    this._initialized = false;
    this._styleElement = null;
  }

  isEnabled() {
    return this.config.enabled;
  }

  async initialize() {
    if (!this.isEnabled() || this._initialized) return;

    try {
      // Load Tailwind CSS
      await this._loadTailwindCSS();

      // Add custom CSS if provided
      if (this.config.customCss) {
        this._injectCustomCSS(this.config.customCss);
      }

      this._initialized = true;
    } catch (error) {
      console.warn('Failed to initialize Tailwind CSS:', error);
    }
  }

  async _loadTailwindCSS() {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = this.config.cdnUrl;
      script.onload = () => resolve();
      script.onerror = () => reject(new Error('Failed to load Tailwind CSS'));
      document.head.appendChild(script);
    });
  }

  _injectCustomCSS(css) {
    const style = document.createElement('style');
    style.textContent = css;
    document.head.appendChild(style);
    this._styleElement = style;
  }

  // Component class generators
  getButtonClasses(variant = 'primary', size = 'md', options = {}) {
    if (!this.isEnabled()) return '';

    const baseClasses = [
      'inline-flex',
      'items-center',
      'justify-center',
      'gap-2',
      'font-medium',
      'transition-colors',
      'duration-200',
      'focus:outline-none',
      'focus:ring-2',
      'focus:ring-offset-2',
      'disabled:opacity-50',
      'disabled:cursor-not-allowed'
    ];

    const variantClasses = {
      primary: [
        'bg-blue-600',
        'hover:bg-blue-700',
        'text-white',
        'border',
        'border-transparent',
        'focus:ring-blue-500'
      ],
      secondary: [
        'bg-gray-200',
        'hover:bg-gray-300',
        'text-gray-900',
        'border',
        'border-transparent',
        'focus:ring-gray-500'
      ],
      outline: [
        'bg-transparent',
        'hover:bg-gray-50',
        'text-gray-700',
        'border',
        'border-gray-300',
        'focus:ring-blue-500'
      ],
      ghost: [
        'bg-transparent',
        'hover:bg-gray-100',
        'text-gray-700',
        'border',
        'border-transparent',
        'focus:ring-blue-500'
      ],
      danger: [
        'bg-red-600',
        'hover:bg-red-700',
        'text-white',
        'border',
        'border-transparent',
        'focus:ring-red-500'
      ]
    };

    const sizeClasses = {
      xs: ['text-xs', 'px-2', 'py-1', 'rounded'],
      sm: ['text-sm', 'px-3', 'py-2', 'rounded-md'],
      md: ['text-sm', 'px-4', 'py-2', 'rounded-md'],
      lg: ['text-base', 'px-6', 'py-3', 'rounded-md'],
      xl: ['text-lg', 'px-8', 'py-4', 'rounded-lg']
    };

    const allClasses = [
      ...baseClasses,
      ...(variantClasses[variant] || variantClasses.primary),
      ...(sizeClasses[size] || sizeClasses.md)
    ];

    if (options.fullWidth) allClasses.push('w-full');
    if (options.rounded) allClasses.push('rounded-full');

    return allClasses.join(' ');
  }

  getInputClasses(variant = 'default', size = 'md', options = {}) {
    if (!this.isEnabled()) return '';

    const baseClasses = [
      'block',
      'w-full',
      'border',
      'rounded-md',
      'shadow-sm',
      'transition-colors',
      'duration-200',
      'focus:outline-none',
      'focus:ring-1',
      'disabled:opacity-50',
      'disabled:cursor-not-allowed'
    ];

    const variantClasses = {
      default: [
        'border-gray-300',
        'placeholder-gray-400',
        'focus:ring-blue-500',
        'focus:border-blue-500'
      ],
      error: [
        'border-red-300',
        'placeholder-red-300',
        'text-red-900',
        'focus:ring-red-500',
        'focus:border-red-500'
      ],
      success: [
        'border-green-300',
        'placeholder-green-300',
        'text-green-900',
        'focus:ring-green-500',
        'focus:border-green-500'
      ]
    };

    const sizeClasses = {
      sm: ['text-sm', 'px-2', 'py-1'],
      md: ['text-sm', 'px-3', 'py-2'],
      lg: ['text-base', 'px-4', 'py-3']
    };

    return [
      ...baseClasses,
      ...(variantClasses[variant] || variantClasses.default),
      ...(sizeClasses[size] || sizeClasses.md)
    ].join(' ');
  }

  getCardClasses(variant = 'default', options = {}) {
    if (!this.isEnabled()) return '';

    const baseClasses = [
      'bg-white',
      'overflow-hidden',
      'shadow',
      'rounded-lg'
    ];

    const variantClasses = {
      default: [],
      elevated: ['shadow-lg'],
      outlined: ['border', 'border-gray-200'],
      filled: ['bg-gray-50']
    };

    const allClasses = [
      ...baseClasses,
      ...(variantClasses[variant] || variantClasses.default)
    ];

    return allClasses.join(' ');
  }

  getAlertClasses(variant = 'info', options = {}) {
    if (!this.isEnabled()) return '';

    const baseClasses = [
      'rounded-md',
      'p-4',
      'flex',
      'items-start',
      'gap-3'
    ];

    const variantClasses = {
      info: ['bg-blue-50', 'border', 'border-blue-200', 'text-blue-800'],
      success: ['bg-green-50', 'border', 'border-green-200', 'text-green-800'],
      warning: ['bg-yellow-50', 'border', 'border-yellow-200', 'text-yellow-800'],
      error: ['bg-red-50', 'border', 'border-red-200', 'text-red-800']
    };

    return [
      ...baseClasses,
      ...(variantClasses[variant] || variantClasses.info)
    ].join(' ');
  }
}

// Global instance
let _tailwindInstance = null;

export function getTailwindCSS(config = null) {
  if (!_tailwindInstance) {
    _tailwindInstance = new TailwindCSS(config || new TailwindConfig());
  }
  return _tailwindInstance;
}

// Make available globally for components
if (typeof window !== 'undefined') {
  window.getTailwindCSS = getTailwindCSS;
  window.enableTailwind = enableTailwind;
  window.tw = tw;
}

export function configureTailwind(config) {
  _tailwindInstance = new TailwindCSS(config);
}

export function enableTailwind(options = {}) {
  const config = new TailwindConfig({ enabled: true, ...options });
  configureTailwind(config);

  // Set global flag that components check
  if (typeof window !== 'undefined') {
    window.PydanceTailwind = { enabled: true, ...options };
  }

  // Auto-initialize
  const tw = getTailwindCSS();
  tw.initialize().catch(console.warn);
}

export function disableTailwind() {
  const config = new TailwindConfig({ enabled: false });
  configureTailwind(config);
}

// Template literal helper for conditional classes
export function tw(...classes) {
  return classes.filter(Boolean).join(' ');
}

// Export default
export default {
  TailwindConfig,
  TailwindCSS,
  getTailwindCSS,
  configureTailwind,
  enableTailwind,
  disableTailwind,
  tw
};
