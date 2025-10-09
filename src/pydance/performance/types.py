"""Performance-related type definitions."""
from dataclasses import dataclass, field
from typing import Dict, Any, Union, List
from datetime import datetime

@dataclass
class PerformanceThreshold:
    metric: str
    operator: str
    value: Union[int, float]
    severity: str = "warning"

@dataclass
class PerformanceSnapshot:
    timestamp: datetime
    metrics: Dict[str, Union[int, float]]
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OptimizationRecommendation:
    type: str
    description: str
    impact: str
    implementation: str
    priority: str = "medium"

@dataclass
class ProfileResult:
    function_name: str
    calls: int
    total_time: float
    avg_time: float
    max_time: float
    min_time: float

@dataclass
class BenchmarkResult:
    name: str
    iterations: int
    total_time: float
    avg_time: float
    throughput: float

@dataclass
class LoadTestScenario:
    name: str
    duration: int
    users: int
    ramp_up: int
    endpoints: List[str]




__all__ = [
    'PerformanceThreshold', 'PerformanceSnapshot', 'ProfileResult'
]
