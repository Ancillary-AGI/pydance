"""
Trace management system for Pydance monitoring.
Provides distributed tracing capabilities.
"""

from typing import Dict, Any, List, Optional, ContextManager
import time
import uuid
import threading


@dataclass
class TraceSpan:
    """Represents a trace span"""

    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    tags: Dict[str, Any] = None
    logs: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = {}
        if self.logs is None:
            self.logs = []

    def finish(self):
        """Finish the span"""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time

    def add_tag(self, key: str, value: Any):
        """Add a tag to the span"""
        self.tags[key] = value

    def log(self, event: str, **kwargs):
        """Add a log entry to the span"""
        log_entry = {
            "timestamp": time.time(),
            "event": event,
            **kwargs
        }
        self.logs.append(log_entry)


class TraceContext:
    """Trace context for managing active spans"""

    def __init__(self):
        self.current_span: Optional[TraceSpan] = None
        self.spans: List[TraceSpan] = []

    def start_span(self, name: str, parent_span: Optional[TraceSpan] = None) -> TraceSpan:
        """Start a new span"""
        span_id = str(uuid.uuid4())
        trace_id = parent_span.trace_id if parent_span else str(uuid.uuid4())

        span = TraceSpan(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span.span_id if parent_span else None,
            name=name,
            start_time=time.time()
        )

        self.spans.append(span)
        self.current_span = span
        return span

    def finish_span(self, span: TraceSpan):
        """Finish a span"""
        span.finish()

    def get_current_span(self) -> Optional[TraceSpan]:
        """Get the current active span"""
        return self.current_span


# Context variable for trace context
trace_context: ContextVar[Optional[TraceContext]] = ContextVar('trace_context', default=None)


class TraceManager:
    """Distributed tracing manager"""

    def __init__(self):
        self.spans: List[TraceSpan] = []
        self.max_spans = 10000
        self.exporters: List[callable] = []
        self.samplers: List[callable] = []
        self._lock = threading.Lock()

    def start_trace(self, name: str) -> TraceContext:
        """Start a new trace"""
        context = TraceContext()
        trace_context.set(context)
        context.start_span(name)
        return context

    def get_current_context(self) -> Optional[TraceContext]:
        """Get the current trace context"""
        return trace_context.get()

    def start_span(self, name: str) -> TraceSpan:
        """Start a new span in the current trace"""
        context = self.get_current_context()
        if not context:
            # Create new trace if none exists
            context = self.start_trace("auto_trace")
            trace_context.set(context)

        parent_span = context.get_current_span()
        span = context.start_span(name, parent_span)
        return span

    def finish_span(self, span: TraceSpan):
        """Finish a span"""
        span.finish()

        # Apply sampling
        if self._should_sample(span):
            with self._lock:
                self.spans.append(span)

                # Maintain max spans limit
                if len(self.spans) > self.max_spans:
                    self.spans.pop(0)

                # Export span
                self._export_span(span)

    def add_span_tag(self, span: TraceSpan, key: str, value: Any):
        """Add a tag to a span"""
        span.add_tag(key, value)

    def log_to_span(self, span: TraceSpan, event: str, **kwargs):
        """Add a log entry to a span"""
        span.log(event, **kwargs)

    def _should_sample(self, span: TraceSpan) -> bool:
        """Determine if span should be sampled"""
        for sampler in self.samplers:
            if not sampler(span):
                return False
        return True

    def _export_span(self, span: TraceSpan):
        """Export span to configured exporters"""
        for exporter in self.exporters:
            try:
                exporter(span)
            except Exception as e:
                print(f"Trace export error: {e}")

    def add_exporter(self, exporter: callable):
        """Add a span exporter"""
        self.exporters.append(exporter)

    def add_sampler(self, sampler: callable):
        """Add a sampling function"""
        self.samplers.append(sampler)

    def get_spans(self, trace_id: Optional[str] = None, limit: int = 100) -> List[TraceSpan]:
        """Get spans, optionally filtered by trace ID"""
        with self._lock:
            if trace_id:
                filtered_spans = [span for span in self.spans if span.trace_id == trace_id]
            else:
                filtered_spans = self.spans

            return filtered_spans[-limit:]

    def get_trace_spans(self, trace_id: str) -> List[TraceSpan]:
        """Get all spans for a specific trace"""
        with self._lock:
            return [span for span in self.spans if span.trace_id == trace_id]

    def clear_spans(self):
        """Clear all stored spans"""
        with self._lock:
            self.spans.clear()

    def get_statistics(self) -> Dict[str, Any]:
        """Get tracing statistics"""
        with self._lock:
            total_spans = len(self.spans)
            traces = set(span.trace_id for span in self.spans)
            total_traces = len(traces)

            return {
                "total_spans": total_spans,
                "total_traces": total_traces,
                "exporters_count": len(self.exporters),
                "samplers_count": len(self.samplers)
            }


# Global trace manager
_trace_manager = None

def get_trace_manager() -> TraceManager:
    """Get global trace manager"""
    global _trace_manager
    if _trace_manager is None:
        _trace_manager = TraceManager()
    return _trace_manager


class Tracer:
    """Convenience class for tracing"""

    def __init__(self, manager: Optional[TraceManager] = None):
        self.manager = manager or get_trace_manager()

    def start_span(self, name: str) -> ContextManager[TraceSpan]:
        """Context manager for tracing"""
        class SpanContext:
            def __init__(self, tracer, name):
                self.tracer = tracer
                self.name = name
                self.span = None

            def __enter__(self):
                self.span = self.tracer.manager.start_span(self.name)
                return self.span

            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.span:
                    if exc_val:
                        self.span.add_tag("error", True)
                        self.span.add_tag("error.message", str(exc_val))
                    self.tracer.manager.finish_span(self.span)

        return SpanContext(self, name)