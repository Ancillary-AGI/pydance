"""
Log aggregation system for Pydance monitoring.
Collects and aggregates logs from various sources.
"""

from typing import Dict, Any, List, Optional
import logging
import time
import json


@dataclass
class LogEntry:
    """Log entry structure"""

    timestamp: float
    level: str
    message: str
    logger_name: str
    module: str
    function: str
    line: int
    extra: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "message": self.message,
            "logger_name": self.logger_name,
            "module": self.module,
            "function": self.function,
            "line": self.line,
            "extra": self.extra or {}
        }


class LogAggregator:
    """Log aggregation and analysis system"""

    def __init__(self):
        self.logs: List[LogEntry] = []
        self.max_logs = 10000  # Maximum logs to keep in memory
        self.log_handlers: List[logging.Handler] = []
        self.filters: List[callable] = []

        # Statistics
        self.stats = defaultdict(int)
        self.error_counts = defaultdict(int)
        self.warning_counts = defaultdict(int)

        self._setup_default_handler()

    def _setup_default_handler(self):
        """Set up default log handler"""
        class AggregatorHandler(logging.Handler):
            def __init__(self, aggregator):
                super().__init__()
                self.aggregator = aggregator

            def emit(self, record):
                self.aggregator.add_log(record)

        handler = AggregatorHandler(self)
        handler.setLevel(logging.DEBUG)
        self.log_handlers.append(handler)

    def add_log(self, record: logging.LogRecord):
        """Add a log record to the aggregator"""
        # Apply filters
        for filter_func in self.filters:
            if not filter_func(record):
                return

        # Create log entry
        log_entry = LogEntry(
            timestamp=record.created,
            level=record.levelname,
            message=record.getMessage(),
            logger_name=record.name,
            module=getattr(record, 'module', 'unknown'),
            function=record.funcName or 'unknown',
            line=record.lineno,
            extra=getattr(record, 'extra', None)
        )

        # Add to logs
        self.logs.append(log_entry)

        # Maintain max logs limit
        if len(self.logs) > self.max_logs:
            self.logs.pop(0)

        # Update statistics
        self.stats[record.levelname] += 1

        if record.levelno >= logging.ERROR:
            self.error_counts[record.name] += 1
        elif record.levelno >= logging.WARNING:
            self.warning_counts[record.name] += 1

    def add_filter(self, filter_func: callable):
        """Add a log filter"""
        self.filters.append(filter_func)

    def get_logs(self, level: Optional[str] = None, logger_name: Optional[str] = None,
                 limit: int = 100, since: Optional[float] = None) -> List[LogEntry]:
        """Get filtered logs"""
        filtered_logs = self.logs

        if level:
            filtered_logs = [log for log in filtered_logs if log.level == level]

        if logger_name:
            filtered_logs = [log for log in filtered_logs if log.logger_name == logger_name]

        if since:
            filtered_logs = [log for log in filtered_logs if log.timestamp >= since]

        return filtered_logs[-limit:]

    def get_statistics(self) -> Dict[str, Any]:
        """Get log statistics"""
        return {
            "total_logs": len(self.logs),
            "level_counts": dict(self.stats),
            "error_counts": dict(self.error_counts),
            "warning_counts": dict(self.warning_counts),
            "timestamp": time.time()
        }

    def get_recent_errors(self, limit: int = 10) -> List[LogEntry]:
        """Get recent error logs"""
        error_logs = [log for log in self.logs if log.level in ['ERROR', 'CRITICAL']]
        return error_logs[-limit:]

    def get_recent_warnings(self, limit: int = 10) -> List[LogEntry]:
        """Get recent warning logs"""
        warning_logs = [log for log in self.logs if log.level == 'WARNING']
        return warning_logs[-limit:]

    def search_logs(self, query: str, limit: int = 50) -> List[LogEntry]:
        """Search logs by message content"""
        query_lower = query.lower()
        matching_logs = []

        for log in reversed(self.logs):  # Search from most recent
            if query_lower in log.message.lower():
                matching_logs.append(log)
                if len(matching_logs) >= limit:
                    break

        return matching_logs

    def export_logs(self, format: str = 'json') -> str:
        """Export logs in specified format"""
        if format == 'json':
            return json.dumps([log.to_dict() for log in self.logs], indent=2)
        elif format == 'text':
            lines = []
            for log in self.logs:
                lines.append(f"[{log.timestamp}] {log.level} {log.logger_name}: {log.message}")
            return '\n'.join(lines)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def clear_logs(self):
        """Clear all logs"""
        self.logs.clear()
        self.stats.clear()
        self.error_counts.clear()
        self.warning_counts.clear()

    def get_log_handlers(self) -> List[logging.Handler]:
        """Get log handlers for attaching to loggers"""
        return self.log_handlers.copy()