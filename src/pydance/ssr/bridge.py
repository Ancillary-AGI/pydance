"""
SSR Bridge for Pydance Framework.

This module provides the bridge between server-side and client-side rendering,
enabling seamless communication and state synchronization.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Callable


@dataclass
class BridgeMessage:
    """Message structure for SSR bridge communication."""
    type: str
    payload: Dict[str, Any]
    timestamp: float
    request_id: Optional[str] = None


class SSRBridge:
    """
    Bridge between server-side and client-side rendering.

    Handles communication between SSR and client-side hydration,
    state synchronization, and real-time updates.
    """

    def __init__(self, client_entry: str = 'pydance-client/src/index.js'):
        self.client_entry = client_entry
        self.message_handlers: Dict[str, Callable] = {}
        self.state_listeners: List[Callable] = []
        self.connected = False

    async def initialize(self) -> None:
        """Initialize the SSR bridge."""
        self.connected = True

        # Register default message handlers
        self.register_handler('HYDRATE', self._handle_hydration)
        self.register_handler('STATE_UPDATE', self._handle_state_update)
        self.register_handler('ACTION', self._handle_action)

    def register_handler(self, message_type: str, handler: Callable) -> None:
        """Register a message handler."""
        self.message_handlers[message_type] = handler

    def register_state_listener(self, listener: Callable) -> None:
        """Register a state change listener."""
        self.state_listeners.append(listener)

    async def send_message(self, message_type: str, payload: Dict[str, Any]) -> None:
        """Send a message through the bridge."""
        message = BridgeMessage(
            type=message_type,
            payload=payload,
            timestamp=asyncio.get_event_loop().time()
        )

        # Handle message locally first
        if message_type in self.message_handlers:
            await self.message_handlers[message_type](message)

        # Broadcast to state listeners
        for listener in self.state_listeners:
            try:
                await listener(message)
            except Exception as e:
                print(f"Error in state listener: {e}")

    async def _handle_hydration(self, message: BridgeMessage) -> None:
        """Handle client-side hydration requests."""
        # This would coordinate with the hydration system
        pass

    async def _handle_state_update(self, message: BridgeMessage) -> None:
        """Handle state updates from client."""
        # Broadcast state changes to all listeners
        for listener in self.state_listeners:
            await listener(message)

    async def _handle_action(self, message: BridgeMessage) -> None:
        """Handle actions from client-side."""
        # Process actions and potentially trigger server-side updates
        pass

    def create_bootstrap_script(self, initial_data: Dict[str, Any] = None) -> str:
        """Create bootstrap script for client-side initialization."""
        data = initial_data or {}

        return f"""
        <script>
            (function() {{
                window.__PYDANCE_BRIDGE__ = {{
                    initialized: true,
                    initialData: {json.dumps(data)},
                    sendMessage: function(type, payload) {{
                        return fetch('/__ssr_bridge__', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{ type, payload, timestamp: Date.now() }})
                        }});
                    }},
                    onMessage: function(callback) {{
                        // WebSocket or SSE connection for real-time updates
                        if (window.WebSocket) {{
                            const ws = new WebSocket('ws://' + window.location.host + '/__ssr_ws__');
                            ws.onmessage = function(event) {{
                                const message = JSON.parse(event.data);
                                callback(message);
                            }};
                        }}
                    }}
                }};

                // Auto-hydrate when DOM is ready
                if (document.readyState === 'loading') {{
                    document.addEventListener('DOMContentLoaded', function() {{
                        if (window.__SSR_DATA__ && window.__PYDANCE_SSR__) {{
                            // Trigger hydration with SSR data
                            console.log('Hydrating with SSR data:', window.__SSR_DATA__);
                        }}
                    }});
                }} else {{
                    if (window.__SSR_DATA__ && window.__PYDANCE_SSR__) {{
                        console.log('Hydrating with SSR data:', window.__SSR_DATA__);
                    }}
                }}
            }})();
        </script>
        """

    async def handle_client_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming message from client."""
        try:
            message = BridgeMessage(
                type=message_data.get('type', 'UNKNOWN'),
                payload=message_data.get('payload', {}),
                timestamp=message_data.get('timestamp', asyncio.get_event_loop().time()),
                request_id=message_data.get('request_id')
            )

            # Route to appropriate handler
            if message.type in self.message_handlers:
                await self.message_handlers[message.type](message)

            return {'status': 'success', 'message_id': message.request_id}

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'message_id': message_data.get('request_id')
            }

    def get_bridge_info(self) -> Dict[str, Any]:
        """Get information about the bridge configuration."""
        return {
            'client_entry': self.client_entry,
            'connected': self.connected,
            'handlers': list(self.message_handlers.keys()),
            'listeners': len(self.state_listeners)
        }

