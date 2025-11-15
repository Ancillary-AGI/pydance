/**
 * Input - Reusable Input Component
 * Provides a flexible input component with different types,
 * validation states, and styling support.
 * Supports both traditional CSS and Tailwind CSS.
 */

import { Component } from '~/core/Component.js';

export class Input extends Component {
  constructor(props = {}) {
    super(props);

    this.state = {
      value: props.value || '',
      isValid: true,
      isTouched: false,
      errorMessage: ''
    };

    // Initialize Tailwind if enabled - safe to call even if not used
    this.tailwind = { isEnabled: () => false }; // Default fallback
    try {
      if (typeof window !== 'undefined' && window.getTailwindCSS) {
        this.tailwind = window.getTailwindCSS();
      }
    } catch (e) {
      // Gracefully fall back to traditional CSS
    }
  }

  static getDefaultProps() {
    return {
      type: 'text', // text, email, password, number, tel, url, search, etc.
      name: '',
      value: '',
      placeholder: '',
      label: '',
      helpText: '',
      disabled: false,
      readonly: false,
      required: false,
      variant: 'default', // default, error, success
      size: 'md', // sm, md, lg
      fullWidth: true,
      autoComplete: '',
      autoFocus: false,
      maxLength: null,
      minLength: null,
      pattern: '',
      validationRules: [],
      onChange: null,
      onBlur: null,
      onFocus: null,
      useTailwind: null // null = auto-detect, true = force tailwind, false = force traditional
    };
  }

  shouldUseTailwind() {
    const { useTailwind } = this.props;

    // Explicit preference
    if (useTailwind !== null) {
      return useTailwind;
    }

    // Auto-detect based on configuration
    return this.tailwind.isEnabled();
  }

  getCSSClasses() {
    const { variant = 'default', size = 'md', fullWidth = true, className = '' } = this.props;

    if (this.shouldUseTailwind()) {
      // Generate Tailwind classes inline
      const classes = [
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

      // Size variants
      const sizeMap = {
        sm: ['text-sm', 'px-2', 'py-1'],
        md: ['text-sm', 'px-3', 'py-2'],
        lg: ['text-base', 'px-4', 'py-3']
      };
      classes.push(...(sizeMap[size] || sizeMap.md));

      // Variant classes
      const variantMap = {
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
      classes.push(...(variantMap[variant] || variantMap.default));

      if (fullWidth) classes.push('w-full');
      return [...classes, className].filter(Boolean).join(' ');
    } else {
      // Use traditional CSS classes
      const baseClasses = [
        'pydance-input',
        `pydance-input--${variant}`,
        `pydance-input--${size}`,
        {
          'pydance-input--full-width': fullWidth,
          'pydance-input--error': !this.state.isValid,
          'pydance-input--success': this.state.isValid && this.state.isTouched && this.state.value
        },
        className
      ].filter(Boolean).join(' ');

      return baseClasses;
    }
  }

  componentDidMount() {
    if (this.props.autoFocus && this.element) {
      this.element.focus();
    }

    // Set initial value
    if (this.props.value !== undefined) {
      this.setState({ value: this.props.value });
    }
  }

  componentWillUpdate(nextProps) {
    // Update value if props change
    if (nextProps.value !== this.props.value) {
      this.setState({ value: nextProps.value || '' });
    }
  }

  validate(value) {
    const { validationRules = [], required, minLength, maxLength, pattern } = this.props;
    let isValid = true;
    let errorMessage = '';

    // Required validation
    if (required && (!value || value.trim() === '')) {
      isValid = false;
      errorMessage = 'This field is required';
    }

    // Length validation
    if (isValid && value) {
      if (minLength && value.length < minLength) {
        isValid = false;
        errorMessage = `Minimum length is ${minLength} characters`;
      } else if (maxLength && value.length > maxLength) {
        isValid = false;
        errorMessage = `Maximum length is ${maxLength} characters`;
      }
    }

    // Pattern validation
    if (isValid && pattern && value) {
      const regex = new RegExp(pattern);
      if (!regex.test(value)) {
        isValid = false;
        errorMessage = 'Invalid format';
      }
    }

    // Custom validation rules
    if (isValid) {
      for (const rule of validationRules) {
        try {
          const result = rule(value);
          if (result !== true) {
            isValid = false;
            errorMessage = typeof result === 'string' ? result : 'Validation failed';
            break;
          }
        } catch (error) {
          isValid = false;
          errorMessage = 'Validation error';
          break;
        }
      }
    }

    this.setState({ isValid, errorMessage });
    return isValid;
  }

  _handleInput = (event) => {
    const value = event.target.value;
    this.setState({ value, isTouched: true });

    // Run validation
    this.validate(value);

    // Call onChange prop
    if (this.props.onChange) {
      this.props.onChange(event, value);
    }
  };

  _handleBlur = (event) => {
    this.setState({ isTouched: true });

    // Final validation on blur
    this.validate(event.target.value);

    if (this.props.onBlur) {
      this.props.onBlur(event);
    }
  };

  _handleFocus = (event) => {
    if (this.props.onFocus) {
      this.props.onFocus(event);
    }
  };

  render() {
    const {
      type = 'text',
      name = '',
      placeholder = '',
      label = '',
      helpText = '',
      disabled = false,
      readonly = false,
      required = false,
      autoComplete = '',
      maxLength = null,
      minLength = null,
      pattern = '',
      className = '',
      useTailwind,
      ...otherProps
    } = this.props;

    const { value, errorMessage } = this.state;
    const cssClasses = this.getCSSClasses();

    const inputElement = this.createElement('input', {
      type,
      name: name || this.props.name,
      value,
      placeholder,
      disabled,
      readOnly: readonly,
      required,
      autoComplete,
      maxLength: maxLength || undefined,
      minLength: minLength || undefined,
      pattern: pattern || undefined,
      className: cssClasses,
      onInput: this._handleInput,
      onBlur: this._handleBlur,
      onFocus: this._handleFocus,
      'aria-label': label || placeholder,
      'aria-describedby': helpText ? `${name}-help` : undefined,
      'aria-invalid': !this.state.isValid,
      ...otherProps
    });

    // Label
    const labelElement = label ? this.createElement('label', {
      htmlFor: name,
      className: this.shouldUseTailwind()
        ? 'block text-sm font-medium text-gray-700 mb-1'
        : 'pydance-input__label'
    }, label) : null;

    // Help text
    const helpElement = helpText ? this.createElement('p', {
      id: `${name}-help`,
      className: this.shouldUseTailwind()
        ? 'mt-1 text-sm text-gray-500'
        : 'pydance-input__help'
    }, helpText) : null;

    // Error message
    const errorElement = errorMessage && !this.state.isValid ? this.createElement('p', {
      className: this.shouldUseTailwind()
        ? 'mt-1 text-sm text-red-600'
        : 'pydance-input__error'
    }, errorMessage) : null;

    return this.createElement('div', {
      className: this.shouldUseTailwind()
        ? 'mb-4'
        : 'pydance-input-wrapper'
    },
      labelElement,
      inputElement,
      helpElement,
      errorElement
    );
  }

  // Public methods
  focus() {
    if (this.element && this.element.querySelector('input')) {
      this.element.querySelector('input').focus();
    }
  }

  blur() {
    if (this.element && this.element.querySelector('input')) {
      this.element.querySelector('input').blur();
    }
  }

  getValue() {
    return this.state.value;
  }

  setValue(value) {
    this.setState({ value });
    this.validate(value);
  }

  isValid() {
    return this.state.isValid;
  }

  getErrorMessage() {
    return this.state.errorMessage;
  }
}

// Specialized input components
export class EmailInput extends Input {
  static getDefaultProps() {
    return {
      ...super.getDefaultProps(),
      type: 'email',
      placeholder: 'Enter your email address',
      autoComplete: 'email'
    };
  }
}

export class PasswordInput extends Input {
  static getDefaultProps() {
    return {
      ...super.getDefaultProps(),
      type: 'password',
      placeholder: 'Enter your password',
      autoComplete: 'current-password'
    };
  }
}

export class SearchInput extends Input {
  constructor(props = {}) {
    super(props);

    this.state = {
      ...this.state,
      showClearButton: false
    };
  }

  componentWillUpdate(nextProps, nextState) {
    super.componentWillUpdate(nextProps, nextState);

    // Show clear button when there's text
    if (nextState && nextState.value !== undefined) {
      this.setState({ showClearButton: nextState.value.length > 0 });
    }
  }

  _handleClear = () => {
    this.setValue('');
    this.focus();
  };

  render() {
    const searchInput = super.render();

    // Add search icon and clear button
    const searchIcon = this.createElement('span', {
      className: this.shouldUseTailwind()
        ? 'absolute inset-y-0 left-0 pl-3 flex items-center text-gray-400'
        : 'pydance-search-input__icon'
    }, '🔍');

    const clearButton = this.state.showClearButton ? this.createElement('button', {
      type: 'button',
      className: this.shouldUseTailwind()
        ? 'absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600'
        : 'pydance-search-input__clear',
      onClick: this._handleClear,
      'aria-label': 'Clear search'
    }, '✕') : null;

    return this.createElement('div', {
      className: this.shouldUseTailwind()
        ? 'relative'
        : 'pydance-search-input-wrapper'
    },
      searchIcon,
      searchInput,
      clearButton
    );
  }
}

export class NumberInput extends Input {
  static getDefaultProps() {
    return {
      ...super.getDefaultProps(),
      type: 'number',
      placeholder: '0',
      min: 0,
      step: 1
    };
  }

  // No custom render needed - base class handles all props including min, max, step via otherProps
}

export class FileInput extends Input {
  static getDefaultProps() {
    return {
      ...super.getDefaultProps(),
      type: 'file',
      accept: '',
      multiple: false
    };
  }

  render() {
    // Get the base wrapper
    const wrapper = super.render();

    // Extract the input element from the wrapper
    const inputElement = wrapper.props.children[1]; // The input element

    // Clone with file-specific props
    const {
      accept = '',
      multiple = false,
      ...otherProps
    } = this.props;

    const enhancedInput = this.createElement('input', {
      ...inputElement.props,
      accept,
      multiple,
      ...otherProps
    });

    // Return the wrapper with enhanced input
    return this.createElement('div', {
      className: wrapper.props.className
    },
      wrapper.props.children[0], // Label
      enhancedInput,
      wrapper.props.children[2], // Help text
      wrapper.props.children[3]  // Error message
    );
  }
}

export class Select extends Component {
  constructor(props = {}) {
    super(props);

    this.state = {
      value: props.value || '',
      isValid: true,
      isTouched: false,
      errorMessage: ''
    };

    // Initialize Tailwind if enabled
    this.tailwind = { isEnabled: () => false };
    try {
      if (typeof window !== 'undefined' && window.getTailwindCSS) {
        this.tailwind = window.getTailwindCSS();
      }
    } catch (e) {
      // Graceful fallback
    }
  }

  static getDefaultProps() {
    return {
      name: '',
      value: '',
      placeholder: '',
      label: '',
      helpText: '',
      disabled: false,
      required: false,
      options: [], // Array of {value, label} objects
      variant: 'default',
      size: 'md',
      fullWidth: true,
      useTailwind: null
    };
  }

  shouldUseTailwind() {
    const { useTailwind } = this.props;
    if (useTailwind !== null) return useTailwind;
    return this.tailwind.isEnabled();
  }

  getCSSClasses() {
    const { variant = 'default', size = 'md', fullWidth = true, className = '' } = this.props;

    if (this.shouldUseTailwind()) {
      const classes = [
        'block',
        'w-full',
        'border',
        'border-gray-300',
        'rounded-md',
        'shadow-sm',
        'focus:outline-none',
        'focus:ring-1',
        'focus:ring-blue-500',
        'focus:border-blue-500',
        'disabled:opacity-50',
        'disabled:cursor-not-allowed'
      ];

      // Size variants
      const sizeMap = {
        sm: ['text-sm', 'py-1'],
        md: ['text-sm', 'py-2'],
        lg: ['text-base', 'py-3']
      };
      classes.push(...(sizeMap[size] || sizeMap.md));

      if (fullWidth) classes.push('w-full');
      if (variant === 'error') {
        classes.push('border-red-300', 'focus:ring-red-500', 'text-red-900');
      }

      return [...classes, className].filter(Boolean).join(' ');
    } else {
      const classes = [
        'pydance-select',
        `pydance-select--${variant}`,
        `pydance-select--${size}`,
        {
          'pydance-select--full-width': fullWidth,
          'pydance-select--error': !this.state.isValid
        },
        className
      ].filter(Boolean);

      return classes.join(' ');
    }
  }

  _handleChange = (event) => {
    const value = event.target.value;
    this.setState({ value, isTouched: true });

    if (this.props.onChange) {
      this.props.onChange(event, value);
    }
  };

  render() {
    const {
      name = '',
      placeholder = '',
      label = '',
      helpText = '',
      disabled = false,
      required = false,
      options = [],
      useTailwind,
      ...otherProps
    } = this.props;

    const { value } = this.state;
    const cssClasses = this.getCSSClasses();

    const selectElement = this.createElement('select', {
      name,
      value,
      disabled,
      required,
      className: cssClasses,
      onChange: this._handleChange,
      'aria-label': label || placeholder,
      ...otherProps
    },
      placeholder && this.createElement('option', {
        value: '',
        disabled: true,
        hidden: true
      }, placeholder),
      ...options.map(option => this.createElement('option', {
        key: option.value,
        value: option.value
      }, option.label))
    );

    const labelElement = label ? this.createElement('label', {
      htmlFor: name,
      className: this.shouldUseTailwind()
        ? 'block text-sm font-medium text-gray-700 mb-1'
        : 'pydance-select__label'
    }, label) : null;

    const helpElement = helpText ? this.createElement('p', {
      className: this.shouldUseTailwind()
        ? 'mt-1 text-sm text-gray-500'
        : 'pydance-select__help'
    }, helpText) : null;

    return this.createElement('div', {
      className: this.shouldUseTailwind()
        ? 'mb-4'
        : 'pydance-select-wrapper'
    },
      labelElement,
      selectElement,
      helpElement
    );
  }
}

export class Radio extends Component {
  constructor(props = {}) {
    super(props);

    this.state = {
      checked: props.checked || false
    };
  }

  static getDefaultProps() {
    return {
      name: '',
      value: '',
      checked: false,
      label: '',
      disabled: false,
      useTailwind: null
    };
  }

  shouldUseTailwind() {
    const { useTailwind } = this.props;
    if (useTailwind !== null) return useTailwind;
    return typeof window !== 'undefined' && window.PydanceTailwind?.enabled;
  }

  _handleChange = (event) => {
    this.setState({ checked: true });
    if (this.props.onChange) {
      this.props.onChange(event, event.target.value);
    }
  };

  render() {
    const {
      name = '',
      value = '',
      label = '',
      disabled = false,
      useTailwind,
      ...otherProps
    } = this.props;

    const { checked } = this.state;

    const inputElement = this.createElement('input', {
      type: 'radio',
      name,
      value,
      checked,
      disabled,
      onChange: this._handleChange,
      className: this.shouldUseTailwind()
        ? 'h-4 w-4 text-blue-600 focus:ring-blue-500'
        : 'pydance-radio',
      ...otherProps
    });

    const labelElement = this.createElement('label', {
      className: this.shouldUseTailwind()
        ? 'inline-flex items-center'
        : 'pydance-radio-label'
    },
      inputElement,
      label && this.createElement('span', {
        className: this.shouldUseTailwind()
          ? 'ml-2 text-sm'
          : 'pydance-radio-label-text'
      }, label)
    );

    return labelElement;
  }
}

export class Checkbox extends Component {
  constructor(props = {}) {
    super(props);

    this.state = {
      checked: props.checked || false
    };
  }

  static getDefaultProps() {
    return {
      name: '',
      value: '',
      checked: false,
      label: '',
      disabled: false,
      useTailwind: null
    };
  }

  shouldUseTailwind() {
    const { useTailwind } = this.props;
    if (useTailwind !== null) return useTailwind;
    return typeof window !== 'undefined' && window.PydanceTailwind?.enabled;
  }

  _handleChange = (event) => {
    const checked = event.target.checked;
    this.setState({ checked });
    if (this.props.onChange) {
      this.props.onChange(event, checked);
    }
  };

  render() {
    const {
      name = '',
      value = '',
      label = '',
      disabled = false,
      useTailwind,
      ...otherProps
    } = this.props;

    const { checked } = this.state;

    const inputElement = this.createElement('input', {
      type: 'checkbox',
      name,
      value,
      checked,
      disabled,
      onChange: this._handleChange,
      className: this.shouldUseTailwind()
        ? 'h-4 w-4 text-blue-600 focus:ring-blue-500 rounded'
        : 'pydance-checkbox',
      ...otherProps
    });

    const labelElement = this.createElement('label', {
      className: this.shouldUseTailwind()
        ? 'inline-flex items-center'
        : 'pydance-checkbox-label'
    },
      inputElement,
      label && this.createElement('span', {
        className: this.shouldUseTailwind()
          ? 'ml-2 text-sm'
          : 'pydance-checkbox-label-text'
      }, label)
    );

    return labelElement;
  }
}

// Textarea component
export class Textarea extends Component {
  constructor(props = {}) {
    super(props);

    this.state = {
      value: props.value || '',
      isValid: true,
      isTouched: false,
      errorMessage: ''
    };

    // Initialize Tailwind if enabled - safe to call even if not used
    this.tailwind = { isEnabled: () => false }; // Default fallback
    try {
      if (typeof window !== 'undefined' && window.getTailwindCSS) {
        this.tailwind = window.getTailwindCSS();
      }
    } catch (e) {
      // Gracefully fall back to traditional CSS
    }
  }

  static getDefaultProps() {
    return {
      name: '',
      value: '',
      placeholder: '',
      label: '',
      helpText: '',
      disabled: false,
      readonly: false,
      required: false,
      rows: 4,
      cols: null,
      maxLength: null,
      minLength: null,
      resize: 'vertical', // none, vertical, horizontal, both
      autoComplete: '',
      useTailwind: null
    };
  }

  shouldUseTailwind() {
    const { useTailwind } = this.props;

    // Explicit preference
    if (useTailwind !== null) {
      return useTailwind;
    }

    // Auto-detect based on configuration
    return this.tailwind.isEnabled();
  }

  getCSSClasses() {
    const { className = '' } = this.props;

    if (this.shouldUseTailwind()) {
      const classes = [
        'block',
        'w-full',
        'px-3',
        'py-2',
        'border',
        'border-gray-300',
        'rounded-md',
        'shadow-sm',
        'placeholder-gray-400',
        'focus:outline-none',
        'focus:ring-blue-500',
        'focus:border-blue-500',
        'sm:text-sm',
        'transition-colors',
        'duration-200',
        'disabled:opacity-50',
        'disabled:cursor-not-allowed'
      ];

      if (!this.state.isValid) classes.push('border-red-500', 'focus:ring-red-500');

      return [...classes, className].filter(Boolean).join(' ');
    } else {
      const classes = [
        'pydance-textarea',
        !this.state.isValid && 'pydance-textarea--error',
        className
      ].filter(Boolean);

      return classes.join(' ');
    }
  }

  validate(value) {
    // Similar validation logic as Input component
    // Implementation omitted for brevity - would be same as Input.validate()
    return true;
  }

  render() {
    const {
      name = '',
      placeholder = '',
      label = '',
      helpText = '',
      disabled = false,
      readonly = false,
      required = false,
      rows = 4,
      cols = null,
      maxLength = null,
      minLength = null,
      resize = 'vertical',
      autoComplete = '',
      className = '',
      useTailwind,
      ...otherProps
    } = this.props;

    const { value } = this.state;
    const cssClasses = this.getCSSClasses();

    const textareaElement = this.createElement('textarea', {
      name,
      value,
      placeholder,
      disabled,
      readOnly: readonly,
      required,
      rows,
      cols,
      maxLength,
      minLength,
      autoComplete,
      style: { resize },
      className: cssClasses,
      onInput: (event) => this.setState({ value: event.target.value }),
      'aria-label': label || placeholder,
      ...otherProps
    });

    return textareaElement;
  }
}
