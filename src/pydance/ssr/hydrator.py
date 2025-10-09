"""
Data Hydrator for Pydance SSR Framework.

This module handles data hydration for server-side rendered content,
ensuring seamless integration between server and client state.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass


@dataclass
class HydrationData:
    """Data structure for hydration."""
    component_id: str
    data: Any
    timestamp: float
    version: str = '1.0.0'
    checksum: Optional[str] = None


class DataHydrator:
    """
    Handles data hydration for SSR content.

    Manages the transfer of server-side data to client-side components
    for seamless hydration and state synchronization.
    """

    def __init__(self):
        self.hydration_registry: Dict[str, HydrationData] = {}
        self.hydration_listeners: List[Callable] = []

    def register_component(
        self,
        component_id: str,
        data: Any,
        version: str = '1.0.0'
    ) -> str:
        """Register a component for hydration."""
        import hashlib
        import time

        # Generate checksum for data integrity
        data_str = json.dumps(data, sort_keys=True)
        checksum = hashlib.sha256(data_str.encode()).hexdigest()[:16]

        hydration_data = HydrationData(
            component_id=component_id,
            data=data,
            timestamp=time.time(),
            version=version,
            checksum=checksum
        )

        self.hydration_registry[component_id] = hydration_data
        return checksum

    def get_hydration_data(self, component_id: str) -> Optional[HydrationData]:
        """Get hydration data for a component."""
        return self.hydration_registry.get(component_id)

    def get_all_hydration_data(self) -> Dict[str, HydrationData]:
        """Get all registered hydration data."""
        return self.hydration_registry.copy()

    def register_hydration_listener(self, listener: Callable) -> None:
        """Register a listener for hydration events."""
        self.hydration_listeners.append(listener)

    async def notify_hydration_complete(self, component_id: str) -> None:
        """Notify that hydration is complete for a component."""
        for listener in self.hydration_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(component_id, 'complete')
                else:
                    listener(component_id, 'complete')
            except Exception as e:
                print(f"Error in hydration listener: {e}")

    def generate_hydration_script(self, component_id: str = None) -> str:
        """Generate hydration script for client-side."""
        if component_id:
            data = self.get_hydration_data(component_id)
            if not data:
                return ''
            components_data = {component_id: data}
        else:
            components_data = self.get_all_hydration_data()

        if not components_data:
            return ''

        # Generate hydration script
        script = """
        <script>
            (function() {
                'use strict';

                const hydrationData = """ + json.dumps({
            cid: data.__dict__ if hasattr(data, '__dict__') else data
            for cid, data in components_data.items()
        }) + """;

                window.__HYDRATION_DATA__ = hydrationData;

                // Hydration function
                window.hydrateComponent = function(componentId, data) {
                    const element = document.querySelector(`[data-component-id="${componentId}"]`);
                    if (element && window.__HYDRATE__) {
                        window.__HYDRATE__(componentId, data);
                    }
                };

                // Auto-hydrate components when DOM is ready
                function autoHydrate() {
                    Object.keys(hydrationData).forEach(componentId => {
                        window.hydrateComponent(componentId, hydrationData[componentId]);
                    });
                }

                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', autoHydrate);
                } else {
                    autoHydrate();
                }
            })();
        </script>
        """

        return script

    def create_hydration_wrapper(
        self,
        component_id: str,
        html_content: str,
        data: Any = None
    ) -> str:
        """Wrap HTML content with hydration data."""
        if data is None:
            hydration_data = self.get_hydration_data(component_id)
            if not hydration_data:
                return html_content
            data = hydration_data.data

        # Add data attributes for hydration
        wrapper_div = f"""
        <div
            data-component-id="{component_id}"
            data-hydration-data="{json.dumps(data)}"
            data-ssr="true"
        >
            {html_content}
        </div>
        """

        return wrapper_div

    def validate_hydration_data(self, component_id: str, client_checksum: str) -> bool:
        """Validate hydration data integrity."""
        hydration_data = self.get_hydration_data(component_id)
        if not hydration_data or not hydration_data.checksum:
            return False

        return hydration_data.checksum == client_checksum

    def clear_hydration_data(self, component_id: str = None) -> None:
        """Clear hydration data."""
        if component_id:
            self.hydration_registry.pop(component_id, None)
        else:
            self.hydration_registry.clear()

    def get_hydration_stats(self) -> Dict[str, Any]:
        """Get hydration statistics."""
        return {
            'registered_components': len(self.hydration_registry),
            'listeners': len(self.hydration_listeners),
            'components': list(self.hydration_registry.keys())
        }

    async def batch_register_components(self, components: Dict[str, Any]) -> Dict[str, str]:
        """Register multiple components for hydration."""
        checksums = {}

        for component_id, data in components.items():
            checksum = self.register_component(component_id, data)
            checksums[component_id] = checksum

        return checksums

    def export_hydration_data(self) -> Dict[str, Any]:
        """Export hydration data for debugging or persistence."""
        return {
            'components': {
                cid: {
                    'data': data.data,
                    'timestamp': data.timestamp,
                    'version': data.version,
                    'checksum': data.checksum
                }
                for cid, data in self.hydration_registry.items()
            },
            'exported_at': asyncio.get_event_loop().time()
        }

    def import_hydration_data(self, data: Dict[str, Any]) -> None:
        """Import hydration data from external source."""
        components = data.get('components', {})

        for component_id, component_data in components.items():
            hydration_data = HydrationData(
                component_id=component_id,
                data=component_data['data'],
                timestamp=component_data['timestamp'],
                version=component_data['version'],
                checksum=component_data['checksum']
            )

            self.hydration_registry[component_id] = hydration_data

