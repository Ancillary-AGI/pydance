/**
 * Efficient Reconciler - React Fiber-inspired reconciliation
 * O(n) diffing with key-based reconciliation and minimal DOM operations
 */

// Reconciliation strategies
const RECONCILE_TYPE = {
  REPLACE: 'REPLACE',
  UPDATE: 'UPDATE',
  MOVE: 'MOVE',
  INSERT: 'INSERT',
  REMOVE: 'REMOVE',
  SKIP: 'SKIP'
};

export class Reconciler {
  constructor() {
    this.commitQueue = [];
    this.isCommitting = false;
  }

  /**
   * Reconcile old and new VDOM trees - O(n) complexity
   */
  reconcile(parentDom, oldVNode, newVNode, index = 0) {
    // Case 1: No old node - INSERT
    if (!oldVNode && newVNode) {
      return this.createNode(newVNode, parentDom, index);
    }

    // Case 2: No new node - REMOVE
    if (oldVNode && !newVNode) {
      return this.removeNode(parentDom, index);
    }

    // Case 3: Different types - REPLACE
    if (this.isDifferentType(oldVNode, newVNode)) {
      const newDom = this.createNode(newVNode, parentDom, index);
      this.removeNode(parentDom, index);
      return newDom;
    }

    // Case 4: Text nodes - UPDATE if different
    if (this.isTextNode(newVNode)) {
      return this.updateTextNode(parentDom, oldVNode, newVNode, index);
    }

    // Case 5: Element nodes - UPDATE props and reconcile children
    return this.updateElement(parentDom, oldVNode, newVNode, index);
  }

  /**
   * Reconcile children with key-based optimization
   */
  reconcileChildren(parentDom, oldChildren = [], newChildren = []) {
    // Build key maps for O(1) lookup
    const oldKeyMap = new Map();
    const newKeyMap = new Map();
    const oldIndexMap = new Map();

    oldChildren.forEach((child, i) => {
      if (child?.key) {
        oldKeyMap.set(child.key, child);
        oldIndexMap.set(child.key, i);
      }
    });

    newChildren.forEach((child, i) => {
      if (child?.key) {
        newKeyMap.set(child.key, i);
      }
    });

    const operations = [];
    const domNodes = Array.from(parentDom.childNodes);

    // Pass 1: Identify operations
    let oldIndex = 0;
    let newIndex = 0;

    while (newIndex < newChildren.length) {
      const newChild = newChildren[newIndex];
      const oldChild = oldChildren[oldIndex];

      if (!newChild) {
        newIndex++;
        continue;
      }

      // Key-based matching
      if (newChild.key) {
        const matchedOld = oldKeyMap.get(newChild.key);
        
        if (matchedOld) {
          const oldPos = oldIndexMap.get(newChild.key);
          
          if (oldPos !== newIndex) {
            // MOVE operation
            operations.push({
              type: RECONCILE_TYPE.MOVE,
              from: oldPos,
              to: newIndex,
              oldVNode: matchedOld,
              newVNode: newChild
            });
          } else {
            // UPDATE in place
            operations.push({
              type: RECONCILE_TYPE.UPDATE,
              index: newIndex,
              oldVNode: matchedOld,
              newVNode: newChild
            });
          }
        } else {
          // INSERT new
          operations.push({
            type: RECONCILE_TYPE.INSERT,
            index: newIndex,
            newVNode: newChild
          });
        }
      } else {
        // No key - positional matching
        if (oldChild) {
          if (this.isDifferentType(oldChild, newChild)) {
            operations.push({
              type: RECONCILE_TYPE.REPLACE,
              index: newIndex,
              oldVNode: oldChild,
              newVNode: newChild
            });
          } else {
            operations.push({
              type: RECONCILE_TYPE.UPDATE,
              index: newIndex,
              oldVNode: oldChild,
              newVNode: newChild
            });
          }
        } else {
          operations.push({
            type: RECONCILE_TYPE.INSERT,
            index: newIndex,
            newVNode: newChild
          });
        }
        oldIndex++;
      }

      newIndex++;
    }

    // Pass 2: Remove old nodes not in new
    for (let i = oldChildren.length - 1; i >= newChildren.length; i--) {
      operations.push({
        type: RECONCILE_TYPE.REMOVE,
        index: i
      });
    }

    // Pass 3: Execute operations
    this.executeOperations(parentDom, operations, domNodes);
  }

  /**
   * Execute reconciliation operations efficiently
   */
  executeOperations(parentDom, operations, domNodes) {
    const moved = new Set();

    operations.forEach(op => {
      switch (op.type) {
        case RECONCILE_TYPE.INSERT:
          const newNode = this.createDomNode(op.newVNode);
          if (op.index >= parentDom.childNodes.length) {
            parentDom.appendChild(newNode);
          } else {
            parentDom.insertBefore(newNode, parentDom.childNodes[op.index]);
          }
          break;

        case RECONCILE_TYPE.REMOVE:
          const nodeToRemove = parentDom.childNodes[op.index];
          if (nodeToRemove) {
            parentDom.removeChild(nodeToRemove);
          }
          break;

        case RECONCILE_TYPE.REPLACE:
          const replacement = this.createDomNode(op.newVNode);
          const oldNode = parentDom.childNodes[op.index];
          if (oldNode) {
            parentDom.replaceChild(replacement, oldNode);
          }
          break;

        case RECONCILE_TYPE.UPDATE:
          const domNode = parentDom.childNodes[op.index];
          if (domNode) {
            this.updateDomNode(domNode, op.oldVNode, op.newVNode);
          }
          break;

        case RECONCILE_TYPE.MOVE:
          if (!moved.has(op.from)) {
            const nodeToMove = domNodes[op.from];
            if (nodeToMove) {
              if (op.to >= parentDom.childNodes.length) {
                parentDom.appendChild(nodeToMove);
              } else {
                parentDom.insertBefore(nodeToMove, parentDom.childNodes[op.to]);
              }
              this.updateDomNode(nodeToMove, op.oldVNode, op.newVNode);
              moved.add(op.from);
            }
          }
          break;
      }
    });
  }

  /**
   * Create DOM node from VDOM
   */
  createDomNode(vnode) {
    if (!vnode) return null;

    // Text node
    if (typeof vnode === 'string' || typeof vnode === 'number') {
      return document.createTextNode(String(vnode));
    }

    // Element node
    if (vnode.$$typeof === Symbol.for('pydance.element')) {
      const el = document.createElement(vnode.tagName);
      
      // Set props
      this.setProps(el, vnode.props);
      
      // Create children
      if (vnode.children) {
        vnode.children.forEach(child => {
          const childNode = this.createDomNode(child);
          if (childNode) el.appendChild(childNode);
        });
      }
      
      return el;
    }

    // Fragment
    if (vnode.$$typeof === Symbol.for('pydance.fragment')) {
      const fragment = document.createDocumentFragment();
      if (vnode.children) {
        vnode.children.forEach(child => {
          const childNode = this.createDomNode(child);
          if (childNode) fragment.appendChild(childNode);
        });
      }
      return fragment;
    }

    return null;
  }

  /**
   * Update DOM node props efficiently
   */
  updateDomNode(domNode, oldVNode, newVNode) {
    if (!domNode || !newVNode) return;

    // Update props
    const oldProps = oldVNode?.props || {};
    const newProps = newVNode?.props || {};

    // Remove old props
    for (const key in oldProps) {
      if (!(key in newProps) && key !== 'children' && key !== 'key') {
        this.removeProp(domNode, key, oldProps[key]);
      }
    }

    // Set new props
    for (const key in newProps) {
      if (key !== 'children' && key !== 'key' && oldProps[key] !== newProps[key]) {
        this.setProp(domNode, key, newProps[key], oldProps[key]);
      }
    }

    // Reconcile children
    if (newVNode.children && domNode.nodeType === 1) {
      this.reconcileChildren(domNode, oldVNode?.children || [], newVNode.children);
    }
  }

  /**
   * Set single prop efficiently
   */
  setProp(el, key, value, oldValue) {
    if (key === 'className') {
      el.className = value;
    } else if (key === 'style' && typeof value === 'object') {
      Object.assign(el.style, value);
    } else if (key.startsWith('on')) {
      const event = key.slice(2).toLowerCase();
      if (oldValue) el.removeEventListener(event, oldValue);
      el.addEventListener(event, value);
    } else if (key === 'ref') {
      if (typeof value === 'function') value(el);
      else if (value) value.current = el;
    } else if (typeof value === 'boolean') {
      if (value) el.setAttribute(key, '');
      else el.removeAttribute(key);
    } else {
      el.setAttribute(key, value);
    }
  }

  /**
   * Remove prop efficiently
   */
  removeProp(el, key, value) {
    if (key === 'className') {
      el.className = '';
    } else if (key === 'style') {
      el.style.cssText = '';
    } else if (key.startsWith('on')) {
      const event = key.slice(2).toLowerCase();
      el.removeEventListener(event, value);
    } else {
      el.removeAttribute(key);
    }
  }

  /**
   * Set all props
   */
  setProps(el, props) {
    for (const key in props) {
      if (key !== 'children' && key !== 'key') {
        this.setProp(el, key, props[key]);
      }
    }
  }

  // Helper methods
  isDifferentType(a, b) {
    if (!a || !b) return true;
    if (typeof a !== typeof b) return true;
    if (a.$$typeof !== b.$$typeof) return true;
    if (a.tagName !== b.tagName) return true;
    return false;
  }

  isTextNode(vnode) {
    return typeof vnode === 'string' || typeof vnode === 'number';
  }

  createNode(vnode, parent, index) {
    const node = this.createDomNode(vnode);
    if (node && parent) {
      if (index >= parent.childNodes.length) {
        parent.appendChild(node);
      } else {
        parent.insertBefore(node, parent.childNodes[index]);
      }
    }
    return node;
  }

  removeNode(parent, index) {
    if (parent && parent.childNodes[index]) {
      parent.removeChild(parent.childNodes[index]);
    }
  }

  updateTextNode(parent, oldVNode, newVNode, index) {
    const oldText = String(oldVNode);
    const newText = String(newVNode);
    
    if (oldText !== newText) {
      const textNode = parent.childNodes[index];
      if (textNode && textNode.nodeType === 3) {
        textNode.textContent = newText;
      }
    }
    return parent.childNodes[index];
  }

  updateElement(parent, oldVNode, newVNode, index) {
    if (!parent) return null;
    const domNode = parent.childNodes[index];
    if (domNode) {
      this.updateDomNode(domNode, oldVNode, newVNode);
    }
    return domNode;
  }
}

// Singleton instance
export const reconciler = new Reconciler();

// Export for use in Component
export function reconcile(parentDom, oldVNode, newVNode) {
  return reconciler.reconcile(parentDom, oldVNode, newVNode);
}
