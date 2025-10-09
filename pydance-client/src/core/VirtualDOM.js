/**
 * Virtual DOM with O(n) diffing algorithm
 * Preserves all existing rendering functionality
 */

import { JSXElement, JSXFragment } from './Component.js';

/**
 * Virtual DOM node types
 */
export const VNodeType = {
  ELEMENT: 'element',
  TEXT: 'text',
  FRAGMENT: 'fragment',
  COMPONENT: 'component'
};

/**
 * Patch types for efficient updates
 */
export const PatchType = {
  CREATE: 'CREATE',
  REMOVE: 'REMOVE',
  REPLACE: 'REPLACE',
  UPDATE: 'UPDATE',
  REORDER: 'REORDER'
};

/**
 * Virtual DOM node
 */
export class VNode {
  constructor(type, props = {}, children = [], key = null) {
    this.type = type;
    this.props = props;
    this.children = Array.isArray(children) ? children : [children];
    this.key = key || props?.key || null;
    this.ref = props?.ref || null;
  }
  
  static text(value) {
    return new VNode(VNodeType.TEXT, { value: String(value) }, []);
  }
  
  static element(tag, props, children) {
    return new VNode(VNodeType.ELEMENT, { tag, ...props }, children);
  }
  
  static fragment(children) {
    return new VNode(VNodeType.FRAGMENT, {}, children);
  }
}

/**
 * O(n) Virtual DOM differ with key-based reconciliation
 * Preserves existing functionality
 */
export class VirtualDOM {
  constructor() {
    this.cache = new WeakMap();
  }
  
  /**
   * Diff two virtual DOM trees - O(n) complexity
   */
  diff(oldVNode, newVNode) {
    // Early exit for identical nodes
    if (oldVNode === newVNode) {
      return null;
    }
    
    // Handle null/undefined
    if (!oldVNode && newVNode) {
      return { type: PatchType.CREATE, vnode: newVNode };
    }
    if (oldVNode && !newVNode) {
      return { type: PatchType.REMOVE };
    }
    
    // Type changed - replace
    if (oldVNode.type !== newVNode.type) {
      return { type: PatchType.REPLACE, vnode: newVNode };
    }
    
    // Text nodes
    if (oldVNode.type === VNodeType.TEXT) {
      if (oldVNode.props.value !== newVNode.props.value) {
        return { type: PatchType.UPDATE, props: newVNode.props };
      }
      return null;
    }
    
    // Element nodes
    if (oldVNode.type === VNodeType.ELEMENT) {
      const patches = {};
      
      // Diff props
      const propPatches = this.diffProps(oldVNode.props, newVNode.props);
      if (propPatches) {
        patches.props = propPatches;
      }
      
      // Diff children with keys
      const childPatches = this.diffChildren(oldVNode.children, newVNode.children);
      if (childPatches && childPatches.length > 0) {
        patches.children = childPatches;
      }
      
      return Object.keys(patches).length > 0 ? { type: PatchType.UPDATE, ...patches } : null;
    }
    
    // Fragment nodes
    if (oldVNode.type === VNodeType.FRAGMENT) {
      const childPatches = this.diffChildren(oldVNode.children, newVNode.children);
      return childPatches && childPatches.length > 0 
        ? { type: PatchType.UPDATE, children: childPatches }
        : null;
    }
    
    return null;
  }
  
  /**
   * Diff props - O(n) where n is number of props
   */
  diffProps(oldProps, newProps) {
    const patches = {};
    let hasChanges = false;
    
    // Check for changed/removed props
    for (const key in oldProps) {
      if (key === 'children' || key === 'key' || key === 'ref') continue;
      
      if (!(key in newProps)) {
        patches[key] = undefined;
        hasChanges = true;
      } else if (oldProps[key] !== newProps[key]) {
        patches[key] = newProps[key];
        hasChanges = true;
      }
    }
    
    // Check for new props
    for (const key in newProps) {
      if (key === 'children' || key === 'key' || key === 'ref') continue;
      
      if (!(key in oldProps)) {
        patches[key] = newProps[key];
        hasChanges = true;
      }
    }
    
    return hasChanges ? patches : null;
  }
  
  /**
   * Diff children with key-based reconciliation - O(n)
   */
  diffChildren(oldChildren, newChildren) {
    const patches = [];
    
    // Build key maps for O(1) lookup
    const oldKeyMap = new Map();
    const newKeyMap = new Map();
    
    oldChildren.forEach((child, i) => {
      if (child && child.key) {
        oldKeyMap.set(child.key, { child, index: i });
      }
    });
    
    newChildren.forEach((child, i) => {
      if (child && child.key) {
        newKeyMap.set(child.key, { child, index: i });
      }
    });
    
    // Process new children
    const maxLen = Math.max(oldChildren.length, newChildren.length);
    
    for (let i = 0; i < maxLen; i++) {
      const oldChild = oldChildren[i];
      const newChild = newChildren[i];
      
      // Use key-based matching if available
      if (newChild && newChild.key) {
        const oldMatch = oldKeyMap.get(newChild.key);
        
        if (oldMatch) {
          // Key exists - diff the nodes
          const patch = this.diff(oldMatch.child, newChild);
          if (patch) {
            patches.push({ index: i, patch });
          }
          
          // Check if reordering needed
          if (oldMatch.index !== i) {
            patches.push({ 
              index: i, 
              patch: { type: PatchType.REORDER, from: oldMatch.index, to: i }
            });
          }
        } else {
          // New key - create
          patches.push({ 
            index: i, 
            patch: { type: PatchType.CREATE, vnode: newChild }
          });
        }
      } else if (oldChild && !newChild) {
        // Child removed
        patches.push({ 
          index: i, 
          patch: { type: PatchType.REMOVE }
        });
      } else if (!oldChild && newChild) {
        // Child added
        patches.push({ 
          index: i, 
          patch: { type: PatchType.CREATE, vnode: newChild }
        });
      } else if (oldChild && newChild) {
        // Both exist - diff them
        const patch = this.diff(oldChild, newChild);
        if (patch) {
          patches.push({ index: i, patch });
        }
      }
    }
    
    return patches;
  }
  
  /**
   * Apply patches to DOM - O(n)
   */
  patch(domNode, patches) {
    if (!patches) return domNode;
    
    switch (patches.type) {
      case PatchType.CREATE:
        return this.create(patches.vnode);
      
      case PatchType.REMOVE:
        if (domNode.parentNode) {
          domNode.parentNode.removeChild(domNode);
        }
        return null;
      
      case PatchType.REPLACE:
        const newNode = this.create(patches.vnode);
        if (domNode.parentNode) {
          domNode.parentNode.replaceChild(newNode, domNode);
        }
        return newNode;
      
      case PatchType.UPDATE:
        this.update(domNode, patches);
        return domNode;
      
      case PatchType.REORDER:
        this.reorder(domNode, patches);
        return domNode;
      
      default:
        return domNode;
    }
  }
  
  /**
   * Create DOM node from VNode
   */
  create(vnode) {
    if (!vnode) return null;
    
    if (vnode.type === VNodeType.TEXT) {
      return document.createTextNode(vnode.props.value);
    }
    
    if (vnode.type === VNodeType.ELEMENT) {
      const el = document.createElement(vnode.props.tag);
      
      // Set props
      this.setProps(el, vnode.props);
      
      // Append children
      vnode.children.forEach(child => {
        const childNode = this.create(child);
        if (childNode) {
          el.appendChild(childNode);
        }
      });
      
      return el;
    }
    
    if (vnode.type === VNodeType.FRAGMENT) {
      const fragment = document.createDocumentFragment();
      vnode.children.forEach(child => {
        const childNode = this.create(child);
        if (childNode) {
          fragment.appendChild(childNode);
        }
      });
      return fragment;
    }
    
    return null;
  }
  
  /**
   * Update DOM node with patches
   */
  update(domNode, patches) {
    // Update props
    if (patches.props) {
      this.updateProps(domNode, patches.props);
    }
    
    // Update children
    if (patches.children) {
      patches.children.forEach(({ index, patch }) => {
        const childNode = domNode.childNodes[index];
        this.patch(childNode, patch);
      });
    }
  }
  
  /**
   * Set element props
   */
  setProps(el, props) {
    for (const key in props) {
      if (key === 'tag' || key === 'children' || key === 'key' || key === 'ref') continue;
      
      if (key === 'className') {
        el.className = props[key];
      } else if (key.startsWith('on')) {
        const eventName = key.slice(2).toLowerCase();
        el.addEventListener(eventName, props[key]);
      } else if (key === 'style' && typeof props[key] === 'object') {
        Object.assign(el.style, props[key]);
      } else {
        el.setAttribute(key, props[key]);
      }
    }
  }
  
  /**
   * Update element props
   */
  updateProps(el, propPatches) {
    for (const key in propPatches) {
      const value = propPatches[key];
      
      if (value === undefined) {
        // Remove prop
        if (key === 'className') {
          el.className = '';
        } else if (key.startsWith('on')) {
          const eventName = key.slice(2).toLowerCase();
          el.removeEventListener(eventName, el[key]);
        } else {
          el.removeAttribute(key);
        }
      } else {
        // Update prop
        if (key === 'className') {
          el.className = value;
        } else if (key.startsWith('on')) {
          const eventName = key.slice(2).toLowerCase();
          el.removeEventListener(eventName, el[key]);
          el.addEventListener(eventName, value);
          el[key] = value;
        } else if (key === 'style' && typeof value === 'object') {
          Object.assign(el.style, value);
        } else {
          el.setAttribute(key, value);
        }
      }
    }
  }
  
  /**
   * Reorder children
   */
  reorder(domNode, patches) {
    const { from, to } = patches;
    const child = domNode.childNodes[from];
    
    if (child) {
      domNode.removeChild(child);
      
      if (to >= domNode.childNodes.length) {
        domNode.appendChild(child);
      } else {
        domNode.insertBefore(child, domNode.childNodes[to]);
      }
    }
  }
}

// Export singleton instance
export const vdom = new VirtualDOM();

// Helper to convert JSX to VNode
export function jsxToVNode(jsx) {
  if (typeof jsx === 'string' || typeof jsx === 'number') {
    return VNode.text(jsx);
  }
  
  if (Array.isArray(jsx)) {
    return VNode.fragment(jsx.map(jsxToVNode));
  }
  
  if (jsx && jsx.$$typeof === Symbol.for('pydance.element')) {
    return VNode.element(
      jsx.tagName,
      jsx.props,
      jsx.children.map(jsxToVNode)
    );
  }
  
  if (jsx && jsx.$$typeof === Symbol.for('pydance.fragment')) {
    return VNode.fragment(jsx.children.map(jsxToVNode));
  }
  
  return null;
}
