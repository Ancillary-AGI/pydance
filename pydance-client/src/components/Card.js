/**
 * Card - Reusable Card Component
 * Provides flexible card layouts with headers, bodies, footers, and various styling options
 */

import { Component } from '~/core/Component.js';

export class Card extends Component {
  constructor(props = {}) {
    super(props);

    this.state = {
      expanded: props.expanded || false,
      collapsed: props.collapsed || false,
      loading: props.loading || false
    };
  }

  static getDefaultProps() {
    return {
      title: null,
      subtitle: null,
      header: null,
      footer: null,
      children: null,
      variant: 'default', // default, primary, secondary, success, warning, error, info
      size: 'md', // xs, sm, md, lg, xl
      shadow: 'sm', // none, xs, sm, md, lg, xl
      border: true,
      rounded: true,
      hover: false,
      expandable: false,
      collapsible: false,
      expanded: false,
      collapsed: false,
      loading: false,
      actions: [],
      cover: null,
      className: ''
    };
  }

  componentWillUpdate(nextProps, nextState) {
    // Update loading state
    if (nextProps.loading !== this.props.loading) {
      this.setState({ loading: nextProps.loading });
    }

    // Update expanded state
    if (nextProps.expanded !== this.props.expanded) {
      this.setState({ expanded: nextProps.expanded });
    }

    // Update collapsed state
    if (nextProps.collapsed !== this.props.collapsed) {
      this.setState({ collapsed: nextProps.collapsed });
    }
  }

  _handleToggle() {
    if (this.props.expandable) {
      this.setState({ expanded: !this.state.expanded });
    } else if (this.props.collapsible) {
      this.setState({ collapsed: !this.state.collapsed });
    }
  }

  _handleAction(action) {
    if (action.handler) {
      action.handler(action);
    }
  }

  render() {
    const {
      title,
      subtitle,
      header,
      footer,
      children,
      variant = 'default',
      size = 'md',
      shadow = 'sm',
      border = true,
      rounded = true,
      hover = false,
      expandable = false,
      collapsible = false,
      actions = [],
      cover,
      className = '',
      ...otherProps
    } = this.props;

    const { expanded, collapsed, loading } = this.state;

    const cardClasses = [
      'pydance-card',
      `pydance-card--${variant}`,
      `pydance-card--${size}`,
      `pydance-card--shadow-${shadow}`,
      {
        'pydance-card--bordered': border,
        'pydance-card--rounded': rounded,
        'pydance-card--hover': hover,
        'pydance-card--expandable': expandable,
        'pydance-card--collapsible': collapsible,
        'pydance-card--expanded': expanded,
        'pydance-card--collapsed': collapsed,
        'pydance-card--loading': loading
      },
      className
    ].filter(Boolean).join(' ');

    const showHeader = title || subtitle || header || expandable || collapsible || actions.length > 0;
    const showFooter = footer;
    const showBody = children || (!collapsed && !expandable) || (expandable && expanded);

    return this.createElement('div', {
      className: cardClasses,
      ...otherProps
    },
      // Cover image
      cover && this.createElement('div', { className: 'pydance-card__cover' },
        typeof cover === 'string' ?
          this.createElement('img', { src: cover, alt: title || 'Card cover' }) :
          cover
      ),

      // Header
      showHeader && this.createElement('div', { className: 'pydance-card__header' },
        // Header content
        (title || subtitle || header) && this.createElement('div', { className: 'pydance-card__header-content' },
          title && this.createElement('h3', { className: 'pydance-card__title' }, title),
          subtitle && this.createElement('p', { className: 'pydance-card__subtitle' }, subtitle),
          header
        ),

        // Header actions
        (expandable || collapsible || actions.length > 0) && this.createElement('div', { className: 'pydance-card__header-actions' },
          // Expand/collapse toggle
          (expandable || collapsible) && this.createElement('button', {
            type: 'button',
            className: `pydance-card__toggle ${expanded || !collapsed ? 'pydance-card__toggle--expanded' : ''}`,
            onClick: this._handleToggle.bind(this),
            'aria-expanded': expanded || !collapsed,
            'aria-label': expandable ? (expanded ? 'Collapse' : 'Expand') : (collapsed ? 'Expand' : 'Collapse')
          }, expandable ? (expanded ? '▼' : '▶') : (collapsed ? '+' : '−')),

          // Custom actions
          actions.map((action, index) =>
            this.createElement('button', {
              key: index,
              type: 'button',
              className: `pydance-card__action pydance-card__action--${action.type || 'default'}`,
              onClick: () => this._handleAction(action),
              title: action.label,
              'aria-label': action.label
            }, action.icon || action.label)
          )
        )
      ),

      // Body
      showBody && this.createElement('div', { className: 'pydance-card__body' },
        loading ? this.renderLoading() : children
      ),

      // Footer
      showFooter && this.createElement('div', { className: 'pydance-card__footer' }, footer)
    );
  }

  renderLoading() {
    return this.createElement('div', { className: 'pydance-card__loading' },
      this.createElement('div', { className: 'pydance-card__loading-spinner' }),
      this.createElement('span', { className: 'pydance-card__loading-text' }, 'Loading...')
    );
  }

  // Public methods
  expand() {
    this.setState({ expanded: true, collapsed: false });
  }

  collapse() {
    this.setState({ expanded: false, collapsed: true });
  }

  toggle() {
    this._handleToggle();
  }

  setLoading(loading) {
    this.setState({ loading });
  }

  isExpanded() {
    return this.state.expanded;
  }

  isCollapsed() {
    return this.state.collapsed;
  }
}

// Card Grid component for displaying multiple cards
export class CardGrid extends Component {
  constructor(props = {}) {
    super(props);

    this.state = {
      columns: props.columns || this._calculateColumns()
    };
  }

  static getDefaultProps() {
    return {
      children: [],
      columns: null, // auto, 1, 2, 3, 4, 5, 6
      gap: 'md', // xs, sm, md, lg, xl
      responsive: true,
      className: ''
    };
  }

  componentDidMount() {
    if (this.props.responsive) {
      window.addEventListener('resize', this._handleResize.bind(this));
    }
  }

  componentWillUnmount() {
    if (this.props.responsive) {
      window.removeEventListener('resize', this._handleResize.bind(this));
    }
  }

  _calculateColumns() {
    if (typeof window === 'undefined') return 3;

    const width = window.innerWidth;
    if (width < 576) return 1;
    if (width < 768) return 2;
    if (width < 992) return 3;
    if (width < 1200) return 4;
    return 5;
  }

  _handleResize() {
    if (this.props.columns === null) {
      this.setState({ columns: this._calculateColumns() });
    }
  }

  render() {
    const {
      children,
      columns,
      gap = 'md',
      responsive = true,
      className = '',
      ...otherProps
    } = this.props;

    const gridColumns = columns || this.state.columns;

    const gridClasses = [
      'pydance-card-grid',
      `pydance-card-grid--columns-${gridColumns}`,
      `pydance-card-grid--gap-${gap}`,
      {
        'pydance-card-grid--responsive': responsive
      },
      className
    ].filter(Boolean).join(' ');

    return this.createElement('div', {
      className: gridClasses,
      ...otherProps
    }, children);
  }
}

// Card Group component for related cards
export class CardGroup extends Component {
  constructor(props = {}) {
    super(props);
  }

  static getDefaultProps() {
    return {
      children: [],
      variant: 'default', // default, connected, stacked
      className: ''
    };
  }

  render() {
    const {
      children,
      variant = 'default',
      className = '',
      ...otherProps
    } = this.props;

    const groupClasses = [
      'pydance-card-group',
      `pydance-card-group--${variant}`,
      className
    ].filter(Boolean).join(' ');

    return this.createElement('div', {
      className: groupClasses,
      ...otherProps
    }, children);
  }
}

// CSS Styles
const styles = `
// Card
.pydance-card {
  display: flex;
  flex-direction: column;
  background: var(--pydance-surface);
  color: var(--pydance-text-primary);
  overflow: hidden;
  transition: all 0.3s ease;
}

.pydance-card--bordered {
  border: 1px solid var(--pydance-border);
}

.pydance-card--rounded {
  border-radius: var(--pydance-radius-lg);
}

.pydance-card--hover:hover {
  transform: translateY(-2px);
  box-shadow: var(--pydance-shadow-lg);
}

.pydance-card--shadow-none {
  box-shadow: none;
}

.pydance-card--shadow-xs {
  box-shadow: var(--pydance-shadow-xs);
}

.pydance-card--shadow-sm {
  box-shadow: var(--pydance-shadow-sm);
}

.pydance-card--shadow-md {
  box-shadow: var(--pydance-shadow-md);
}

.pydance-card--shadow-lg {
  box-shadow: var(--pydance-shadow-lg);
}

.pydance-card--shadow-xl {
  box-shadow: var(--pydance-shadow-xl);
}

// Card variants
.pydance-card--default {
  /* Default styling */
}

.pydance-card--primary {
  border-color: var(--pydance-primary);
}

.pydance-card--primary .pydance-card__header {
  background: var(--pydance-primary-light);
  border-bottom-color: var(--pydance-primary);
}

.pydance-card--secondary {
  border-color: var(--pydance-secondary);
}

.pydance-card--secondary .pydance-card__header {
  background: var(--pydance-secondary-light);
  border-bottom-color: var(--pydance-secondary);
}

.pydance-card--success {
  border-color: var(--pydance-success);
}

.pydance-card--success .pydance-card__header {
  background: var(--pydance-success-light);
  border-bottom-color: var(--pydance-success);
}

.pydance-card--warning {
  border-color: var(--pydance-warning);
}

.pydance-card--warning .pydance-card__header {
  background: var(--pydance-warning-light);
  border-bottom-color: var(--pydance-warning);
}

.pydance-card--error {
  border-color: var(--pydance-error);
}

.pydance-card--error .pydance-card__header {
  background: var(--pydance-error-light);
  border-bottom-color: var(--pydance-error);
}

.pydance-card--info {
  border-color: var(--pydance-info);
}

.pydance-card--info .pydance-card__header {
  background: var(--pydance-info-light);
  border-bottom-color: var(--pydance-info);
}

// Card sizes
.pydance-card--xs {
  font-size: var(--pydance-font-size-xs);
}

.pydance-card--sm {
  font-size: var(--pydance-font-size-sm);
}

.pydance-card--md {
  font-size: var(--pydance-font-size-base);
}

.pydance-card--lg {
  font-size: var(--pydance-font-size-lg);
}

.pydance-card--xl {
  font-size: var(--pydance-font-size-xl);
}

// Card cover
.pydance-card__cover {
  position: relative;
  overflow: hidden;
}

.pydance-card__cover img {
  width: 100%;
  height: auto;
  display: block;
  transition: transform 0.3s ease;
}

.pydance-card--hover .pydance-card__cover img:hover {
  transform: scale(1.05);
}

// Card header
.pydance-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--pydance-border-light);
  background: var(--pydance-background-secondary);
}

.pydance-card__header-content {
  flex: 1;
}

.pydance-card__title {
  margin: 0 0 0.25rem 0;
  font-size: 1.25rem;
  font-weight: var(--pydance-font-weight-semibold);
  color: var(--pydance-text-primary);
}

.pydance-card__subtitle {
  margin: 0;
  font-size: var(--pydance-font-size-sm);
  color: var(--pydance-text-secondary);
}

.pydance-card__header-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-left: 1rem;
}

// Card toggle
.pydance-card__toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  background: none;
  border: none;
  cursor: pointer;
  border-radius: var(--pydance-radius-sm);
  color: var(--pydance-text-secondary);
  font-size: 0.875rem;
  transition: all 0.2s ease;
}

.pydance-card__toggle:hover {
  background: var(--pydance-background-tertiary);
  color: var(--pydance-text-primary);
}

.pydance-card__toggle--expanded {
  transform: rotate(180deg);
}

// Card actions
.pydance-card__action {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem;
  background: none;
  border: none;
  cursor: pointer;
  border-radius: var(--pydance-radius-sm);
  color: var(--pydance-text-secondary);
  font-size: 0.875rem;
  transition: all 0.2s ease;
}

.pydance-card__action:hover {
  background: var(--pydance-background-tertiary);
  color: var(--pydance-text-primary);
}

.pydance-card__action--primary {
  color: var(--pydance-primary);
}

.pydance-card__action--primary:hover {
  background: var(--pydance-primary-light);
}

.pydance-card__action--danger {
  color: var(--pydance-error);
}

.pydance-card__action--danger:hover {
  background: var(--pydance-error-light);
}

// Card body
.pydance-card__body {
  flex: 1;
  padding: 1.5rem;
  position: relative;
}

// Card footer
.pydance-card__footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--pydance-border-light);
  background: var(--pydance-background-secondary);
}

// Card loading
.pydance-card__loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  gap: 1rem;
}

.pydance-card__loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--pydance-border);
  border-top: 3px solid var(--pydance-primary);
  border-radius: 50%;
  animation: pydance-card-spin 1s linear infinite;
}

.pydance-card__loading-text {
  font-size: var(--pydance-font-size-sm);
  color: var(--pydance-text-secondary);
}

// Card grid
.pydance-card-grid {
  display: grid;
  gap: 1rem;
}

.pydance-card-grid--columns-1 {
  grid-template-columns: 1fr;
}

.pydance-card-grid--columns-2 {
  grid-template-columns: repeat(2, 1fr);
}

.pydance-card-grid--columns-3 {
  grid-template-columns: repeat(3, 1fr);
}

.pydance-card-grid--columns-4 {
  grid-template-columns: repeat(4, 1fr);
}

.pydance-card-grid--columns-5 {
  grid-template-columns: repeat(5, 1fr);
}

.pydance-card-grid--columns-6 {
  grid-template-columns: repeat(6, 1fr);
}

.pydance-card-grid--gap-xs {
  gap: 0.5rem;
}

.pydance-card-grid--gap-sm {
  gap: 0.75rem;
}

.pydance-card-grid--gap-md {
  gap: 1rem;
}

.pydance-card-grid--gap-lg {
  gap: 1.5rem;
}

.pydance-card-grid--gap-xl {
  gap: 2rem;
}

// Card group
.pydance-card-group {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.pydance-card-group--connected .pydance-card {
  border-radius: 0;
  border-left: none;
  border-right: none;
}

.pydance-card-group--connected .pydance-card:first-child {
  border-top-left-radius: var(--pydance-radius-lg);
  border-top-right-radius: var(--pydance-radius-lg);
  border-top: 1px solid var(--pydance-border);
}

.pydance-card-group--connected .pydance-card:last-child {
  border-bottom-left-radius: var(--pydance-radius-lg);
  border-bottom-right-radius: var(--pydance-radius-lg);
  border-bottom: 1px solid var(--pydance-border);
}

.pydance-card-group--connected .pydance-card:not(:first-child) {
  border-top: 1px solid var(--pydance-border-light);
}

.pydance-card-group--stacked {
  position: relative;
}

.pydance-card-group--stacked .pydance-card {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  z-index: 1;
}

.pydance-card-group--stacked .pydance-card:nth-child(2) {
  z-index: 2;
  transform: translateX(4px) translateY(4px);
}

.pydance-card-group--stacked .pydance-card:nth-child(3) {
  z-index: 3;
  transform: translateX(8px) translateY(8px);
}

.pydance-card-group--stacked .pydance-card:nth-child(4) {
  z-index: 4;
  transform: translateX(12px) translateY(12px);
}

// Animations
@keyframes pydance-card-spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

// Responsive
@media (max-width: 768px) {
  .pydance-card-grid {
    grid-template-columns: 1fr;
  }

  .pydance-card-grid--responsive {
    grid-template-columns: 1fr;
  }

  .pydance-card__header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .pydance-card__header-actions {
    margin-left: 0;
    align-self: flex-end;
  }

  .pydance-card__body,
  .pydance-card__footer {
    padding: 1rem;
  }

  .pydance-card-group--connected {
    flex-direction: column;
  }

  .pydance-card-group--connected .pydance-card {
    border-left: 1px solid var(--pydance-border);
    border-right: 1px solid var(--pydance-border);
  }

  .pydance-card-group--stacked .pydance-card:nth-child(2) {
    transform: translateX(2px) translateY(2px);
  }

  .pydance-card-group--stacked .pydance-card:nth-child(3) {
    transform: translateX(4px) translateY(4px);
  }

  .pydance-card-group--stacked .pydance-card:nth-child(4) {
    transform: translateX(6px) translateY(6px);
  }
}
`;

// Inject styles
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = styles;
  document.head.appendChild(style);
}
