/**
 * Input - Reusable Input Component
 * Provides flexible input fields with validation, formatting, and various input types
 */

import { Component } from '../core/Component.js';

export class Input extends Component {
  constructor(props = {}) {
    super(props);

    this.state = {
      value: props.value || props.defaultValue || '',
      error: null,
      touched: false,
      focused: false,
      valid: true
    };

    this._inputRef = null;
  }

  static getDefaultProps() {
    return {
      type: 'text',
      placeholder: '',
      disabled: false,
      required: false,
      readonly: false,
      size: 'md',
      variant: 'default',
      fullWidth: false,
      clearable: false,
      showPassword: false,
      minLength: null,
      maxLength: null,
      pattern: null,
      autoComplete: 'off',
      autoFocus: false,
      step: null,
      min: null,
      max: null,
      multiple: false,
      accept: null,
      children: null
    };
  }

  componentDidMount() {
    if (this.props.autoFocus && this._inputRef) {
      this._inputRef.focus();
    }

    // Set up validation
    this._setupValidation();
  }

  componentWillUpdate(nextProps, nextState) {
    // Update value if controlled
    if (nextProps.value !== undefined && nextProps.value !== this.props.value) {
      this.setState({ value: nextProps.value });
    }
  }

  _setupValidation() {
    if (this.props.validation) {
      this._validate = this.props.validation;
    } else {
      this._validate = this._defaultValidation.bind(this);
    }
  }

  _defaultValidation(value) {
    const { required, minLength, maxLength, pattern, type } = this.props;
    let error = null;

    if (required && (!value || value.trim() === '')) {
      error = 'This field is required';
    } else if (minLength && value.length < minLength) {
      error = `Minimum length is ${minLength} characters`;
    } else if (maxLength && value.length > maxLength) {
      error = `Maximum length is ${maxLength} characters`;
    } else if (pattern && !new RegExp(pattern).test(value)) {
      error = 'Invalid format';
    } else if (type === 'email' && value && !this._isValidEmail(value)) {
      error = 'Invalid email address';
    } else if (type === 'url' && value && !this._isValidUrl(value)) {
      error = 'Invalid URL';
    }

    return error;
  }

  _isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  _isValidUrl(url) {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  }

  render() {
    const {
      type = 'text',
      placeholder = '',
      disabled = false,
      required = false,
      readonly = false,
      size = 'md',
      variant = 'default',
      fullWidth = false,
      clearable = false,
      showPassword = false,
      minLength,
      maxLength,
      pattern,
      autoComplete = 'off',
      step,
      min,
      max,
      multiple,
      accept,
      className = '',
      onChange,
      onFocus,
      onBlur,
      onKeyDown,
      onKeyUp,
      ...otherProps
    } = this.props;

    const { value, error, touched, focused, valid } = this.state;

    const inputType = type === 'password' && showPassword ? 'text' : type;

    const baseClasses = [
      'pydance-input',
      `pydance-input--${size}`,
      `pydance-input--${variant}`,
      {
        'pydance-input--disabled': disabled,
        'pydance-input--readonly': readonly,
        'pydance-input--error': error && touched,
        'pydance-input--success': !error && touched && value,
        'pydance-input--focused': focused,
        'pydance-input--full-width': fullWidth,
        'pydance-input--clearable': clearable && value
      },
      className
    ].filter(Boolean).join(' ');

    return this.createElement('div', { className: 'pydance-input-wrapper' },
      // Input group
      this.createElement('div', { className: 'pydance-input-group' },
        // Prepend slot
        this.props.prepend && this.createElement('div', { className: 'pydance-input__prepend' }, this.props.prepend),

        // Input element
        this.createElement('input', {
          ref: (el) => this._inputRef = el,
          type: inputType,
          value: value,
          placeholder,
          disabled,
          required,
          readOnly: readonly,
          minLength,
          maxLength,
          pattern,
          autoComplete,
          step,
          min,
          max,
          multiple,
          accept,
          className: baseClasses,
          onChange: this._handleChange.bind(this),
          onFocus: this._handleFocus.bind(this),
          onBlur: this._handleBlur.bind(this),
          onKeyDown: this._handleKeyDown.bind(this),
          onKeyUp: this._handleKeyUp.bind(this),
          ...otherProps
        }),

        // Clear button
        clearable && value && this.createElement('button', {
          type: 'button',
          className: 'pydance-input__clear',
          onClick: this._handleClear.bind(this),
          'aria-label': 'Clear input'
        }, '×'),

        // Password toggle
        type === 'password' && this.createElement('button', {
          type: 'button',
          className: 'pydance-input__password-toggle',
          onClick: this._togglePasswordVisibility.bind(this),
          'aria-label': showPassword ? 'Hide password' : 'Show password'
        }, showPassword ? '🙈' : '👁️'),

        // Append slot
        this.props.append && this.createElement('div', { className: 'pydance-input__append' }, this.props.append)
      ),

      // Error message
      error && touched && this.createElement('div', { className: 'pydance-input__error' }, error),

      // Helper text
      this.props.helperText && this.createElement('div', { className: 'pydance-input__helper' }, this.props.helperText)
    );
  }

  _handleChange(event) {
    const value = event.target.value;
    const error = this._validate(value);

    this.setState({
      value,
      error,
      touched: true,
      valid: !error
    });

    if (this.props.onChange) {
      this.props.onChange(event, { value, error, valid: !error });
    }
  }

  _handleFocus(event) {
    this.setState({ focused: true });

    if (this.props.onFocus) {
      this.props.onFocus(event);
    }
  }

  _handleBlur(event) {
    this.setState({ focused: false, touched: true });

    if (this.props.onBlur) {
      this.props.onBlur(event);
    }
  }

  _handleKeyDown(event) {
    if (this.props.onKeyDown) {
      this.props.onKeyDown(event);
    }
  }

  _handleKeyUp(event) {
    if (this.props.onKeyUp) {
      this.props.onKeyUp(event);
    }
  }

  _handleClear() {
    this.setState({ value: '', error: null, touched: true, valid: true });
    if (this._inputRef) {
      this._inputRef.focus();
    }

    if (this.props.onChange) {
      this.props.onChange({ target: { value: '' } }, { value: '', error: null, valid: true });
    }
  }

  _togglePasswordVisibility() {
    this.setState({ showPassword: !this.state.showPassword });
  }

  // Public methods
  getValue() {
    return this.state.value;
  }

  setValue(value) {
    const error = this._validate(value);
    this.setState({ value, error, valid: !error });
  }

  getError() {
    return this.state.error;
  }

  isValid() {
    return this.state.valid;
  }

  focus() {
    if (this._inputRef) {
      this._inputRef.focus();
    }
  }

  blur() {
    if (this._inputRef) {
      this._inputRef.blur();
    }
  }

  validate() {
    const error = this._validate(this.state.value);
    this.setState({ error, valid: !error, touched: true });
    return !error;
  }
}

// Textarea component
export class Textarea extends Component {
  constructor(props = {}) {
    super(props);

    this.state = {
      value: props.value || props.defaultValue || '',
      error: null,
      touched: false,
      focused: false,
      valid: true
    };

    this._textareaRef = null;
  }

  static getDefaultProps() {
    return {
      placeholder: '',
      disabled: false,
      required: false,
      readonly: false,
      rows: 3,
      cols: null,
      minLength: null,
      maxLength: null,
      resize: 'vertical', // none, vertical, horizontal, both
      autoComplete: 'off',
      autoFocus: false,
      children: null
    };
  }

  render() {
    const {
      placeholder = '',
      disabled = false,
      required = false,
      readonly = false,
      rows = 3,
      cols,
      minLength,
      maxLength,
      resize = 'vertical',
      autoComplete = 'off',
      className = '',
      onChange,
      onFocus,
      onBlur,
      onKeyDown,
      onKeyUp,
      ...otherProps
    } = this.props;

    const { value, error, touched, focused } = this.state;

    const baseClasses = [
      'pydance-textarea',
      `pydance-textarea--resize-${resize}`,
      {
        'pydance-textarea--disabled': disabled,
        'pydance-textarea--readonly': readonly,
        'pydance-textarea--error': error && touched,
        'pydance-textarea--focused': focused
      },
      className
    ].filter(Boolean).join(' ');

    return this.createElement('div', { className: 'pydance-textarea-wrapper' },
      this.createElement('textarea', {
        ref: (el) => this._textareaRef = el,
        value,
        placeholder,
        disabled,
        required,
        readOnly: readonly,
        rows,
        cols,
        minLength,
        maxLength,
        autoComplete,
        className: baseClasses,
        onChange: this._handleChange.bind(this),
        onFocus: this._handleFocus.bind(this),
        onBlur: this._handleBlur.bind(this),
        onKeyDown: this._handleKeyDown.bind(this),
        onKeyUp: this._handleKeyUp.bind(this),
        ...otherProps
      }),

      // Character counter
      maxLength && this.createElement('div', { className: 'pydance-textarea__counter' },
        `${value.length}/${maxLength}`
      ),

      // Error message
      error && touched && this.createElement('div', { className: 'pydance-textarea__error' }, error)
    );
  }

  _handleChange(event) {
    const value = event.target.value;
    this.setState({ value });

    if (this.props.onChange) {
      this.props.onChange(event);
    }
  }

  _handleFocus(event) {
    this.setState({ focused: true });

    if (this.props.onFocus) {
      this.props.onFocus(event);
    }
  }

  _handleBlur(event) {
    this.setState({ focused: false, touched: true });

    if (this.props.onBlur) {
      this.props.onBlur(event);
    }
  }

  _handleKeyDown(event) {
    if (this.props.onKeyDown) {
      this.props.onKeyDown(event);
    }
  }

  _handleKeyUp(event) {
    if (this.props.onKeyUp) {
      this.props.onKeyUp(event);
    }
  }

  getValue() {
    return this.state.value;
  }

  setValue(value) {
    this.setState({ value });
  }

  focus() {
    if (this._textareaRef) {
      this._textareaRef.focus();
    }
  }

  blur() {
    if (this._textareaRef) {
      this._textareaRef.blur();
    }
  }
}

// Select component
export class Select extends Component {
  constructor(props = {}) {
    super(props);

    this.state = {
      value: props.value || props.defaultValue || '',
      isOpen: false,
      focused: false,
      error: null,
      touched: false
    };

    this._selectRef = null;
  }

  static getDefaultProps() {
    return {
      placeholder: 'Select an option',
      disabled: false,
      required: false,
      multiple: false,
      searchable: false,
      clearable: false,
      size: 'md',
      options: [],
      children: null
    };
  }

  render() {
    const {
      placeholder = 'Select an option',
      disabled = false,
      required = false,
      multiple = false,
      searchable = false,
      clearable = false,
      size = 'md',
      options = [],
      className = '',
      onChange,
      ...otherProps
    } = this.props;

    const { value, isOpen, focused, error, touched } = this.state;

    const baseClasses = [
      'pydance-select',
      `pydance-select--${size}`,
      {
        'pydance-select--disabled': disabled,
        'pydance-select--open': isOpen,
        'pydance-select--focused': focused,
        'pydance-select--error': error && touched,
        'pydance-select--multiple': multiple
      },
      className
    ].filter(Boolean).join(' ');

    const selectedOption = options.find(opt => opt.value === value);
    const displayValue = selectedOption ? selectedOption.label : placeholder;

    return this.createElement('div', { className: 'pydance-select-wrapper' },
      this.createElement('div', { className: baseClasses },
        // Trigger button
        this.createElement('button', {
          type: 'button',
          className: 'pydance-select__trigger',
          disabled,
          onClick: this._toggleDropdown.bind(this),
          'aria-expanded': isOpen,
          'aria-haspopup': 'listbox'
        },
          this.createElement('span', { className: 'pydance-select__value' }, displayValue),
          this.createElement('span', { className: 'pydance-select__arrow' }, isOpen ? '▲' : '▼')
        ),

        // Dropdown
        isOpen && this.createElement('div', { className: 'pydance-select__dropdown' },
          // Search input
          searchable && this.createElement('input', {
            type: 'text',
            className: 'pydance-select__search',
            placeholder: 'Search...',
            onChange: this._handleSearch.bind(this)
          }),

          // Options list
          this.createElement('ul', {
            className: 'pydance-select__options',
            role: 'listbox'
          },
            options.map(option => this.createElement('li', {
              key: option.value,
              className: `pydance-select__option ${option.value === value ? 'pydance-select__option--selected' : ''}`,
              onClick: () => this._selectOption(option),
              role: 'option',
              'aria-selected': option.value === value
            }, option.label))
          )
        )
      ),

      // Error message
      error && touched && this.createElement('div', { className: 'pydance-select__error' }, error)
    );
  }

  _toggleDropdown() {
    if (this.props.disabled) return;
    this.setState({ isOpen: !this.state.isOpen });
  }

  _selectOption(option) {
    this.setState({
      value: option.value,
      isOpen: false,
      touched: true
    });

    if (this.props.onChange) {
      this.props.onChange({ target: { value: option.value } }, option);
    }
  }

  _handleSearch(event) {
    // Implement search filtering
    console.log('Search:', event.target.value);
  }

  getValue() {
    return this.state.value;
  }

  setValue(value) {
    this.setState({ value });
  }
}

// CSS Styles
const styles = `
// Input styles
.pydance-input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.pydance-input-group {
  position: relative;
  display: flex;
  align-items: center;
}

.pydance-input {
  flex: 1;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--pydance-border);
  border-radius: var(--pydance-radius-md);
  background: var(--pydance-background);
  color: var(--pydance-text-primary);
  font-family: var(--pydance-font-family);
  font-size: var(--pydance-font-size-sm);
  line-height: 1.5;
  transition: all 0.2s ease;
}

.pydance-input:focus {
  outline: none;
  border-color: var(--pydance-primary);
  box-shadow: 0 0 0 3px var(--pydance-primary-light);
}

.pydance-input--error {
  border-color: var(--pydance-error);
}

.pydance-input--error:focus {
  box-shadow: 0 0 0 3px var(--pydance-error-light);
}

.pydance-input--success {
  border-color: var(--pydance-success);
}

.pydance-input--disabled {
  background: var(--pydance-background-secondary);
  color: var(--pydance-text-tertiary);
  cursor: not-allowed;
}

.pydance-input--readonly {
  background: var(--pydance-background-secondary);
  cursor: default;
}

.pydance-input__prepend,
.pydance-input__append {
  display: flex;
  align-items: center;
  padding: 0 0.75rem;
  color: var(--pydance-text-secondary);
}

.pydance-input__clear,
.pydance-input__password-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  background: none;
  border: none;
  color: var(--pydance-text-secondary);
  cursor: pointer;
  border-radius: var(--pydance-radius-sm);
  transition: all 0.2s ease;
}

.pydance-input__clear:hover,
.pydance-input__password-toggle:hover {
  background: var(--pydance-background-secondary);
  color: var(--pydance-text-primary);
}

.pydance-input__error {
  font-size: var(--pydance-font-size-xs);
  color: var(--pydance-error);
  margin-top: 0.25rem;
}

.pydance-input__helper {
  font-size: var(--pydance-font-size-xs);
  color: var(--pydance-text-secondary);
  margin-top: 0.25rem;
}

// Textarea styles
.pydance-textarea-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.pydance-textarea {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--pydance-border);
  border-radius: var(--pydance-radius-md);
  background: var(--pydance-background);
  color: var(--pydance-text-primary);
  font-family: var(--pydance-font-family);
  font-size: var(--pydance-font-size-sm);
  line-height: 1.5;
  resize: vertical;
  transition: all 0.2s ease;
  min-height: 80px;
}

.pydance-textarea:focus {
  outline: none;
  border-color: var(--pydance-primary);
  box-shadow: 0 0 0 3px var(--pydance-primary-light);
}

.pydance-textarea--error {
  border-color: var(--pydance-error);
}

.pydance-textarea--resize-none {
  resize: none;
}

.pydance-textarea--resize-horizontal {
  resize: horizontal;
}

.pydance-textarea--resize-vertical {
  resize: vertical;
}

.pydance-textarea--resize-both {
  resize: both;
}

.pydance-textarea__counter {
  align-self: flex-end;
  font-size: var(--pydance-font-size-xs);
  color: var(--pydance-text-tertiary);
}

.pydance-textarea__error {
  font-size: var(--pydance-font-size-xs);
  color: var(--pydance-error);
}

// Select styles
.pydance-select-wrapper {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.pydance-select {
  position: relative;
}

.pydance-select__trigger {
  width: 100%;
  padding: 0.5rem 2.5rem 0.5rem 0.75rem;
  border: 1px solid var(--pydance-border);
  border-radius: var(--pydance-radius-md);
  background: var(--pydance-background);
  color: var(--pydance-text-primary);
  font-family: var(--pydance-font-family);
  font-size: var(--pydance-font-size-sm);
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.pydance-select__trigger:focus {
  outline: none;
  border-color: var(--pydance-primary);
  box-shadow: 0 0 0 3px var(--pydance-primary-light);
}

.pydance-select__trigger:disabled {
  background: var(--pydance-background-secondary);
  color: var(--pydance-text-tertiary);
  cursor: not-allowed;
}

.pydance-select__value {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pydance-select__arrow {
  font-size: 0.75rem;
  color: var(--pydance-text-secondary);
  transition: transform 0.2s ease;
}

.pydance-select--open .pydance-select__arrow {
  transform: rotate(180deg);
}

.pydance-select__dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 1000;
  margin-top: 0.25rem;
  padding: 0.25rem 0;
  border: 1px solid var(--pydance-border);
  border-radius: var(--pydance-radius-md);
  background: var(--pydance-surface);
  box-shadow: var(--pydance-shadow-lg);
  max-height: 200px;
  overflow-y: auto;
}

.pydance-select__search {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: none;
  border-bottom: 1px solid var(--pydance-border-light);
  background: transparent;
  color: var(--pydance-text-primary);
  font-size: var(--pydance-font-size-sm);
}

.pydance-select__options {
  list-style: none;
  margin: 0;
  padding: 0;
}

.pydance-select__option {
  padding: 0.5rem 0.75rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.pydance-select__option:hover {
  background: var(--pydance-background-secondary);
}

.pydance-select__option--selected {
  background: var(--pydance-primary-light);
  color: var(--pydance-primary-dark);
}

.pydance-select__error {
  font-size: var(--pydance-font-size-xs);
  color: var(--pydance-error);
}

// Responsive adjustments
@media (max-width: 768px) {
  .pydance-input,
  .pydance-textarea,
  .pydance-select__trigger {
    font-size: var(--pydance-font-size-base);
  }

  .pydance-input__prepend,
  .pydance-input__append {
    padding: 0 0.5rem;
  }
}
`;

// Inject styles
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = styles;
  document.head.appendChild(style);
}
