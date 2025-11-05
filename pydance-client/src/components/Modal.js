/**
 * Modal - Reusable Modal Component
 * Provides flexible modal dialogs with various sizes, animations, and accessibility features
 */

import { Component } from '../core/Component.js';

export class Modal extends Component {
  constructor(props = {}) {
    super(props);

    this.state = {
      isOpen: props.isOpen || false,
      isAnimating: false,
      animationType: 'fade', // fade, slide-up, slide-down, slide-left, slide-right, scale, zoom
      zIndex: 1000
    };

    this._modalRef = null;
    this._overlayRef = null;
    this._previouslyFocusedElement = null;
  }

  static getDefaultProps() {
    return {
      isOpen: false,
      size: 'md', // xs, sm, md, lg, xl, full
      variant: 'default', // default, confirm, warning, error, success, info
      closable: true,
      maskClosable: true,
      keyboard: true,
      centered: false,
      fullscreen: false,
      animation: 'fade',
      animationDuration: 300,
      zIndex: 1000,
      title: null,
      footer: null,
      children: null,
      onOpen: null,
      onClose: null,
      onConfirm: null,
      onCancel: null,
      confirmText: 'OK',
      cancelText: 'Cancel',
      showConfirmButton: true,
      showCancelButton: true,
      confirmButtonProps: {},
      cancelButtonProps: {}
    };
  }

  componentDidMount() {
    // Set up keyboard event listeners
    if (this.props.keyboard) {
      document.addEventListener('keydown', this._handleKeyDown.bind(this));
    }

    // Set up escape key handler
    this._setupEscapeHandler();
  }

  componentWillUnmount() {
    // Clean up event listeners
    document.removeEventListener('keydown', this._handleKeyDown.bind(this));
    this._cleanupEscapeHandler();
  }

  componentWillUpdate(nextProps, nextState) {
    // Handle open/close state changes
    if (nextProps.isOpen !== this.props.isOpen) {
      if (nextProps.isOpen) {
        this._openModal();
      } else {
        this._closeModal();
      }
    }

    // Update z-index
    if (nextProps.zIndex !== this.props.zIndex) {
      this.setState({ zIndex: nextProps.zIndex });
    }
  }

  _setupEscapeHandler() {
    // Create a global escape handler
    if (!document._pydanceModalEscapeHandler) {
      document._pydanceModalEscapeHandler = (event) => {
        if (event.key === 'Escape') {
          // Find the topmost open modal and close it
          const openModals = document.querySelectorAll('.pydance-modal--open');
          if (openModals.length > 0) {
            const topModal = openModals[openModals.length - 1];
            const modalInstance = topModal._pydanceModalInstance;
            if (modalInstance && modalInstance.props.closable) {
              modalInstance._handleClose();
            }
          }
        }
      };
      document.addEventListener('keydown', document._pydanceModalEscapeHandler);
    }
  }

  _cleanupEscapeHandler() {
    // Only remove if no other modals are using it
    const openModals = document.querySelectorAll('.pydance-modal--open');
    if (openModals.length === 0 && document._pydanceModalEscapeHandler) {
      document.removeEventListener('keydown', document._pydanceModalEscapeHandler);
      delete document._pydanceModalEscapeHandler;
    }
  }

  _handleKeyDown(event) {
    if (!this.state.isOpen) return;

    // Handle Tab key for focus management
    if (event.key === 'Tab') {
      this._handleTabKey(event);
    }
  }

  _handleTabKey(event) {
    if (!this._modalRef) return;

    const focusableElements = this._modalRef.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    if (event.shiftKey) {
      // Shift + Tab
      if (document.activeElement === firstElement) {
        event.preventDefault();
        lastElement.focus();
      }
    } else {
      // Tab
      if (document.activeElement === lastElement) {
        event.preventDefault();
        firstElement.focus();
      }
    }
  }

  async _openModal() {
    // Store previously focused element
    this._previouslyFocusedElement = document.activeElement;

    // Update state
    this.setState({
      isOpen: true,
      isAnimating: true,
      animationType: this.props.animation
    });

    // Add modal to DOM
    document.body.appendChild(this.element);

    // Trigger animation
    setTimeout(() => {
      this.setState({ isAnimating: false });
    }, 10);

    // Focus management
    setTimeout(() => {
      if (this._modalRef) {
        const focusableElement = this._modalRef.querySelector(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (focusableElement) {
          focusableElement.focus();
        } else {
          this._modalRef.focus();
        }
      }
    }, this.props.animationDuration);

    // Prevent body scroll
    document.body.style.overflow = 'hidden';

    // Call onOpen callback
    if (this.props.onOpen) {
      this.props.onOpen();
    }
  }

  async _closeModal() {
    this.setState({ isAnimating: true });

    // Wait for animation to complete
    setTimeout(() => {
      this.setState({ isOpen: false, isAnimating: false });

      // Restore body scroll
      document.body.style.overflow = '';

      // Restore focus
      if (this._previouslyFocusedElement) {
        this._previouslyFocusedElement.focus();
      }

      // Remove from DOM
      if (this.element && this.element.parentNode) {
        this.element.parentNode.removeChild(this.element);
      }

      // Call onClose callback
      if (this.props.onClose) {
        this.props.onClose();
      }
    }, this.props.animationDuration);
  }

  _handleClose() {
    if (this.props.closable) {
      this._closeModal();
    }
  }

  _handleMaskClick(event) {
    if (event.target === this._overlayRef && this.props.maskClosable) {
      this._handleClose();
    }
  }

  _handleConfirm() {
    if (this.props.onConfirm) {
      this.props.onConfirm();
    }
    this._handleClose();
  }

  _handleCancel() {
    if (this.props.onCancel) {
      this.props.onCancel();
    }
    this._handleClose();
  }

  render() {
    if (!this.state.isOpen && !this.state.isAnimating) {
      return null;
    }

    const {
      size = 'md',
      variant = 'default',
      closable = true,
      centered = false,
      fullscreen = false,
      title,
      footer,
      children,
      confirmText = 'OK',
      cancelText = 'Cancel',
      showConfirmButton = true,
      showCancelButton = true,
      confirmButtonProps = {},
      cancelButtonProps = {},
      className = '',
      ...otherProps
    } = this.props;

    const { isOpen, isAnimating, animationType, zIndex } = this.state;

    const modalClasses = [
      'pydance-modal',
      `pydance-modal--${size}`,
      `pydance-modal--${variant}`,
      `pydance-modal--animation-${animationType}`,
      {
        'pydance-modal--open': isOpen,
        'pydance-modal--animating': isAnimating,
        'pydance-modal--centered': centered,
        'pydance-modal--fullscreen': fullscreen
      },
      className
    ].filter(Boolean).join(' ');

    const overlayClasses = [
      'pydance-modal-overlay',
      {
        'pydance-modal-overlay--open': isOpen,
        'pydance-modal-overlay--animating': isAnimating
      }
    ].filter(Boolean).join(' ');

    // Default footer buttons
    const defaultFooter = this.createElement('div', { className: 'pydance-modal__footer-buttons' },
      showCancelButton && this.createElement('button', {
        type: 'button',
        className: 'pydance-modal__cancel-button',
        onClick: this._handleCancel.bind(this),
        ...cancelButtonProps
      }, cancelText),

      showConfirmButton && this.createElement('button', {
        type: 'button',
        className: 'pydance-modal__confirm-button pydance-modal__confirm-button--primary',
        onClick: this._handleConfirm.bind(this),
        ...confirmButtonProps
      }, confirmText)
    );

    return this.createElement('div', {
      className: overlayClasses,
      style: { zIndex },
      ref: (el) => this._overlayRef = el,
      onClick: this._handleMaskClick.bind(this),
      'aria-hidden': !isOpen,
      ...otherProps
    },
      this.createElement('div', {
        className: modalClasses,
        ref: (el) => {
          this._modalRef = el;
          if (el) el._pydanceModalInstance = this;
        },
        role: 'dialog',
        'aria-modal': true,
        'aria-labelledby': title ? 'pydance-modal-title' : undefined,
        tabIndex: -1
      },
        // Header
        (title || closable) && this.createElement('div', { className: 'pydance-modal__header' },
          title && this.createElement('h2', {
            className: 'pydance-modal__title',
            id: 'pydance-modal-title'
          }, title),

          closable && this.createElement('button', {
            type: 'button',
            className: 'pydance-modal__close',
            onClick: this._handleClose.bind(this),
            'aria-label': 'Close modal'
          }, '×')
        ),

        // Body
        this.createElement('div', { className: 'pydance-modal__body' }, children),

        // Footer
        (footer || showConfirmButton || showCancelButton) && this.createElement('div', {
          className: 'pydance-modal__footer'
        }, footer || defaultFooter)
      )
    );
  }

  // Public methods
  open() {
    this._openModal();
  }

  close() {
    this._closeModal();
  }

  toggle() {
    if (this.state.isOpen) {
      this._closeModal();
    } else {
      this._openModal();
    }
  }

  isOpen() {
    return this.state.isOpen;
  }
}

// Confirm Modal - Specialized modal for confirmations
export class ConfirmModal extends Component {
  constructor(props = {}) {
    super(props);

    this.state = {
      resolve: null,
      reject: null
    };
  }

  static getDefaultProps() {
    return {
      title: 'Confirm',
      message: 'Are you sure?',
      confirmText: 'Yes',
      cancelText: 'No',
      type: 'default', // default, warning, danger
      children: null
    };
  }

  show() {
    return new Promise((resolve, reject) => {
      this.setState({ resolve, reject });
      this.modal.open();
    });
  }

  _handleConfirm() {
    if (this.state.resolve) {
      this.state.resolve(true);
    }
    this.modal.close();
  }

  _handleCancel() {
    if (this.state.reject) {
      this.state.reject(false);
    }
    this.modal.close();
  }

  render() {
    const {
      title = 'Confirm',
      message = 'Are you sure?',
      confirmText = 'Yes',
      cancelText = 'No',
      type = 'default',
      className = '',
      ...otherProps
    } = this.props;

    return this.createElement(Modal, {
      ref: (el) => this.modal = el,
      title,
      size: 'sm',
      variant: type,
      closable: true,
      maskClosable: false,
      showConfirmButton: true,
      showCancelButton: true,
      confirmText,
      cancelText,
      onConfirm: this._handleConfirm.bind(this),
      onCancel: this._handleCancel.bind(this),
      className: `pydance-confirm-modal ${className}`,
      ...otherProps
    },
      this.createElement('p', { className: 'pydance-confirm-modal__message' }, message)
    );
  }
}

// Alert Modal - Specialized modal for alerts
export class AlertModal extends Component {
  constructor(props = {}) {
    super(props);

    this.state = {
      resolve: null
    };
  }

  static getDefaultProps() {
    return {
      title: 'Alert',
      message: 'Something happened!',
      confirmText: 'OK',
      type: 'info', // info, success, warning, error
      children: null
    };
  }

  show() {
    return new Promise((resolve) => {
      this.setState({ resolve });
      this.modal.open();
    });
  }

  _handleConfirm() {
    if (this.state.resolve) {
      this.state.resolve(true);
    }
    this.modal.close();
  }

  render() {
    const {
      title = 'Alert',
      message = 'Something happened!',
      confirmText = 'OK',
      type = 'info',
      className = '',
      ...otherProps
    } = this.props;

    return this.createElement(Modal, {
      ref: (el) => this.modal = el,
      title,
      size: 'sm',
      variant: type,
      closable: true,
      maskClosable: false,
      showConfirmButton: true,
      showCancelButton: false,
      confirmText,
      onConfirm: this._handleConfirm.bind(this),
      className: `pydance-alert-modal ${className}`,
      ...otherProps
    },
      this.createElement('p', { className: 'pydance-alert-modal__message' }, message)
    );
  }
}

// CSS Styles
const styles = `
// Modal overlay
.pydance-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.3s ease, visibility 0.3s ease;
  z-index: 1000;
}

.pydance-modal-overlay--open {
  opacity: 1;
  visibility: visible;
}

.pydance-modal-overlay--animating {
  transition: none;
}

// Modal container
.pydance-modal {
  background: var(--pydance-surface);
  border-radius: var(--pydance-radius-lg);
  box-shadow: var(--pydance-shadow-xl);
  max-height: 90vh;
  max-width: 90vw;
  display: flex;
  flex-direction: column;
  transform: scale(0.7);
  opacity: 0;
  transition: transform 0.3s ease, opacity 0.3s ease;
  outline: none;
}

// Modal animations
.pydance-modal--animation-fade {
  transform: scale(0.7);
  opacity: 0;
}

.pydance-modal--animation-fade.pydance-modal--open {
  transform: scale(1);
  opacity: 1;
}

.pydance-modal--animation-slide-up {
  transform: translateY(100px) scale(0.7);
  opacity: 0;
}

.pydance-modal--animation-slide-up.pydance-modal--open {
  transform: translateY(0) scale(1);
  opacity: 1;
}

.pydance-modal--animation-slide-down {
  transform: translateY(-100px) scale(0.7);
  opacity: 0;
}

.pydance-modal--animation-slide-down.pydance-modal--open {
  transform: translateY(0) scale(1);
  opacity: 1;
}

.pydance-modal--animation-slide-left {
  transform: translateX(100px) scale(0.7);
  opacity: 0;
}

.pydance-modal--animation-slide-left.pydance-modal--open {
  transform: translateX(0) scale(1);
  opacity: 1;
}

.pydance-modal--animation-slide-right {
  transform: translateX(-100px) scale(0.7);
  opacity: 0;
}

.pydance-modal--animation-slide-right.pydance-modal--open {
  transform: translateX(0) scale(1);
  opacity: 1;
}

.pydance-modal--animation-scale {
  transform: scale(0.3);
  opacity: 0;
}

.pydance-modal--animation-scale.pydance-modal--open {
  transform: scale(1);
  opacity: 1;
}

.pydance-modal--animation-zoom {
  transform: scale(0.1);
  opacity: 0;
}

.pydance-modal--animation-zoom.pydance-modal--open {
  transform: scale(1);
  opacity: 1;
}

.pydance-modal--open {
  transform: scale(1);
  opacity: 1;
}

.pydance-modal--animating {
  transition: none;
}

// Modal sizes
.pydance-modal--xs {
  width: 300px;
  max-width: 90vw;
}

.pydance-modal--sm {
  width: 400px;
  max-width: 90vw;
}

.pydance-modal--md {
  width: 500px;
  max-width: 90vw;
}

.pydance-modal--lg {
  width: 700px;
  max-width: 90vw;
}

.pydance-modal--xl {
  width: 900px;
  max-width: 90vw;
}

.pydance-modal--full {
  width: 100vw;
  height: 100vh;
  max-width: none;
  max-height: none;
  border-radius: 0;
}

// Modal variants
.pydance-modal--default .pydance-modal__header {
  border-bottom: 1px solid var(--pydance-border);
}

.pydance-modal--confirm .pydance-modal__confirm-button--primary {
  background: var(--pydance-primary);
  color: white;
}

.pydance-modal--warning .pydance-modal__header {
  background: var(--pydance-warning-light);
  border-bottom-color: var(--pydance-warning);
}

.pydance-modal--error .pydance-modal__header {
  background: var(--pydance-error-light);
  border-bottom-color: var(--pydance-error);
}

.pydance-modal--success .pydance-modal__header {
  background: var(--pydance-success-light);
  border-bottom-color: var(--pydance-success);
}

.pydance-modal--info .pydance-modal__header {
  background: var(--pydance-info-light);
  border-bottom-color: var(--pydance-info);
}

// Modal centering
.pydance-modal--centered {
  margin: auto;
}

// Modal fullscreen
.pydance-modal--fullscreen {
  width: 100vw;
  height: 100vh;
  max-width: none;
  max-height: none;
  border-radius: 0;
}

// Modal header
.pydance-modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--pydance-border-light);
}

.pydance-modal__title {
  margin: 0;
  font-size: var(--pydance-font-size-lg);
  font-weight: var(--pydance-font-weight-semibold);
  color: var(--pydance-text-primary);
}

.pydance-modal__close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: var(--pydance-radius-sm);
  color: var(--pydance-text-secondary);
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
}

.pydance-modal__close:hover {
  background: var(--pydance-background-secondary);
  color: var(--pydance-text-primary);
}

// Modal body
.pydance-modal__body {
  padding: 1.5rem;
  flex: 1;
  overflow-y: auto;
  color: var(--pydance-text-primary);
}

// Modal footer
.pydance-modal__footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--pydance-border-light);
}

.pydance-modal__footer-buttons {
  display: flex;
  gap: 0.75rem;
}

.pydance-modal__confirm-button,
.pydance-modal__cancel-button {
  padding: 0.5rem 1rem;
  border: 1px solid var(--pydance-border);
  border-radius: var(--pydance-radius-md);
  background: var(--pydance-background);
  color: var(--pydance-text-primary);
  font-size: var(--pydance-font-size-sm);
  cursor: pointer;
  transition: all 0.2s ease;
}

.pydance-modal__confirm-button:hover,
.pydance-modal__cancel-button:hover {
  background: var(--pydance-background-secondary);
}

.pydance-modal__confirm-button--primary {
  background: var(--pydance-primary);
  color: white;
  border-color: var(--pydance-primary);
}

.pydance-modal__confirm-button--primary:hover {
  background: var(--pydance-primary-hover);
  border-color: var(--pydance-primary-hover);
}

// Confirm and Alert modal styles
.pydance-confirm-modal__message,
.pydance-alert-modal__message {
  margin: 0;
  font-size: var(--pydance-font-size-base);
  line-height: 1.5;
}

// Focus management
.pydance-modal:focus {
  outline: 2px solid var(--pydance-focus);
  outline-offset: 2px;
}

// Responsive adjustments
@media (max-width: 768px) {
  .pydance-modal {
    width: 95vw;
    max-width: none;
    margin: 1rem;
  }

  .pydance-modal--xs,
  .pydance-modal--sm,
  .pydance-modal--md,
  .pydance-modal--lg,
  .pydance-modal--xl {
    width: 95vw;
  }

  .pydance-modal__header,
  .pydance-modal__body,
  .pydance-modal__footer {
    padding: 1rem;
  }

  .pydance-modal__footer {
    flex-direction: column-reverse;
    gap: 0.5rem;
  }

  .pydance-modal__footer-buttons {
    width: 100%;
    flex-direction: column;
  }

  .pydance-modal__confirm-button,
  .pydance-modal__cancel-button {
    width: 100%;
    padding: 0.75rem;
  }
}

// Animation keyframes (for more complex animations)
@keyframes pydance-modal-fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes pydance-modal-fade-out {
  from {
    opacity: 1;
  }
  to {
    opacity: 0;
  }
}

@keyframes pydance-modal-scale-in {
  from {
    transform: scale(0.7);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes pydance-modal-scale-out {
  from {
    transform: scale(1);
    opacity: 1;
  }
  to {
    transform: scale(0.7);
    opacity: 0;
  }
}
`;

// Inject styles
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = styles;
  document.head.appendChild(style);
}
