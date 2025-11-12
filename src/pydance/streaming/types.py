"""Streaming-related type definitions."""

from typing import Dict, Any
from dataclasses import dataclass, field


class StreamType(Enum):
    """Stream types."""
    LIVE = "live"
    RECORDED = "recorded"
    DASH = "dash"
    HLS = "hls"


@dataclass
class StreamConfig:
    """Configuration for streaming."""
    type: StreamType = StreamType.LIVE
    bitrate: int = 128000
    format: str = "mp3"
    quality: str = "high"
    buffer_size: int = 8192


@dataclass
class ClientSession:
    """WebSocket client session."""
    id: str
    connected_at: datetime
    last_activity: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


__all__ = ['StreamType', 'StreamConfig', 'ClientSession']
