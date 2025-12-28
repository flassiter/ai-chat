"""Source context and capabilities."""

from dataclasses import dataclass
from typing import Callable, Optional, Any

from .capture import CapturePayload


@dataclass
class SourceCapabilities:
    """Capabilities supported by a source."""

    supports_selection: bool = False
    supports_full_capture: bool = True
    supports_streaming: bool = False
    supports_attachments: bool = False


@dataclass
class SourceContext:
    """
    Context provided to sources with callbacks to host application.

    The host application provides callbacks for:
    - Requesting capture of content
    - Notifying status updates
    - Getting configuration values
    """

    request_capture: Callable[[CapturePayload], None]
    """Callback to request capture of content."""

    notify_status: Callable[[str], None]
    """Callback to notify status messages."""

    get_config: Callable[[str], Optional[Any]]
    """Callback to get configuration value by key."""

    def __post_init__(self):
        """Validate callbacks are provided."""
        if not callable(self.request_capture):
            raise ValueError("request_capture must be callable")
        if not callable(self.notify_status):
            raise ValueError("notify_status must be callable")
        if not callable(self.get_config):
            raise ValueError("get_config must be callable")
