/**
 * Button - Reusable Button Component
 * Provides a flexible button component with different variants,
 * sizes, states, and loading indicators
 */

import { Component } from '/core/Component.js';

export class Button extends Component {
  constructor(props = {}) {
    super(props);

    this.state = {
      loading: props.loading || false,
      disabled: props.disabled || false
    };
  }

  static getDefaultProps() {
    return {
      variant: 'primary', // primary, secondary, outline, ghost, link
      size: 'md', // xs, sm, md, lg, xl
      type: 'button', // button, submit, reset
      disabled: false,
      loading: false,
      fullWidth: false,
      rounded: false,
      icon: null,
      iconPosition: 'left', // left, right
      children: null
    };
  }

  componentWillUpdate(nextProps, nextState) {
    // Update loading state when props change
    if (nextProps.loading !== this.props.loading) {
      this.setState({ loading: nextProps.loading });
    }

    if (nextProps.disabled !== this.props.disabled) {
      this.setState({ disabled: nextProps.disabled });
    }
  }

  render() {
    const {
      variant = 'primary',
      size = 'md',
      type = 'button',
      disabled = false,
      loading = false,
      fullWidth = false,
      rounded = false,
      icon = null,
      iconPosition = 'left',
      children,
      className = '',
      onClick,
      ...otherProps
    } = this.props;

    const isDisabled = disabled || loading || this.state.disabled;
    const isLoading = loading || this.state.loading;

    const baseClasses = [
      'pydance-button',
      `pydance-button--${variant}`,
      `pydance-button--${size}`,
      {
        'pydance-button--disabled': isDisabled,
        'pydance-button--loading': isLoading,
        'pydance-button--full-width': fullWidth,
        'pydance-button--rounded': rounded,
        'pydance-button--icon-only': !children && icon
      },
      className
    ].filter(Boolean).join(' ');

    return this.createElement('button', {
      type,
      className: baseClasses,
      disabled: isDisabled,
      onClick: this._handleClick.bind(this),
      'aria-disabled': isDisabled,
      ...otherProps
    },
      // Loading spinner
      isLoading && this.createElement('span', { className: 'pydance-button__spinner' }),

      // Icon (left)
      icon && iconPosition === 'left' && !isLoading && this.createElement('span', {
        className: 'pydance-button__icon pydance-button__icon--left'
      }, icon),

      // Content
      this.createElement('span', {
        className: 'pydance-button__content',
        style: isLoading ? { opacity: 0 } : {}
      },
        children
      ),

      // Icon (right)
      icon && iconPosition === 'right' && !isLoading && this.createElement('span', {
        className: 'pydance-button__icon pydance-button__icon--right'
      }, icon)
    );
  }

  _handleClick(event) {
    if (this.state.disabled || this.state.loading) {
      event.preventDefault();
      return;
    }

    if (this.props.onClick) {
      this.props.onClick(event);
    }
  }

  // Public methods
  setLoading(loading) {
    this.setState({ loading });
  }

  setDisabled(disabled) {
    this.setState({ disabled });
  }

  focus() {
    if (this.element) {
      this.element.focus();
    }
  }

  blur() {
    if (this.element) {
      this.element.blur();
    }
  }
}

// Button group component
export class ButtonGroup extends Component {
  constructor(props = {}) {
    super(props);

    this.state = {
      selectedIndex: props.selectedIndex || 0,
      size: props.size || 'md',
      variant: props.variant || 'outline'
    };
  }

  render() {
    const { children, className = '', ...otherProps } = this.props;
    const { size, variant } = this.state;

    return this.createElement('div', {
      className: `pydance-button-group pydance-button-group--${size} pydance-button-group--${variant} ${className}`,
      role: 'group',
      ...otherProps
    },
      children.map((child, index) => {
        if (!child) return null;

        return this.createElement(child.type, {
          ...child.props,
          key: index,
          size: size,
          variant: variant,
          className: `${child.props.className || ''} pydance-button-group__item`,
          onClick: (event) => {
            this.setState({ selectedIndex: index });
            if (child.props.onClick) {
              child.props.onClick(event);
            }
          }
        }, child.props.children);
      })
    );
  }
}

// Icon button component
export class IconButton extends Component {
  constructor(props = {}) {
    super(props);

    this.state = {
      loading: props.loading || false
    };
  }

  render() {
    const { icon, children, className = '', ...otherProps } = this.props;
    const { loading } = this.state;

    return this.createElement(Button, {
      className: `pydance-icon-button ${className}`,
      icon: loading ? null : icon,
      ...otherProps
    },
      loading && this.createElement('span', { className: 'pydance-icon-button__spinner' }),
      children
    );
  }
}

// Floating action button
export class FloatingActionButton extends Component {
  constructor(props = {}) {
    super(props);

    this.state = {
      extended: props.extended || false,
      position: props.position || 'bottom-right'
    };
  }

  render() {
    const { icon, children, className = '', ...otherProps } = this.props;
    const { extended, position } = this.state;

    return this.createElement('button', {
      className: `pydance-fab pydance-fab--${position} ${extended ? 'pydance-fab--extended' : ''} ${className}`,
      ...otherProps
    },
      this.createElement('span', { className: 'pydance-fab__icon' }, icon),
      extended && this.createElement('span', { className: 'pydance-fab__label' }, children)
    );
  }
}

// CSS Styles
const styles = `
  .pydance-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border: 1px solid transparent;
    border-radius: var(--pydance-radius-md);
    font-family: var(--pydance-font-family);
    font-size: var(--pydance-font-size-sm);
    font-weight: var(--pydance-font-weight-medium);
    line-height: 1.5;
    text-decoration: none;
    cursor: pointer;
    transition: all 0.2s ease;
    position: relative;
    overflow: hidden;
    user-select: none;
    white-space: nowrap;
  }

  .pydance-button:focus {
    outline: 2px solid var(--pydance-focus);
    outline-offset: 2px;
  }

  .pydance-button:disabled,
  .pydance-button--disabled {
    opacity: 0.6;
    cursor: not-allowed;
    pointer-events: none;
  }

  .pydance-button--loading {
    color: transparent;
    pointer-events: none;
  }

  .pydance-button__spinner {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 1rem;
    height: 1rem;
    border: 2px solid transparent;
    border-top: 2px solid currentColor;
    border-radius: 50%;
    animation: pydance-button-spin 1s linear infinite;
  }

  .pydance-button__content {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .pydance-button__icon {
    display: flex;
    align-items: center;
    font-size: 1rem;
  }

  /* Variants */
  .pydance-button--primary {
    background: var(--pydance-primary);
    color: white;
    border-color: var(--pydance-primary);
  }

  .pydance-button--primary:hover:not(.pydance-button--disabled) {
    background: var(--pydance-primary-hover);
    border-color: var(--pydance-primary-hover);
  }

  .pydance-button--secondary {
    background: var(--pydance-secondary);
    color: white;
    border-color: var(--pydance-secondary);
  }

  .pydance-button--secondary:hover:not(.pydance-button--disabled) {
    background: var(--pydance-secondary-hover);
    border-color: var(--pydance-secondary-hover);
  }

  .pydance-button--outline {
    background: transparent;
    color: var(--pydance-primary);
    border-color: var(--pydance-primary);
  }

  .pydance-button--outline:hover:not(.pydance-button--disabled) {
    background: var(--pydance-primary-light);
    color: var(--pydance-primary-dark);
  }

  .pydance-button--ghost {
    background: transparent;
    color: var(--pydance-primary);
    border-color: transparent;
  }

  .pydance-button--ghost:hover:not(.pydance-button--disabled) {
    background: var(--pydance-primary-light);
  }

  .pydance-button--link {
    background: transparent;
    color: var(--pydance-primary);
    border-color: transparent;
    text-decoration: underline;
    padding: 0.25rem 0;
  }

  .pydance-button--link:hover:not(.pydance-button--disabled) {
    color: var(--pydance-primary-hover);
  }

  /* Sizes */
  .pydance-button--xs {
    padding: 0.25rem 0.5rem;
    font-size: var(--pydance-font-size-xs);
  }

  .pydance-button--sm {
    padding: 0.375rem 0.75rem;
    font-size: var(--pydance-font-size-xs);
  }

  .pydance-button--md {
    padding: 0.5rem 1rem;
    font-size: var(--pydance-font-size-sm);
  }

  .pydance-button--lg {
    padding: 0.75rem 1.5rem;
    font-size: var(--pydance-font-size-base);
  }

  .pydance-button--xl {
    padding: 1rem 2rem;
    font-size: var(--pydance-font-size-lg);
  }

  /* Full width */
  .pydance-button--full-width {
    width: 100%;
  }

  /* Rounded */
  .pydance-button--rounded {
    border-radius: var(--pydance-radius-full);
  }

  /* Icon only */
  .pydance-button--icon-only {
    padding: 0.5rem;
    width: auto;
    aspect-ratio: 1;
  }

  /* Button group */
  .pydance-button-group {
    display: inline-flex;
    border-radius: var(--pydance-radius-md);
    overflow: hidden;
    box-shadow: var(--pydance-shadow-sm);
  }

  .pydance-button-group__item {
    border-radius: 0;
    border-right-width: 0;
  }

  .pydance-button-group__item:first-child {
    border-top-left-radius: var(--pydance-radius-md);
    border-bottom-left-radius: var(--pydance-radius-md);
  }

  .pydance-button-group__item:last-child {
    border-top-right-radius: var(--pydance-radius-md);
    border-bottom-right-radius: var(--pydance-radius-md);
    border-right-width: 1px;
  }

  .pydance-button-group__item:only-child {
    border-radius: var(--pydance-radius-md);
  }

  /* Floating action button */
  .pydance-fab {
    position: fixed;
    bottom: 2rem;
    right: 2rem;
    width: 56px;
    height: 56px;
    border-radius: 50%;
    background: var(--pydance-primary);
    color: white;
    border: none;
    cursor: pointer;
    box-shadow: var(--pydance-shadow-lg);
    transition: all 0.3s ease;
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .pydance-fab:hover {
    background: var(--pydance-primary-hover);
    transform: scale(1.1);
    box-shadow: var(--pydance-shadow-xl);
  }

  .pydance-fab--extended {
    width: auto;
    height: auto;
    border-radius: var(--pydance-radius-full);
    padding: 0 1.5rem;
    gap: 0.5rem;
  }

  .pydance-fab__icon {
    font-size: 1.5rem;
  }

  .pydance-fab__label {
    font-size: var(--pydance-font-size-sm);
    font-weight: var(--pydance-font-weight-medium);
  }

  .pydance-fab--bottom-right {
    bottom: 2rem;
    right: 2rem;
  }

  .pydance-fab--bottom-left {
    bottom: 2rem;
    left: 2rem;
  }

  .pydance-fab--top-right {
    top: 2rem;
    right: 2rem;
  }

  .pydance-fab--top-left {
    top: 2rem;
    left: 2rem;
  }

  /* Icon button */
  .pydance-icon-button {
    padding: 0.5rem;
    border-radius: var(--pydance-radius-md);
  }

  .pydance-icon-button__spinner {
    width: 1rem;
    height: 1rem;
  }

  /* Animations */
  @keyframes pydance-button-spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  /* Responsive */
  @media (max-width: 768px) {
    .pydance-button {
      font-size: var(--pydance-font-size-base);
      padding: 0.75rem 1rem;
    }

    .pydance-button--xs,
    .pydance-button--sm {
      font-size: var(--pydance-font-size-sm);
      padding: 0.5rem 0.75rem;
    }

    .pydance-fab {
      bottom: 1rem;
      right: 1rem;
      width: 48px;
      height: 48px;
    }

    .pydance-fab--extended {
      padding: 0 1rem;
    }
  }
`;

// Inject styles
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = styles;
  document.head.appendChild(style);
}
