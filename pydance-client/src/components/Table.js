/**
 * Table - Reusable Data Table Component
 * Provides sortable, filterable, paginated tables with selection and actions
 */

import { Component } from '~/core/Component.js';

export class Table extends Component {
  constructor(props = {}) {
    super(props);

    this.state = {
      data: props.data || [],
      filteredData: props.data || [],
      sortedData: props.data || [],
      selectedRows: new Set(),
      currentPage: 1,
      pageSize: props.pageSize || 10,
      sortColumn: null,
      sortDirection: 'asc', // 'asc' or 'desc'
      filters: {},
      searchTerm: '',
      loading: props.loading || false,
      expandedRows: new Set()
    };

    this._tableRef = null;
  }

  static getDefaultProps() {
    return {
      data: [],
      columns: [],
      selectable: false,
      sortable: true,
      filterable: false,
      searchable: false,
      paginated: true,
      pageSize: 10,
      pageSizeOptions: [10, 25, 50, 100],
      loading: false,
      striped: false,
      bordered: true,
      hover: true,
      compact: false,
      expandable: false,
      actions: [],
      emptyMessage: 'No data available',
      loadingMessage: 'Loading...',
      children: null
    };
  }

  componentWillUpdate(nextProps, nextState) {
    // Update data when props change
    if (nextProps.data !== this.props.data) {
      this.setState({
        data: nextProps.data,
        filteredData: nextProps.data,
        sortedData: nextProps.data,
        currentPage: 1,
        selectedRows: new Set()
      });
    }

    // Update loading state
    if (nextProps.loading !== this.props.loading) {
      this.setState({ loading: nextProps.loading });
    }
  }

  componentDidUpdate(prevProps, prevState) {
    // Re-filter and sort when data changes
    if (prevState.data !== this.state.data) {
      this._applyFiltersAndSort();
    }
  }

  _applyFiltersAndSort() {
    let data = [...this.state.data];

    // Apply search
    if (this.state.searchTerm) {
      data = data.filter(row =>
        Object.values(row).some(value =>
          String(value).toLowerCase().includes(this.state.searchTerm.toLowerCase())
        )
      );
    }

    // Apply column filters
    Object.entries(this.state.filters).forEach(([columnKey, filterValue]) => {
      if (filterValue) {
        data = data.filter(row => {
          const value = row[columnKey];
          return String(value).toLowerCase().includes(filterValue.toLowerCase());
        });
      }
    });

    // Apply sorting
    if (this.state.sortColumn) {
      data.sort((a, b) => {
        const aVal = a[this.state.sortColumn];
        const bVal = b[this.state.sortColumn];

        let result = 0;
        if (aVal < bVal) result = -1;
        if (aVal > bVal) result = 1;

        return this.state.sortDirection === 'desc' ? -result : result;
      });
    }

    this.setState({
      filteredData: data,
      sortedData: data,
      currentPage: 1,
      selectedRows: new Set()
    });
  }

  _handleSort(columnKey) {
    const { sortColumn, sortDirection } = this.state;

    let newDirection = 'asc';
    if (sortColumn === columnKey) {
      newDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    }

    this.setState({
      sortColumn: columnKey,
      sortDirection: newDirection
    }, () => {
      this._applyFiltersAndSort();
    });
  }

  _handleSearch(event) {
    this.setState({ searchTerm: event.target.value }, () => {
      this._applyFiltersAndSort();
    });
  }

  _handleFilter(columnKey, value) {
    const filters = { ...this.state.filters };
    if (value) {
      filters[columnKey] = value;
    } else {
      delete filters[columnKey];
    }

    this.setState({ filters }, () => {
      this._applyFiltersAndSort();
    });
  }

  _handleRowSelect(rowId, selected) {
    const selectedRows = new Set(this.state.selectedRows);
    if (selected) {
      selectedRows.add(rowId);
    } else {
      selectedRows.delete(rowId);
    }

    this.setState({ selectedRows });

    if (this.props.onSelectionChange) {
      this.props.onSelectionChange(Array.from(selectedRows));
    }
  }

  _handleSelectAll(selected) {
    const selectedRows = new Set();
    if (selected) {
      this.state.sortedData.forEach((row, index) => {
        selectedRows.add(this._getRowId(row, index));
      });
    }

    this.setState({ selectedRows });

    if (this.props.onSelectionChange) {
      this.props.onSelectionChange(Array.from(selectedRows));
    }
  }

  _handleRowExpand(rowId) {
    const expandedRows = new Set(this.state.expandedRows);
    if (expandedRows.has(rowId)) {
      expandedRows.delete(rowId);
    } else {
      expandedRows.add(rowId);
    }

    this.setState({ expandedRows });
  }

  _handlePageChange(page) {
    this.setState({ currentPage: page });
  }

  _handlePageSizeChange(pageSize) {
    this.setState({ pageSize, currentPage: 1 });
  }

  _getRowId(row, index) {
    return row.id || row._id || index;
  }

  _getPaginatedData() {
    const { sortedData, currentPage, pageSize } = this.state;
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;

    return sortedData.slice(startIndex, endIndex);
  }

  _getTotalPages() {
    return Math.ceil(this.state.sortedData.length / this.state.pageSize);
  }

  render() {
    const {
      columns = [],
      selectable = false,
      sortable = true,
      filterable = false,
      searchable = false,
      paginated = true,
      pageSizeOptions = [10, 25, 50, 100],
      striped = false,
      bordered = true,
      hover = true,
      compact = false,
      expandable = false,
      actions = [],
      emptyMessage = 'No data available',
      loadingMessage = 'Loading...',
      className = '',
      ...otherProps
    } = this.props;

    const {
      sortedData,
      selectedRows,
      currentPage,
      pageSize,
      sortColumn,
      sortDirection,
      loading,
      expandedRows
    } = this.state;

    const paginatedData = paginated ? this._getPaginatedData() : sortedData;
    const totalPages = this._getTotalPages();
    const allSelected = paginatedData.length > 0 && paginatedData.every((row, index) =>
      selectedRows.has(this._getRowId(row, index))
    );
    const someSelected = paginatedData.some((row, index) =>
      selectedRows.has(this._getRowId(row, index))
    );

    const tableClasses = [
      'pydance-table',
      {
        'pydance-table--striped': striped,
        'pydance-table--bordered': bordered,
        'pydance-table--hover': hover,
        'pydance-table--compact': compact,
        'pydance-table--loading': loading
      },
      className
    ].filter(Boolean).join(' ');

    return this.createElement('div', { className: 'pydance-table-wrapper' },
      // Search and filters
      this.renderToolbar(),

      // Table
      this.createElement('div', { className: 'pydance-table-container' },
        this.createElement('table', {
          ref: (el) => this._tableRef = el,
          className: tableClasses,
          ...otherProps
        },
          // Table header
          this.createElement('thead', { className: 'pydance-table__header' },
            this.createElement('tr', null,
              // Selection column
              selectable && this.createElement('th', {
                className: 'pydance-table__header-cell pydance-table__header-cell--selection'
              },
                this.createElement('input', {
                  type: 'checkbox',
                  checked: allSelected,
                  ref: (el) => el && (el.indeterminate = someSelected && !allSelected),
                  onChange: (e) => this._handleSelectAll(e.target.checked)
                })
              ),

              // Expand column
              expandable && this.createElement('th', {
                className: 'pydance-table__header-cell pydance-table__header-cell--expand'
              }),

              // Data columns
              columns.map(column => this.renderHeaderCell(column)),

              // Actions column
              actions.length > 0 && this.createElement('th', {
                className: 'pydance-table__header-cell pydance-table__header-cell--actions'
              }, 'Actions')
            )
          ),

          // Table body
          this.createElement('tbody', { className: 'pydance-table__body' },
            loading ? this.renderLoadingRow() :
            paginatedData.length === 0 ? this.renderEmptyRow() :
            paginatedData.map((row, index) => this.renderDataRow(row, index))
          )
        )
      ),

      // Pagination
      paginated && sortedData.length > pageSize && this.renderPagination(),

      // Footer info
      this.renderFooterInfo()
    );
  }

  renderToolbar() {
    const { searchable, filterable, columns } = this.props;

    if (!searchable && !filterable) return null;

    return this.createElement('div', { className: 'pydance-table__toolbar' },
      // Search
      searchable && this.createElement('div', { className: 'pydance-table__search' },
        this.createElement('input', {
          type: 'text',
          placeholder: 'Search...',
          className: 'pydance-table__search-input',
          value: this.state.searchTerm,
          onChange: this._handleSearch.bind(this)
        })
      ),

      // Filters
      filterable && this.createElement('div', { className: 'pydance-table__filters' },
        columns.filter(col => col.filterable).map(column =>
          this.createElement('input', {
            key: column.key,
            type: 'text',
            placeholder: `Filter ${column.title}`,
            className: 'pydance-table__filter-input',
            value: this.state.filters[column.key] || '',
            onChange: (e) => this._handleFilter(column.key, e.target.value)
          })
        )
      )
    );
  }

  renderHeaderCell(column) {
    const { sortable } = this.props;
    const { sortColumn, sortDirection } = this.state;

    const isSorted = sortColumn === column.key;
    const canSort = sortable && column.sortable !== false;

    return this.createElement('th', {
      key: column.key,
      className: `pydance-table__header-cell ${canSort ? 'pydance-table__header-cell--sortable' : ''} ${isSorted ? 'pydance-table__header-cell--sorted' : ''}`,
      onClick: canSort ? () => this._handleSort(column.key) : undefined
    },
      this.createElement('div', { className: 'pydance-table__header-content' },
        this.createElement('span', { className: 'pydance-table__header-title' }, column.title),
        canSort && this.createElement('span', { className: 'pydance-table__header-sort' },
          isSorted && this.createElement('span', { className: `pydance-table__sort-icon pydance-table__sort-icon--${sortDirection}` }, '▲')
        )
      )
    );
  }

  renderDataRow(row, index) {
    const {
      columns = [],
      selectable = false,
      expandable = false,
      actions = []
    } = this.props;

    const { selectedRows, expandedRows } = this.state;
    const rowId = this._getRowId(row, index);
    const isSelected = selectedRows.has(rowId);
    const isExpanded = expandedRows.has(rowId);

    return [
      // Main row
      this.createElement('tr', {
        key: `row-${rowId}`,
        className: `pydance-table__row ${isSelected ? 'pydance-table__row--selected' : ''}`
      },
        // Selection column
        selectable && this.createElement('td', { className: 'pydance-table__cell pydance-table__cell--selection' },
          this.createElement('input', {
            type: 'checkbox',
            checked: isSelected,
            onChange: (e) => this._handleRowSelect(rowId, e.target.checked)
          })
        ),

        // Expand column
        expandable && this.createElement('td', { className: 'pydance-table__cell pydance-table__cell--expand' },
          this.createElement('button', {
            className: `pydance-table__expand-button ${isExpanded ? 'pydance-table__expand-button--expanded' : ''}`,
            onClick: () => this._handleRowExpand(rowId),
            'aria-expanded': isExpanded
          }, isExpanded ? '▼' : '▶')
        ),

        // Data columns
        columns.map(column => this.renderDataCell(row, column)),

        // Actions column
        actions.length > 0 && this.createElement('td', { className: 'pydance-table__cell pydance-table__cell--actions' },
          this.createElement('div', { className: 'pydance-table__actions' },
            actions.map((action, actionIndex) =>
              this.createElement('button', {
                key: actionIndex,
                className: `pydance-table__action pydance-table__action--${action.type || 'default'}`,
                onClick: () => action.handler(row, rowId),
                title: action.label
              }, action.icon || action.label)
            )
          )
        )
      ),

      // Expanded row
      isExpanded && expandable && this.createElement('tr', {
        key: `expanded-${rowId}`,
        className: 'pydance-table__row pydance-table__row--expanded'
      },
        this.createElement('td', {
          colSpan: (selectable ? 1 : 0) + (expandable ? 1 : 0) + columns.length + (actions.length > 0 ? 1 : 0),
          className: 'pydance-table__cell pydance-table__cell--expanded'
        }, this.props.renderExpandedRow ? this.props.renderExpandedRow(row, rowId) : JSON.stringify(row, null, 2))
      )
    ];
  }

  renderDataCell(row, column) {
    const value = row[column.key];
    const formattedValue = column.render ? column.render(value, row) : value;

    return this.createElement('td', {
      key: column.key,
      className: `pydance-table__cell pydance-table__cell--${column.key}`
    }, formattedValue);
  }

  renderLoadingRow() {
    const { columns = [], selectable, expandable, actions } = this.props;
    const colSpan = (selectable ? 1 : 0) + (expandable ? 1 : 0) + columns.length + (actions.length > 0 ? 1 : 0);

    return this.createElement('tr', { className: 'pydance-table__row pydance-table__row--loading' },
      this.createElement('td', { colSpan, className: 'pydance-table__cell pydance-table__cell--loading' },
        this.createElement('div', { className: 'pydance-table__loading' },
          this.createElement('div', { className: 'pydance-table__loading-spinner' }),
          this.createElement('span', { className: 'pydance-table__loading-text' }, this.props.loadingMessage)
        )
      )
    );
  }

  renderEmptyRow() {
    const { columns = [], selectable, expandable, actions } = this.props;
    const colSpan = (selectable ? 1 : 0) + (expandable ? 1 : 0) + columns.length + (actions.length > 0 ? 1 : 0);

    return this.createElement('tr', { className: 'pydance-table__row pydance-table__row--empty' },
      this.createElement('td', { colSpan, className: 'pydance-table__cell pydance-table__cell--empty' },
        this.props.emptyMessage
      )
    );
  }

  renderPagination() {
    const { pageSizeOptions = [10, 25, 50, 100] } = this.props;
    const { currentPage, pageSize, sortedData } = this.state;
    const totalPages = this._getTotalPages();
    const startItem = (currentPage - 1) * pageSize + 1;
    const endItem = Math.min(currentPage * pageSize, sortedData.length);

    return this.createElement('div', { className: 'pydance-table__pagination' },
      // Page size selector
      this.createElement('div', { className: 'pydance-table__page-size' },
        this.createElement('span', null, 'Show'),
        this.createElement('select', {
          value: pageSize,
          onChange: (e) => this._handlePageSizeChange(Number(e.target.value)),
          className: 'pydance-table__page-size-select'
        }, pageSizeOptions.map(size =>
          this.createElement('option', { key: size, value: size }, size)
        )),
        this.createElement('span', null, 'entries')
      ),

      // Page info
      this.createElement('div', { className: 'pydance-table__page-info' },
        `Showing ${startItem} to ${endItem} of ${sortedData.length} entries`
      ),

      // Page navigation
      this.createElement('div', { className: 'pydance-table__page-nav' },
        this.createElement('button', {
          className: 'pydance-table__page-button',
          disabled: currentPage === 1,
          onClick: () => this._handlePageChange(1)
        }, 'First'),

        this.createElement('button', {
          className: 'pydance-table__page-button',
          disabled: currentPage === 1,
          onClick: () => this._handlePageChange(currentPage - 1)
        }, 'Previous'),

        this.createElement('span', { className: 'pydance-table__page-current' },
          `Page ${currentPage} of ${totalPages}`
        ),

        this.createElement('button', {
          className: 'pydance-table__page-button',
          disabled: currentPage === totalPages,
          onClick: () => this._handlePageChange(currentPage + 1)
        }, 'Next'),

        this.createElement('button', {
          className: 'pydance-table__page-button',
          disabled: currentPage === totalPages,
          onClick: () => this._handlePageChange(totalPages)
        }, 'Last')
      )
    );
  }

  renderFooterInfo() {
    const { selectedRows, sortedData } = this.state;

    if (selectedRows.size === 0) return null;

    return this.createElement('div', { className: 'pydance-table__footer-info' },
      `${selectedRows.size} of ${sortedData.length} rows selected`
    );
  }

  // Public methods
  getSelectedRows() {
    return Array.from(this.state.selectedRows);
  }

  getSelectedData() {
    const selectedIds = Array.from(this.state.selectedRows);
    return this.state.data.filter((row, index) =>
      selectedIds.includes(this._getRowId(row, index))
    );
  }

  clearSelection() {
    this.setState({ selectedRows: new Set() });
  }

  refresh() {
    this._applyFiltersAndSort();
  }

  setData(data) {
    this.setState({
      data,
      filteredData: data,
      sortedData: data,
      currentPage: 1,
      selectedRows: new Set()
    });
  }
}

// CSS Styles
const styles = `
// Table wrapper
.pydance-table-wrapper {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.pydance-table-container {
  overflow-x: auto;
  border-radius: var(--pydance-radius-md);
  box-shadow: var(--pydance-shadow-sm);
}

// Table
.pydance-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--pydance-surface);
  color: var(--pydance-text-primary);
  font-size: var(--pydance-font-size-sm);
}

.pydance-table--bordered {
  border: 1px solid var(--pydance-border);
}

.pydance-table--striped tbody tr:nth-child(even) {
  background: var(--pydance-background-secondary);
}

.pydance-table--hover tbody tr:hover {
  background: var(--pydance-background-secondary);
}

.pydance-table--compact {
  font-size: var(--pydance-font-size-xs);
}

.pydance-table--compact .pydance-table__cell {
  padding: 0.25rem 0.5rem;
}

// Table header
.pydance-table__header {
  background: var(--pydance-background-secondary);
}

.pydance-table__header-cell {
  padding: 0.75rem 1rem;
  text-align: left;
  font-weight: var(--pydance-font-weight-semibold);
  border-bottom: 1px solid var(--pydance-border);
  position: relative;
}

.pydance-table__header-cell--sortable {
  cursor: pointer;
  user-select: none;
}

.pydance-table__header-cell--sortable:hover {
  background: var(--pydance-background-tertiary);
}

.pydance-table__header-cell--sorted {
  background: var(--pydance-primary-light);
}

.pydance-table__header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.pydance-table__header-sort {
  margin-left: 0.5rem;
}

.pydance-table__sort-icon {
  font-size: 0.75rem;
  color: var(--pydance-primary);
}

.pydance-table__sort-icon--desc {
  transform: rotate(180deg);
}

// Table body
.pydance-table__body {
}

.pydance-table__row {
  transition: background-color 0.2s ease;
}

.pydance-table__row--selected {
  background: var(--pydance-primary-light);
}

.pydance-table__row--expanded {
  background: var(--pydance-background-secondary);
}

.pydance-table__row--loading,
.pydance-table__row--empty {
  text-align: center;
}

.pydance-table__cell {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--pydance-border-light);
  vertical-align: top;
}

.pydance-table__cell--selection {
  width: 40px;
  text-align: center;
}

.pydance-table__cell--expand {
  width: 40px;
  text-align: center;
}

.pydance-table__cell--actions {
  width: 120px;
}

.pydance-table__cell--loading,
.pydance-table__cell--empty {
  padding: 2rem;
}

.pydance-table__cell--expanded {
  padding: 1rem;
  background: var(--pydance-background-tertiary);
}

// Table toolbar
.pydance-table__toolbar {
  display: flex;
  gap: 1rem;
  align-items: center;
  margin-bottom: 1rem;
}

.pydance-table__search {
  flex: 1;
  max-width: 300px;
}

.pydance-table__search-input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--pydance-border);
  border-radius: var(--pydance-radius-md);
  background: var(--pydance-background);
  color: var(--pydance-text-primary);
}

.pydance-table__filters {
  display: flex;
  gap: 0.5rem;
}

.pydance-table__filter-input {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--pydance-border);
  border-radius: var(--pydance-radius-md);
  background: var(--pydance-background);
  color: var(--pydance-text-primary);
  width: 150px;
}

// Table actions
.pydance-table__actions {
  display: flex;
  gap: 0.25rem;
}

.pydance-table__action {
  padding: 0.25rem 0.5rem;
  border: none;
  border-radius: var(--pydance-radius-sm);
  background: transparent;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s ease;
}

.pydance-table__action:hover {
  background: var(--pydance-background-secondary);
}

.pydance-table__action--primary {
  background: var(--pydance-primary);
  color: white;
}

.pydance-table__action--primary:hover {
  background: var(--pydance-primary-hover);
}

.pydance-table__action--danger {
  color: var(--pydance-error);
}

.pydance-table__action--danger:hover {
  background: var(--pydance-error-light);
}

// Expand button
.pydance-table__expand-button {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.75rem;
  padding: 0.25rem;
  border-radius: var(--pydance-radius-sm);
  transition: transform 0.2s ease;
}

.pydance-table__expand-button:hover {
  background: var(--pydance-background-secondary);
}

.pydance-table__expand-button--expanded {
  transform: rotate(90deg);
}

// Loading
.pydance-table__loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.pydance-table__loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--pydance-border);
  border-top: 3px solid var(--pydance-primary);
  border-radius: 50%;
  animation: pydance-table-spin 1s linear infinite;
}

.pydance-table__loading-text {
  color: var(--pydance-text-secondary);
}

// Pagination
.pydance-table__pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: var(--pydance-background-secondary);
  border-radius: 0 0 var(--pydance-radius-md) var(--pydance-radius-md);
}

.pydance-table__page-size {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: var(--pydance-font-size-sm);
}

.pydance-table__page-size-select {
  padding: 0.25rem 0.5rem;
  border: 1px solid var(--pydance-border);
  border-radius: var(--pydance-radius-sm);
  background: var(--pydance-background);
  color: var(--pydance-text-primary);
}

.pydance-table__page-info {
  font-size: var(--pydance-font-size-sm);
  color: var(--pydance-text-secondary);
}

.pydance-table__page-nav {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.pydance-table__page-button {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--pydance-border);
  border-radius: var(--pydance-radius-sm);
  background: var(--pydance-background);
  color: var(--pydance-text-primary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.pydance-table__page-button:hover:not(:disabled) {
  background: var(--pydance-background-tertiary);
}

.pydance-table__page-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pydance-table__page-current {
  font-size: var(--pydance-font-size-sm);
  color: var(--pydance-text-secondary);
  margin: 0 0.5rem;
}

// Footer info
.pydance-table__footer-info {
  padding: 0.5rem 1rem;
  background: var(--pydance-primary-light);
  color: var(--pydance-primary-dark);
  font-size: var(--pydance-font-size-sm);
  border-radius: 0 0 var(--pydance-radius-md) var(--pydance-radius-md);
}

// Animations
@keyframes pydance-table-spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

// Responsive
@media (max-width: 768px) {
  .pydance-table__toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .pydance-table__search {
    max-width: none;
  }

  .pydance-table__filters {
    flex-direction: column;
  }

  .pydance-table__filter-input {
    width: 100%;
  }

  .pydance-table__pagination {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .pydance-table__page-nav {
    justify-content: center;
  }

  .pydance-table__cell--actions {
    width: 80px;
  }

  .pydance-table__actions {
    flex-direction: column;
  }
}
`;

// Inject styles
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = styles;
  document.head.appendChild(style);
}
