"""
Load balancing types for Pydance.
"""
from typing import Dict, Any

@dataclass
class BackendServer:
    host: str
    port: int
    weight: int = 1
    healthy: bool = True
    connections: int = 0
    max_connections: int = 100

@dataclass
class LoadBalancerConfig:
    algorithm: str = "round_robin"
    health_check_interval: int = 30
    health_check_timeout: int = 5
    sticky_sessions: bool = False
