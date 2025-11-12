"""Monitoring-related type definitions."""

from typing import Dict, Union
from dataclasses import dataclass, field


@dataclass
class Metrics:
    """Application metrics."""
    name: str
    value: Union[int, float]
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class MetricValue:
    """Metric value."""
    timestamp: datetime
    value: Union[int, float]
    labels: Dict[str, str] = field(default_factory=dict)


__all__ = ['Metrics', 'MetricValue']
