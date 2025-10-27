"""
Comprehensive unit tests for the Pydance Client Component system.
Tests component lifecycle, state management, rendering, and performance.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from pydance.core.Component import Component
from pydance.core.Store import Store
from pydance.core.Signal import Signal


class TestComponent:
    """Test cases for Component class"""

    def setup_method(self):
        """Setup for each test method"""
        self.store = Store()
        self.component = Component()

    def test_component_initialization(self):
        """Test component initializes correctly"""
        assert self.component.props == {}
        assert self.component.state == {}
        assert self.component.children == []
        assert self.component.store is None
        assert self.component.signals == {}
        assert self.component._mounted is False
        assert self.component._rendered is False

    def test_component_with_props(self):
        """Test component with initial props"""
        props = {'title': 'Test Component', 'count': 5}
        component = Component(props=props)

        assert component.props == props

    def test_component_with_store(self):
        """Test component with store integration"""
        component = Component(store=self.store)

        assert component.store == self.store

    def test_component_state_management(self):
        """Test component state management"""
        # Test initial state
        assert self.component.state == {}

        # Test setting state
        new_state = {'count': 1, 'text': 'hello'}
        self.component.set_state(new_state)
        assert self.component.state == new_state

        # Test updating state
        self.component.set_state({'count': 2})
        assert self.component.state == {'count': 2, 'text': 'hello'}

    def test_component_signal_management(self):
        """Test component signal management"""
        signal1 = Signal()
        signal2 = Signal()

        self.component.add_signal('signal1', signal1)
        self.component.add_signal('signal2', signal2)

        assert self.component.signals['signal1'] == signal1
        assert self.component.signals['signal2'] == signal2

    def test_component_lifecycle_methods(self):
        """Test component lifecycle method calls"""
        lifecycle_calls = []

        class TestComponent(Component):
            def component_did_mount(self):
                lifecycle_calls.append('did_mount')

            def component_did_update(self):
                lifecycle_calls.append('did_update')

            def component_will_unmount(self):
                lifecycle_calls.append('will_unmount')

        component = TestComponent()

        # Test mount
        component.mount()
        assert lifecycle_calls == ['did_mount']
        assert component._mounted is True

        # Test update
        component.set_state({'test': 'value'})
        assert lifecycle_calls == ['did_mount', 'did_update']

        # Test unmount
        component.unmount()
        assert lifecycle_calls == ['did_mount', 'did_update', 'will_unmount']

    def test_component_rendering(self):
        """Test component rendering"""
        class TestComponent(Component):
            def render(self):
                return {
                    'tag': 'div',
                    'props': {'class': 'test'},
                    'children': ['Hello, World!']
                }

        component = TestComponent()

        vdom = component.render()
        assert vdom['tag'] == 'div'
        assert vdom['props']['class'] == 'test'
        assert vdom['children'] == ['Hello, World!']

    def test_component_store_integration(self):
        """Test component store integration"""
        initial_state = {'count': 0}
        store = Store(initial_state)

        class CounterComponent(Component):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.subscribe_to_store()

            def subscribe_to_store(self):
                if self.store:
                    self.store.subscribe('count', self.on_count_change)

            def on_count_change(self, new_count):
                self.set_state({'count': new_count})

        component = CounterComponent(store=store)

        # Test initial state
        assert component.state == {}

        # Test store subscription
        store.set_state({'count': 5})
        assert component.state['count'] == 5

    def test_component_props_update(self):
        """Test component props update"""
        initial_props = {'title': 'Initial'}
        component = Component(props=initial_props)

        assert component.props['title'] == 'Initial'

        # Update props
        new_props = {'title': 'Updated'}
        component.update_props(new_props)
        assert component.props['title'] == 'Updated'

    def test_component_error_handling(self):
        """Test component error handling"""
        class ErrorComponent(Component):
            def render(self):
                raise ValueError("Render error")

        component = ErrorComponent()

        # Test error in render
        with pytest.raises(ValueError):
            component.render()

    def test_component_performance_tracking(self):
        """Test component performance tracking"""
        class SlowComponent(Component):
            def render(self):
                # Simulate slow rendering
                import time
                time.sleep(0.01)
                return {'tag': 'div', 'children': ['Slow component']}

        component = SlowComponent()

        # Test render performance
        import time
        start_time = time.time()
        vdom = component.render()
        render_time = time.time() - start_time

        assert render_time > 0.01  # Should take at least 10ms
        assert vdom['tag'] == 'div'


class TestComponentIntegration:
    """Integration tests for Component system"""

    def setup_method(self):
        """Setup for integration tests"""
        self.store = Store()
        self.signal = Signal()

    def test_component_tree_integration(self):
        """Test component tree integration"""
        class ParentComponent(Component):
            def render(self):
                return {
                    'tag': 'div',
                    'props': {'class': 'parent'},
                    'children': [
                        {
                            'tag': 'h1',
                            'children': [self.props.get('title', 'No Title')]
                        },
                        {
                            'tag': 'p',
                            'children': [f"Count: {self.state.get('count', 0)}"]
                        }
                    ]
                }

        component = ParentComponent(props={'title': 'Test App'})

        vdom = component.render()
        assert vdom['tag'] == 'div'
        assert vdom['props']['class'] == 'parent'
        assert len(vdom['children']) == 2

    def test_component_store_reactivity(self):
        """Test component reactivity with store"""
        class ReactiveComponent(Component):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.store_data = None
                if self.store:
                    self.store.subscribe('data', self.on_store_change)

            def on_store_change(self, new_data):
                self.store_data = new_data
                self.set_state({'store_value': new_data})

        component = ReactiveComponent(store=self.store)

        # Test initial state
        assert component.store_data is None

        # Test store update
        self.store.set_state({'data': 'test_value'})
        assert component.store_data == 'test_value'
        assert component.state['store_value'] == 'test_value'

    def test_component_signal_integration(self):
        """Test component signal integration"""
        signal_data = []

        class SignalComponent(Component):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                if 'test_signal' in self.signals:
                    self.signals['test_signal'].subscribe(self.on_signal)

            def on_signal(self, data):
                signal_data.append(data)
                self.set_state({'signal_received': data})

        component = SignalComponent(signals={'test_signal': self.signal})

        # Test signal emission
        self.signal.emit('test_message')
        assert signal_data == ['test_message']
        assert component.state['signal_received'] == 'test_message'


class TestComponentPerformance:
    """Performance tests for Component system"""

    def setup_method(self):
        """Setup for performance tests"""
        self.store = Store()

    def test_component_rendering_performance(self):
        """Test component rendering performance"""
        class FastComponent(Component):
            def render(self):
                return {
                    'tag': 'div',
                    'props': {'class': 'fast'},
                    'children': ['Fast component']
                }

        component = FastComponent()

        # Test render performance
        import time
        start_time = time.time()

        for _ in range(1000):
            vdom = component.render()

        end_time = time.time()
        total_time = end_time - start_time

        # Should be very fast (< 100ms for 1000 renders)
        assert total_time < 0.1
        assert vdom['tag'] == 'div'

    def test_component_state_update_performance(self):
        """Test component state update performance"""
        component = Component()

        # Test state update performance
        import time
        start_time = time.time()

        for i in range(1000):
            component.set_state({'counter': i})

        end_time = time.time()
        total_time = end_time - start_time

        # Should be fast (< 50ms for 1000 updates)
        assert total_time < 0.05
        assert component.state['counter'] == 999

    def test_component_memory_usage(self):
        """Test component memory usage"""
        components = []

        # Create many components
        for i in range(1000):
            component = Component(props={'id': i})
            components.append(component)

        # Test memory usage
        assert len(components) == 1000

        # Clean up
        del components


class TestComponentErrorHandling:
    """Error handling tests for Component system"""

    def setup_method(self):
        """Setup for error handling tests"""
        self.component = Component()

    def test_component_error_in_lifecycle(self):
        """Test error handling in component lifecycle"""
        class ErrorComponent(Component):
            def component_did_mount(self):
                raise ValueError("Mount error")

        component = ErrorComponent()

        # Test error in mount
        with pytest.raises(ValueError):
            component.mount()

    def test_component_error_in_render(self):
        """Test error handling in component render"""
        class ErrorComponent(Component):
            def render(self):
                raise ValueError("Render error")

        component = ErrorComponent()

        # Test error in render
        with pytest.raises(ValueError):
            component.render()

    def test_component_error_in_update(self):
        """Test error handling in component update"""
        class ErrorComponent(Component):
            def component_did_update(self):
                raise ValueError("Update error")

        component = ErrorComponent()

        # Test error in update
        with pytest.raises(ValueError):
            component.set_state({'test': 'value'})


class TestComponentAdvancedFeatures:
    """Test advanced component features"""

    def setup_method(self):
        """Setup for advanced feature tests"""
        self.store = Store()
        self.signal = Signal()

    def test_component_conditional_rendering(self):
        """Test conditional rendering"""
        class ConditionalComponent(Component):
            def render(self):
                if self.state.get('show_content', False):
                    return {
                        'tag': 'div',
                        'props': {'class': 'visible'},
                        'children': ['Visible content']
                    }
                else:
                    return {
                        'tag': 'div',
                        'props': {'class': 'hidden'},
                        'children': ['Hidden content']
                    }

        component = ConditionalComponent()

        # Test hidden state
        vdom = component.render()
        assert vdom['props']['class'] == 'hidden'

        # Test visible state
        component.set_state({'show_content': True})
        vdom = component.render()
        assert vdom['props']['class'] == 'visible'

    def test_component_list_rendering(self):
        """Test list rendering"""
        class ListComponent(Component):
            def render(self):
                items = self.state.get('items', [])
                return {
                    'tag': 'ul',
                    'children': [
                        {
                            'tag': 'li',
                            'children': [item]
                        } for item in items
                    ]
                }

        component = ListComponent()
        component.set_state({'items': ['item1', 'item2', 'item3']})

        vdom = component.render()
        assert vdom['tag'] == 'ul'
        assert len(vdom['children']) == 3
        assert vdom['children'][0]['children'] == ['item1']

    def test_component_event_handling(self):
        """Test component event handling"""
        events_handled = []

        class EventComponent(Component):
            def handle_click(self, event_data):
                events_handled.append(event_data)
                self.set_state({'click_count': self.state.get('click_count', 0) + 1})

        component = EventComponent()

        # Test event handling
        component.handle_click('button_click')
        assert events_handled == ['button_click']
        assert component.state['click_count'] == 1

    def test_component_form_handling(self):
        """Test component form handling"""
        class FormComponent(Component):
            def handle_input_change(self, field, value):
                self.set_state({field: value})

            def render(self):
                return {
                    'tag': 'form',
                    'children': [
                        {
                            'tag': 'input',
                            'props': {
                                'value': self.state.get('name', ''),
                                'onchange': lambda v: self.handle_input_change('name', v)
                            }
                        }
                    ]
                }

        component = FormComponent()

        # Test form state management
        component.handle_input_change('name', 'John Doe')
        assert component.state['name'] == 'John Doe'

        vdom = component.render()
        assert vdom['children'][0]['props']['value'] == 'John Doe'


if __name__ == '__main__':
    # Run tests if executed directly
    pytest.main([__file__])
