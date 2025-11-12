"""
Mocking Framework for Pydance

A comprehensive mocking library inspired by Mockito and unittest.mock,
providing powerful mocking capabilities for testing Pydance applications.
"""

import inspect
from typing import Any, Dict, List, Optional, Callable, Union
import sys


class Mock:
    """
    A flexible mock object that can be configured to return specific values,
    raise exceptions, or track method calls.
    """

    def __init__(self, spec=None, name=None, **kwargs):
        self._mock_name = name or 'Mock'
        self._mock_calls = []
        self._mock_return_value = None
        self._mock_side_effect = None
        self._mock_children = {}
        self._spec = spec

        # Set any initial attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __getattr__(self, name):
        if name.startswith('_mock_'):
            return object.__getattribute__(self, name)

        if name not in self._mock_children:
            self._mock_children[name] = Mock(name=f"{self._mock_name}.{name}")

        return self._mock_children[name]

    def __call__(self, *args, **kwargs):
        self._mock_calls.append((args, kwargs))

        if self._mock_side_effect is not None:
            if callable(self._mock_side_effect):
                return self._mock_side_effect(*args, **kwargs)
            elif isinstance(self._mock_side_effect, list):
                if self._mock_side_effect:
                    return self._mock_side_effect.pop(0)
                else:
                    raise StopIteration()
            else:
                raise self._mock_side_effect

        return self._mock_return_value

    @property
    def return_value(self):
        """Get the return value."""
        return self._mock_return_value

    @return_value.setter
    def return_value(self, value):
        """Set the return value."""
        self._mock_return_value = value

    @property
    def side_effect(self):
        """Get the side effect."""
        return self._mock_side_effect

    @side_effect.setter
    def side_effect(self, value):
        """Set the side effect."""
        self._mock_side_effect = value

    @property
    def called(self):
        """True if the mock has been called."""
        return len(self._mock_calls) > 0

    @property
    def call_count(self):
        """Number of times the mock has been called."""
        return len(self._mock_calls)

    @property
    def call_args(self):
        """Arguments of the last call."""
        if self._mock_calls:
            return self._mock_calls[-1]
        return None

    @property
    def call_args_list(self):
        """List of all call arguments."""
        return self._mock_calls.copy()

    def reset_mock(self):
        """Reset the mock to its initial state."""
        self._mock_calls.clear()
        self._mock_return_value = None
        self._mock_side_effect = None
        for child in self._mock_children.values():
            child.reset_mock()

    def assert_called(self):
        """Assert that the mock was called."""
        assert self.called, f"Expected {self._mock_name} to be called"

    def assert_not_called(self):
        """Assert that the mock was not called."""
        assert not self.called, f"Expected {self._mock_name} to not be called"

    def assert_called_once(self):
        """Assert that the mock was called exactly once."""
        assert self.call_count == 1, f"Expected {self._mock_name} to be called once, got {self.call_count}"

    def assert_called_with(self, *args, **kwargs):
        """Assert that the mock was called with specific arguments."""
        assert self.called, f"Expected {self._mock_name} to be called"
        last_args, last_kwargs = self.call_args
        assert last_args == args and last_kwargs == kwargs, \
            f"Expected {self._mock_name} to be called with {args}, {kwargs}, got {last_args}, {last_kwargs}"

    def __repr__(self):
        return f"<{self._mock_name}>"


class MagicMock(Mock):
    """
    A Mock that implements magic methods for more comprehensive mocking.
    """

    def __init__(self, spec=None, name=None, **kwargs):
        super().__init__(spec, name, **kwargs)
        self._mock_wraps = None

    def __len__(self):
        return self()

    def __iter__(self):
        return iter(self())

    def __bool__(self):
        return bool(self())

    def __int__(self):
        return int(self())

    def __float__(self):
        return float(self())

    def __str__(self):
        return str(self())

    def __repr__(self):
        if self._mock_name != 'MagicMock':
            return f"<{self._mock_name}>"
        return super().__repr__()

    def configure_mock(self, **kwargs):
        """Configure multiple attributes at once."""
        for key, value in kwargs.items():
            setattr(self, key, value)


def mock(spec=None, **kwargs):
    """
    Create a mock object.

    Args:
        spec: Object to mock the interface of
        **kwargs: Initial attributes

    Returns:
        Mock object
    """
    return Mock(spec=spec, **kwargs)


class _Patch:
    """
    Context manager and decorator for patching objects.
    """

    def __init__(self, target, new=None, spec=None, create=False, **kwargs):
        self.target = target
        self.new = new if new is not None else Mock(spec=spec, **kwargs)
        self.spec = spec
        self.create = create
        self.temp_original = None
        self.is_decorator = False

    def __enter__(self):
        self.start()
        return self.new

    def __exit__(self, *args):
        self.stop()

    def __call__(self, func):
        self.is_decorator = True

        @wraps(func)
        def wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)

        return wrapper

    def start(self):
        """Start the patch."""
        target_parts = self.target.split('.')
        target_obj = self._get_target_object(target_parts[:-1])
        attr_name = target_parts[-1]

        # Store original value
        if hasattr(target_obj, attr_name):
            self.temp_original = getattr(target_obj, attr_name)
        elif not self.create:
            raise AttributeError(f"{self.target} does not exist")

        # Set the mock
        setattr(target_obj, attr_name, self.new)

    def stop(self):
        """Stop the patch."""
        if self.temp_original is not None:
            target_parts = self.target.split('.')
            target_obj = self._get_target_object(target_parts[:-1])
            attr_name = target_parts[-1]
            setattr(target_obj, attr_name, self.temp_original)
        elif self.create:
            # Remove the attribute if it was created
            target_parts = self.target.split('.')
            target_obj = self._get_target_object(target_parts[:-1])
            attr_name = target_parts[-1]
            if hasattr(target_obj, attr_name):
                delattr(target_obj, attr_name)

    def _get_target_object(self, target_parts):
        """Get the target object from dotted path."""
        if not target_parts:
            return sys.modules['__main__']

        obj = sys.modules.get(target_parts[0])
        if obj is None:
            # Try importing
            try:
                obj = __import__(target_parts[0])
            except ImportError:
                raise ImportError(f"Cannot import {target_parts[0]}")

        for part in target_parts[1:]:
            obj = getattr(obj, part)

        return obj


def patch(target, new=None, spec=None, create=False, **kwargs):
    """
    Patch an object for testing.

    Args:
        target: Dotted path to the object to patch
        new: Replacement object (defaults to Mock)
        spec: Object to mock the interface of
        create: Whether to create the attribute if it doesn't exist
        **kwargs: Additional attributes for the mock

    Returns:
        _Patch context manager/decorator
    """
    return _Patch(target, new, spec, create, **kwargs)


def patch_object(target, attribute, new=None, spec=None, **kwargs):
    """
    Patch an attribute of an object.

    Args:
        target: Object to patch
        attribute: Attribute name to patch
        new: Replacement object
        spec: Object to mock the interface of
        **kwargs: Additional attributes for the mock

    Returns:
        _Patch context manager/decorator
    """
    full_target = f"{target.__module__}.{target.__name__}.{attribute}"
    return _Patch(full_target, new, spec, **kwargs)


def patch_dict(target, values=(), clear=False, **kwargs):
    """
    Patch a dictionary for testing.

    Args:
        target: Dictionary to patch
        values: Values to add to the dictionary
        clear: Whether to clear the dictionary first
        **kwargs: Additional key-value pairs

    Returns:
        _Patch context manager/decorator
    """
    class _DictPatch(_Patch):
        def __init__(self, target, values, clear, **kwargs):
            self.target = target
            self.values = dict(values)
            self.values.update(kwargs)
            self.clear = clear
            self.temp_original = {}

        def start(self):
            if self.clear:
                self.temp_original.update(self.target)
                self.target.clear()
            else:
                for key in self.values:
                    if key in self.target:
                        self.temp_original[key] = self.target[key]

            self.target.update(self.values)

        def stop(self):
            if self.clear:
                self.target.clear()
                self.target.update(self.temp_original)
            else:
                for key in self.values:
                    if key in self.temp_original:
                        self.target[key] = self.temp_original[key]
                    else:
                        del self.target[key]

    return _DictPatch(target, values, clear, **kwargs)


def patch_multiple(target, spec=None, create=False, **kwargs):
    """
    Patch multiple attributes of an object.

    Args:
        target: Object to patch
        spec: Object to mock the interface of
        create: Whether to create attributes if they don't exist
        **kwargs: Attribute names and their replacement values

    Returns:
        _Patch context manager/decorator
    """
    class _MultiplePatch:
        def __init__(self, target, spec, create, **kwargs):
            self.patches = []
            for attr, value in kwargs.items():
                full_target = f"{target.__module__}.{target.__name__}.{attr}"
                self.patches.append(_Patch(full_target, value, spec, create))

        def __enter__(self):
            for patch in self.patches:
                patch.start()
            return self

        def __exit__(self, *args):
            for patch in reversed(self.patches):
                patch.stop()

        def __call__(self, func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                with self:
                    return func(*args, **kwargs)
            return wrapper

    return _MultiplePatch(target, spec, create, **kwargs)


# Convenience functions
def create_autospec(spec, spec_set=False, instance=False, **kwargs):
    """
    Create a mock with the same interface as the spec.
    """
    mock_obj = Mock(spec=spec, **kwargs)

    if spec and inspect.isclass(spec):
        # For classes, mock the __init__ method
        mock_obj.__init__ = Mock(name=f"{spec.__name__}.__init__")

    return mock_obj


def seal(mock_obj):
    """
    Seal a mock to prevent creation of new attributes.
    """
    # This is a simplified implementation
    # In a full implementation, this would prevent new attribute creation
    return mock_obj


__all__ = [
    'Mock',
    'MagicMock',
    'mock',
    'patch',
    'patch_object',
    'patch_dict',
    'patch_multiple',
    'create_autospec',
    'seal',
]
