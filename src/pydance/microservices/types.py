"""
Microservices types for Pydance.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime

@dataclass
class ServiceInstance:
    id: str
    name: str
    host: str
    port: int
    health_check_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LogEntry:
    term: int
    index: int
    command: str
    timestamp: datetime

@dataclass
class Event:
    id: str
    type: str
    aggregate_id: str
    data: Dict[str, Any]
    timestamp: datetime
    version: int

@dataclass
class GRPCConfig:
    host: str = "localhost"
    port: int = 50051
    max_workers: int = 10
    options: Dict[str, Any] = field(default_factory=dict)
