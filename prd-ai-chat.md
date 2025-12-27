# AI Chat Application - Product & Technical Requirements Document

**Version:** 1.1  
**Status:** Draft  
**Last Updated:** December 2024

---

## 1. Executive Summary

### 1.1 Purpose
This document defines the product and technical requirements for a Python-based AI chat application that provides a unified interface for interacting with local OpenAI-compatible API models and AWS Bedrock models.

### 1.2 Scope
The application will serve as an internal tool for teams with limited AI options, supporting both local model inference (for users with capable hardware) and cloud-based inference via AWS Bedrock.

### 1.3 Deployment Modes
The application operates in two modes:
- **Standalone Mode:** Independent desktop application with full UI
- **Source Mode:** Embedded as a Source plugin within a host application (ToolHostPane)

### 1.4 Target Users
- **Primary:** Developer/creator for personal use
- **Secondary:** Internal teams with restricted AI access

---

## 2. Product Requirements

### 2.1 Core Functionality

| ID | Requirement | Priority |
|----|-------------|----------|
| PR-001 | Chat with local OpenAI-compatible API models | Must Have |
| PR-002 | Chat with AWS Bedrock models | Must Have |
| PR-003 | TOML-based configuration management | Must Have |
| PR-004 | Model selection via dropdown | Must Have |
| PR-005 | Streaming response support | Must Have |
| PR-006 | Markdown rendering in chat | Must Have |
| PR-007 | Dynamic reasoning/chain-of-thought display | Must Have |
| PR-008 | Copy-to-clipboard for AI responses | Must Have |
| PR-009 | Multi-line chat input | Must Have |
| PR-010 | Image/document paste support | Must Have |
| PR-011 | File attachment support | Should Have |
| PR-012 | Document generation and download | Must Have |
| PR-013 | Source plugin integration for host apps | Must Have |

### 2.2 Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-001 | Application startup time | < 3 seconds |
| NFR-002 | UI responsiveness during streaming | No blocking/freezing |
| NFR-003 | Memory footprint | < 500MB baseline |
| NFR-004 | Cross-platform support | Windows, macOS, Linux |
| NFR-005 | Python version | 3.10+ |

---

## 3. User Interface Specification

### 3.1 Layout Structure

```
┌─────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────┐  │
│  │  Model Dropdown Selector          [▼ Model]  │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │                                               │  │
│  │           Chat Display Window                 │  │
│  │         (Scrollable, Markdown)                │  │
│  │                                               │  │
│  │  ┌─────────────────────────────────────────┐  │  │
│  │  │ AI Response Block        [📄][Copy]     │  │  │
│  │  │ - Rendered Markdown content             │  │  │
│  │  │ - Expandable reasoning section          │  │  │
│  │  └─────────────────────────────────────────┘  │  │
│  │                                               │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │  Chat Input Window                           │  │
│  │  (Multi-line, supports paste & attachments)  │  │
│  │                                    [📎][Send]│  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### 3.2 Component Specifications

#### 3.2.1 Model Dropdown Selector
- **Position:** Top of application window
- **Content:** List of configured models from TOML
- **Display format:** `[Provider] Model Name` (e.g., `[Bedrock] Claude 3.5 Sonnet`)
- **Behavior:** Selection immediately sets active model for next message

#### 3.2.2 Chat Display Window
- **Position:** Center, primary content area
- **Features:**
  - Scrollable conversation history
  - Distinct visual styling for user vs. AI messages
  - Full Markdown rendering (headers, code blocks, lists, tables, etc.)
  - Syntax highlighting for code blocks
  - Streaming text display with visible cursor/indicator
  - Collapsible reasoning/thinking sections for CoT models

#### 3.2.3 AI Response Block
- **Copy Button:** Top-right corner of each AI response
  - Copies raw Markdown content to clipboard
  - Visual feedback on successful copy
- **Document Button (📄):** Adjacent to copy button
  - Opens "Save as Document" dialog
  - See Section 3.3 for document generation details
- **Reasoning Section:** 
  - Collapsed by default
  - Expandable "Show reasoning" toggle
  - Displays `<thinking>` or similar reasoning tokens

#### 3.2.4 Chat Input Window
- **Position:** Bottom of application
- **Height:** 3-5 lines default, expandable
- **Features:**
  - Multi-line text input
  - Paste support for images (PNG, JPG, GIF, WebP)
  - Paste support for documents (PDF, TXT, MD)
  - File attachment button with file picker
  - Send button (also responds to Ctrl/Cmd + Enter)
  - Attachment preview thumbnails

### 3.3 Document Generation & Download

#### 3.3.1 Trigger Methods
1. **Per-Response:** Click 📄 button on any AI response to save that response as a document
2. **Via Prompt:** User asks model to create a document (e.g., "summarize in bullets and put into a document")
3. **Export Conversation:** Menu option to export full conversation as markdown

#### 3.3.2 Document Detection
The application detects when the AI intends to create a downloadable document by:
- Explicit markers in response: `<!-- DOCUMENT: filename.md -->` or fenced block with `download` attribute
- User request patterns: "create a document", "put into a file", "make this downloadable"
- Model-generated structured output with document intent

#### 3.3.3 Document Output Format

```markdown
<!-- DOCUMENT: summary-notes.md -->
# Summary Notes

- Point one
- Point two
- Point three
```

#### 3.3.4 Download Flow
1. Document content detected or 📄 button clicked
2. Preview dialog shows rendered markdown
3. User can:
   - **Download:** Save as `.md` file via system file picker
   - **Copy:** Copy raw markdown to clipboard
   - **Capture (Source Mode):** Send as CapturePayload to host application
4. Default filename derived from first heading or timestamp

#### 3.3.5 UI for Document Download

```
┌─────────────────────────────────────────────────────┐
│  📄 Save Document                            [X]    │
├─────────────────────────────────────────────────────┤
│  Filename: [summary-notes.md            ]           │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │  # Summary Notes                              │  │
│  │                                               │  │
│  │  - Point one                                  │  │
│  │  - Point two                                  │  │
│  │  - Point three                                │  │
│  │                                               │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  [Copy to Clipboard]  [Capture ▼]  [Download]       │
└─────────────────────────────────────────────────────┘
```

Note: "Capture" button only visible in Source Mode.

---

## 4. Source Plugin Architecture

### 4.1 Overview

The AI Chat application can operate as a **Source** within a host application's `ToolHostPane`. This enables the chat functionality to be embedded alongside other tools while providing a standardized capture mechanism.

Key architectural patterns:
- **Protocol-based interface:** Sources implement the `Source` protocol (not ABC) for duck-typing compatibility
- **Context injection:** Host provides a `SourceContext` with callbacks when creating the widget
- **Lazy widget creation:** `create_widget()` is called only when the Source is first activated
- **Entry point discovery:** Sources are registered via `pyproject.toml` entry points and discovered at runtime

### 4.2 Source Contracts (from Host Specification)

The following contracts are defined by the host application and must be implemented exactly as specified.

```python
from typing import Protocol, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QIcon


# =============================================================================
# Enums
# =============================================================================

class SourceType(Enum):
    """Type of source for provenance tracking."""
    WEB = "web"
    PRIVATE_CHAT = "private_chat"
    RAG = "rag"
    TOOL = "tool"
    FILE = "file"


class FormatHint(Enum):
    """Hint for how content should be interpreted."""
    MARKDOWN = "markdown"
    PLAIN = "plain"
    HTML = "html"


# =============================================================================
# Data Contracts
# =============================================================================

@dataclass
class Attachment:
    """File attachment included with a capture."""
    filename: str
    mime_type: str
    data: bytes


@dataclass
class Provenance:
    """Metadata about the origin of captured content."""
    source_id: str
    source_type: SourceType
    timestamp: datetime
    title: Optional[str] = None
    url: Optional[str] = None
    model: Optional[str] = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class CapturePayload:
    """Standard contract for content captured from a Source."""
    content: str
    provenance: Provenance
    format_hint: FormatHint = FormatHint.MARKDOWN
    attachments: list[Attachment] = field(default_factory=list)


@dataclass
class SourceCapabilities:
    """Declares what capture modes a Source supports."""
    supports_selection: bool = False      # Can capture highlighted/selected text
    supports_full_capture: bool = False   # Can capture full content
    supports_built_in_viewer: bool = False  # Has internal viewer (browser sources)


@dataclass
class SourceContext:
    """
    Context provided by the host when creating a Source widget.
    Sources use these callbacks to communicate with the host.
    """
    request_capture: Callable[[CapturePayload], None]  # Send capture to host
    notify_status: Callable[[str], None]               # Update status bar
    get_config: Callable[[str], Any]                   # Read host config values


# =============================================================================
# Source Protocol
# =============================================================================

class Source(Protocol):
    """
    Protocol defining the interface all Sources must implement.
    Sources are discovered via entry points and instantiated by the host.
    """
    
    @property
    def source_id(self) -> str:
        """Unique identifier (e.g., 'ai_chat'). Used in provenance."""
        ...
    
    @property
    def display_name(self) -> str:
        """Human-readable name shown in source selector dropdown."""
        ...
    
    @property
    def icon(self) -> QIcon:
        """Icon displayed in source selector and tabs."""
        ...
    
    @property
    def capabilities(self) -> SourceCapabilities:
        """Declares supported capture modes."""
        ...
    
    def create_widget(self, context: SourceContext) -> QWidget:
        """
        Create and return the Source's main widget.
        Called once when the Source is first activated.
        The context provides callbacks for host communication.
        """
        ...
    
    def get_selection(self) -> Optional[CapturePayload]:
        """
        Return currently selected/highlighted content.
        Returns None if nothing is selected or selection not supported.
        """
        ...
    
    def get_full_capture(self) -> Optional[CapturePayload]:
        """
        Return full capturable content (e.g., last AI response).
        Returns None if nothing is available to capture.
        """
        ...
    
    def shutdown(self) -> None:
        """
        Clean up resources when Source is being removed.
        Called by host during application shutdown or source unload.
        """
        ...
```

### 4.3 AI Chat Source Implementation

```python
from typing import Optional
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QIcon

from .contracts import (
    Source, SourceContext, SourceCapabilities, CapturePayload,
    Provenance, SourceType, FormatHint, Attachment
)
from .ui.chat_widget import AIChatWidget
from .config.loader import load_config


class AIChatSource:
    """
    AI Chat as a Source plugin.
    Implements the Source protocol for integration with ToolHostPane.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self._config_path = config_path
        self._widget: Optional[AIChatWidget] = None
        self._context: Optional[SourceContext] = None
    
    @property
    def source_id(self) -> str:
        return "ai_chat"
    
    @property
    def display_name(self) -> str:
        return "AI Chat"
    
    @property
    def icon(self) -> QIcon:
        # Load from bundled resources or return default
        icon_path = Path(__file__).parent / "resources" / "chat_icon.png"
        if icon_path.exists():
            return QIcon(str(icon_path))
        return QIcon.fromTheme("chat", QIcon())
    
    @property
    def capabilities(self) -> SourceCapabilities:
        return SourceCapabilities(
            supports_selection=True,       # Can capture selected text in response
            supports_full_capture=True,    # Can capture last AI response
            supports_built_in_viewer=False # Not a browser-based source
        )
    
    def create_widget(self, context: SourceContext) -> QWidget:
        """
        Create the chat widget with host context.
        The context provides callbacks for capture and status updates.
        """
        self._context = context
        
        # Check for config override from host
        config_path = self._config_path or context.get_config("ai_chat.config_path")
        
        self._widget = AIChatWidget(
            config_path=config_path,
            source_mode=True,
            on_capture_request=self._handle_capture_request,
            on_status_update=context.notify_status
        )
        
        return self._widget
    
    def get_selection(self) -> Optional[CapturePayload]:
        """Return currently selected/highlighted text in the chat."""
        if not self._widget:
            return None
        
        selection = self._widget.get_selected_text()
        if not selection:
            return None
        
        return CapturePayload(
            content=selection,
            provenance=self._create_provenance(title="Selected text"),
            format_hint=FormatHint.MARKDOWN,
            attachments=[]
        )
    
    def get_full_capture(self) -> Optional[CapturePayload]:
        """Return the last AI response as a capture."""
        if not self._widget:
            return None
        
        response = self._widget.get_last_response()
        if not response:
            return None
        
        # Build attachments if response included generated documents
        attachments = []
        if response.document:
            attachments.append(Attachment(
                filename=response.document.filename,
                mime_type="text/markdown",
                data=response.document.content.encode("utf-8")
            ))
        
        return CapturePayload(
            content=response.markdown,
            provenance=self._create_provenance(
                title=response.title or "AI Response",
                model=response.model_name
            ),
            format_hint=FormatHint.MARKDOWN,
            attachments=attachments
        )
    
    def shutdown(self) -> None:
        """Clean up resources."""
        if self._widget:
            # Cancel any pending requests
            self._widget.cancel_pending()
            # Clear conversation state
            self._widget.clear()
            self._widget = None
        self._context = None
    
    def _create_provenance(
        self,
        title: Optional[str] = None,
        model: Optional[str] = None
    ) -> Provenance:
        """Helper to create Provenance with common fields."""
        return Provenance(
            source_id=self.source_id,
            source_type=SourceType.PRIVATE_CHAT,
            timestamp=datetime.now(),
            title=title,
            url=None,  # Chat doesn't have URLs
            model=model or (self._widget.current_model_name if self._widget else None),
            extra={
                "conversation_length": self._widget.message_count if self._widget else 0
            }
        )
    
    def _handle_capture_request(self, payload: CapturePayload) -> None:
        """
        Called when user clicks Capture button in the widget.
        Forwards to host via context callback.
        """
        if self._context:
            self._context.request_capture(payload)
```

### 4.4 Entry Point Registration

Sources are discovered by the host application via Python entry points. Register the AI Chat source in `pyproject.toml`:

```toml
[project.entry-points."myapp.sources"]
ai_chat = "ai_chat.source:AIChatSource"
```

The host discovers and loads sources at startup:

```python
# Host discovery (for reference)
from importlib.metadata import entry_points

def discover_sources() -> dict[str, type]:
    """Discover all registered Source plugins."""
    sources = {}
    eps = entry_points(group="myapp.sources")
    for ep in eps:
        source_class = ep.load()
        sources[ep.name] = source_class
    return sources
```

### 4.5 Widget Implementation for Dual-Mode Operation

The `AIChatWidget` adapts its behavior based on operating mode:

```python
from typing import Optional, Callable
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal

class AIChatWidget(QWidget):
    """
    Main chat widget supporting standalone and source modes.
    
    In standalone mode: Full application with menubar, title, etc.
    In source mode: Embedded widget with capture callbacks.
    """
    
    # Signal for standalone mode document downloads
    document_ready = pyqtSignal(object)  # GeneratedDocument
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        source_mode: bool = False,
        on_capture_request: Optional[Callable[[CapturePayload], None]] = None,
        on_status_update: Optional[Callable[[str], None]] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        
        self.source_mode = source_mode
        self._on_capture_request = on_capture_request
        self._on_status_update = on_status_update
        
        self._setup_ui()
        self._load_config(config_path)
    
    def _setup_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        
        # Common components
        self.model_selector = ModelSelector()
        self.chat_display = ChatDisplay()
        self.input_widget = InputWidget()
        
        layout.addWidget(self.model_selector)
        layout.addWidget(self.chat_display, stretch=1)
        layout.addWidget(self.input_widget)
        
        # Mode-specific setup
        if self.source_mode:
            self._enable_capture_mode()
    
    def _enable_capture_mode(self):
        """Configure widget for Source mode operation."""
        # Enable capture buttons on response blocks
        self.chat_display.set_capture_enabled(True)
        self.chat_display.capture_clicked.connect(self._handle_capture_click)
        
        # Document dialog shows "Capture" instead of just "Download"
        self.chat_display.set_capture_button_visible(True)
    
    def _handle_capture_click(self, response_content: str, document: Optional[GeneratedDocument]):
        """Handle capture button click on a response."""
        if self._on_capture_request:
            payload = CapturePayload(
                content=response_content,
                provenance=Provenance(
                    source_id="ai_chat",
                    source_type=SourceType.PRIVATE_CHAT,
                    timestamp=datetime.now(),
                    title=document.title if document else "AI Response",
                    model=self.current_model_name
                ),
                format_hint=FormatHint.MARKDOWN,
                attachments=[]
            )
            self._on_capture_request(payload)
    
    def _update_status(self, message: str):
        """Update status in host or standalone status bar."""
        if self._on_status_update:
            self._on_status_update(message)
    
    # --- Public API for Source ---
    
    @property
    def current_model_name(self) -> Optional[str]:
        """Return name of currently selected model."""
        return self.model_selector.current_model_name
    
    @property
    def message_count(self) -> int:
        """Return number of messages in conversation."""
        return self.chat_display.message_count
    
    def get_selected_text(self) -> Optional[str]:
        """Return currently highlighted text, if any."""
        return self.chat_display.get_selection_text()
    
    def get_last_response(self) -> Optional[ResponseContent]:
        """Return the last AI response content."""
        return self.chat_display.get_last_ai_response()
    
    def cancel_pending(self):
        """Cancel any in-flight requests."""
        self.chat_service.cancel()
    
    def clear(self):
        """Clear conversation history."""
        self.chat_display.clear()
```

### 4.6 Host Integration Example

```python
# In host application - for reference only
from importlib.metadata import entry_points
from PyQt6.QtWidgets import QWidget, QStackedWidget, QComboBox, QVBoxLayout

from .contracts import Source, SourceContext, CapturePayload


class ToolHostPane(QWidget):
    """Host panel that manages Source plugins."""
    
    def __init__(self):
        super().__init__()
        self.source_stack = QStackedWidget()
        self.source_selector = QComboBox()
        self.sources: dict[str, Source] = {}
        self._source_widgets: dict[str, QWidget] = {}
        
        self._setup_ui()
        self._discover_and_register_sources()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(self.source_selector)
        layout.addWidget(self.source_stack, stretch=1)
        
        self.source_selector.currentIndexChanged.connect(self._on_source_changed)
    
    def _discover_and_register_sources(self):
        """Load all registered Source plugins via entry points."""
        eps = entry_points(group="myapp.sources")
        for ep in eps:
            source_class = ep.load()
            source = source_class()
            self._register_source(source)
    
    def _register_source(self, source: Source):
        """Register a Source and add to selector."""
        self.sources[source.source_id] = source
        self.source_selector.addItem(
            source.icon,
            source.display_name,
            source.source_id
        )
    
    def _on_source_changed(self, index: int):
        """Switch to selected source, creating widget if needed."""
        source_id = self.source_selector.itemData(index)
        
        if source_id not in self._source_widgets:
            # First activation - create widget with context
            source = self.sources[source_id]
            context = SourceContext(
                request_capture=self._handle_capture,
                notify_status=self._update_status,
                get_config=self._get_config
            )
            widget = source.create_widget(context)
            self._source_widgets[source_id] = widget
            self.source_stack.addWidget(widget)
        
        # Show the source's widget
        widget = self._source_widgets[source_id]
        self.source_stack.setCurrentWidget(widget)
    
    def _handle_capture(self, payload: CapturePayload):
        """
        Handle capture request from Source.
        Host decides how to promote the payload.
        """
        # Example: Insert into active note with provenance
        self.active_note.insert_content(
            payload.content,
            format_hint=payload.format_hint,
            provenance=payload.provenance,
            attachments=payload.attachments
        )
        self._update_status(f"Captured from {payload.provenance.source_id}")
    
    def _update_status(self, message: str):
        """Update host status bar."""
        self.status_bar.showMessage(message, timeout=3000)
    
    def _get_config(self, key: str):
        """Return host configuration value."""
        return self.config.get(key)
    
    def shutdown(self):
        """Clean shutdown of all sources."""
        for source in self.sources.values():
            source.shutdown()
```

### 4.7 Capture Flow Diagram

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   AIChatWidget  │     │   AIChatSource   │     │   ToolHostPane  │
│                 │     │                  │     │   (Host)        │
└────────┬────────┘     └────────┬─────────┘     └────────┬────────┘
         │                       │                        │
         │                       │   create_widget(ctx)   │
         │                       │<───────────────────────│
         │                       │                        │
         │   AIChatWidget(...)   │                        │
         │<──────────────────────│                        │
         │                       │                        │
         │   widget instance     │                        │
         │──────────────────────>│                        │
         │                       │                        │
         │                       │   QWidget              │
         │                       │───────────────────────>│
         │                       │                        │
         │                       │                        │
    ─ ─ ─│─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│─ ─ ─ ─
         │  User clicks          │                        │
         │  "Capture" button     │                        │
         │                       │                        │
         │  _on_capture_request  │                        │
         │  callback(payload)    │                        │
         │──────────────────────>│                        │
         │                       │                        │
         │                       │  context.request_      │
         │                       │  capture(payload)      │
         │                       │───────────────────────>│
         │                       │                        │
         │                       │                        │ Host promotes
         │                       │                        │ payload to note
         │                       │                        │
    ─ ─ ─│─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│─ ─ ─ ─
         │                       │                        │
         │                       │  Host requests capture │
         │                       │  via get_full_capture  │
         │                       │<───────────────────────│
         │                       │                        │
         │  get_last_response()  │                        │
         │<──────────────────────│                        │
         │                       │                        │
         │  ResponseContent      │                        │
         │──────────────────────>│                        │
         │                       │                        │
         │                       │  CapturePayload        │
         │                       │───────────────────────>│
         │                       │                        │
```

---

## 5. Technical Architecture

### 5.1 Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Language | Python 3.10+ | Team familiarity, ecosystem |
| UI Framework | PyQt6 | Cross-platform, native look, rich widgets |
| HTTP Client | httpx | Async support, streaming |
| AWS SDK | boto3 | Official AWS SDK |
| Config Parser | tomllib / tomli | TOML support |
| Markdown | markdown + pygments | Rendering + syntax highlighting |

### 5.2 Application Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Presentation Layer                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ MainWindow  │  │ ChatDisplay │  │ InputWidget         │  │
│  │ (standalone)│  │             │  │                     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│         │                                                    │
│  ┌──────┴──────────────────────────────────────────────┐    │
│  │ AIChatWidget (core widget, used in both modes)      │    │
│  └─────────────────────────────────────────────────────┘    │
│         │                                                    │
│  ┌──────┴──────────────────────────────────────────────┐    │
│  │ AIChatSource (Source interface wrapper)             │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │ ChatService     │  │ ConfigService   │  │ DocService  │  │
│  │ - send_message  │  │ - load_config   │  │ - generate  │  │
│  │ - stream_resp   │  │ - get_models    │  │ - export    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Provider Layer                          │
│  ┌─────────────────┐  ┌─────────────────────────────────┐   │
│  │ BedrockProvider │  │ OpenAICompatibleProvider        │   │
│  │ - invoke_model  │  │ - LMStudio / llama.cpp / Ollama │   │
│  │ - stream        │  │ - chat_completions              │   │
│  └─────────────────┘  └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 Directory Structure

```
ai-chat-app/
├── src/
│   ├── ai_chat/
│   │   ├── __init__.py
│   │   ├── main.py                 # Standalone entry point
│   │   ├── source.py               # AIChatSource implementation
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   ├── loader.py           # TOML configuration loader
│   │   │   └── models.py           # Pydantic config models
│   │   ├── providers/
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # Abstract provider interface
│   │   │   ├── bedrock.py          # AWS Bedrock implementation
│   │   │   └── openai_compatible.py # Local model implementation
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── chat.py             # Chat orchestration service
│   │   │   └── document.py         # Document generation service
│   │   ├── ui/
│   │   │   ├── __init__.py
│   │   │   ├── main_window.py      # Standalone main window
│   │   │   ├── chat_widget.py      # Core chat widget (both modes)
│   │   │   ├── chat_display.py     # Chat message display widget
│   │   │   ├── input_widget.py     # Chat input with attachments
│   │   │   ├── model_selector.py   # Dropdown component
│   │   │   ├── document_dialog.py  # Document preview/save dialog
│   │   │   └── styles.py           # Qt stylesheets
│   │   ├── contracts/
│   │   │   ├── __init__.py         # Re-exports all contracts
│   │   │   ├── source.py           # Source protocol (from host spec)
│   │   │   ├── capture.py          # CapturePayload, Provenance, etc.
│   │   │   └── context.py          # SourceContext, SourceCapabilities
│   │   ├── resources/
│   │   │   ├── chat_icon.png       # Source icon for selector
│   │   │   └── icons/              # Additional UI icons
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── clipboard.py        # Clipboard operations
│   │       └── markdown.py         # Markdown rendering utilities
├── config/
│   └── models.toml                 # Default configuration file
├── tests/
│   ├── __init__.py
│   ├── test_source.py              # Source interface tests
│   ├── test_providers.py           # Provider tests
│   └── test_chat_widget.py         # UI tests
├── requirements.txt
├── pyproject.toml                  # Includes entry point registration
└── README.md
```

---

## 6. Configuration Specification

### 6.1 Configuration File Location

The application searches for configuration in this order:
1. `./config/models.toml` (application directory)
2. `~/.config/ai-chat/models.toml` (user config directory)
3. Custom path via `--config` CLI argument
4. Passed programmatically when instantiated as Source

### 6.2 TOML Schema

```toml
# models.toml - AI Chat Application Configuration

[app]
title = "AI Chat"
theme = "dark"                    # "dark" | "light" | "system"
default_model = "bedrock-claude"  # Must match a model key below

[documents]
default_directory = "~/Documents/AI-Exports"
filename_template = "{title}_{timestamp}.md"
include_metadata = true           # Include provenance in exported docs

# =============================================================================
# AWS Bedrock Models
# =============================================================================
[models.bedrock-claude]
provider = "bedrock"
name = "Claude 3.5 Sonnet"
model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"
region = "us-east-1"              # Optional, defaults to AWS CLI config
supports_images = true
supports_documents = true
supports_reasoning = false
max_tokens = 8192
temperature = 0.7

[models.bedrock-claude-thinking]
provider = "bedrock"
name = "Claude 3.5 Sonnet (Extended Thinking)"
model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"
region = "us-east-1"
supports_images = true
supports_documents = true
supports_reasoning = true
reasoning_budget_tokens = 10000
max_tokens = 8192

[models.bedrock-nova]
provider = "bedrock"
name = "Amazon Nova Pro"
model_id = "amazon.nova-pro-v1:0"
region = "us-east-1"
supports_images = true
supports_documents = false
supports_reasoning = false
max_tokens = 4096

# =============================================================================
# Local OpenAI-Compatible Models
# =============================================================================
[models.local-llama]
provider = "openai_compatible"
name = "Llama 3.2 (Local)"
base_url = "http://localhost:1234/v1"   # LM Studio default
model = "llama-3.2-8b"
api_key = "lm-studio"                    # Often ignored by local servers
supports_images = false
supports_documents = false
supports_reasoning = false
max_tokens = 4096
temperature = 0.7

[models.ollama-mistral]
provider = "openai_compatible"
name = "Mistral (Ollama)"
base_url = "http://localhost:11434/v1"  # Ollama OpenAI-compatible endpoint
model = "mistral"
api_key = "ollama"
supports_images = false
supports_documents = false
supports_reasoning = false
max_tokens = 4096

[models.local-qwen-coder]
provider = "openai_compatible"
name = "Qwen 2.5 Coder (llama.cpp)"
base_url = "http://localhost:8080/v1"   # llama.cpp server default
model = "qwen2.5-coder-32b"
api_key = "not-needed"
supports_images = false
supports_documents = false
supports_reasoning = true
max_tokens = 8192

[models.local-vision]
provider = "openai_compatible"
name = "LLaVA Vision (Local)"
base_url = "http://localhost:1234/v1"
model = "llava-v1.6"
api_key = "lm-studio"
supports_images = true
supports_documents = false
supports_reasoning = false
max_tokens = 4096
```

### 6.3 Configuration Model (Pydantic)

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional
from enum import Enum

class ProviderType(str, Enum):
    BEDROCK = "bedrock"
    OPENAI_COMPATIBLE = "openai_compatible"

class ModelConfig(BaseModel):
    provider: ProviderType
    name: str
    supports_images: bool = False
    supports_documents: bool = False
    supports_reasoning: bool = False
    max_tokens: int = 4096
    temperature: float = 0.7
    
    # Bedrock-specific
    model_id: Optional[str] = None
    region: Optional[str] = None
    reasoning_budget_tokens: Optional[int] = None
    
    # OpenAI-compatible specific
    base_url: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None

class DocumentConfig(BaseModel):
    default_directory: str = "~/Documents/AI-Exports"
    filename_template: str = "{title}_{timestamp}.md"
    include_metadata: bool = True

class AppConfig(BaseModel):
    title: str = "AI Chat"
    theme: Literal["dark", "light", "system"] = "system"
    default_model: str

class Config(BaseModel):
    app: AppConfig
    documents: DocumentConfig = DocumentConfig()
    models: dict[str, ModelConfig]
```

---

## 7. Provider Specifications

### 7.1 Abstract Provider Interface

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional, Literal
from dataclasses import dataclass, field

@dataclass
class Message:
    role: Literal["user", "assistant"]
    content: str
    images: list[bytes] = field(default_factory=list)
    documents: list[tuple[str, bytes]] = field(default_factory=list)

@dataclass
class StreamChunk:
    content: str = ""
    reasoning: str = ""
    is_reasoning: bool = False
    done: bool = False

class BaseProvider(ABC):
    @abstractmethod
    async def stream_chat(
        self,
        messages: list[Message],
        max_tokens: int,
        temperature: float
    ) -> AsyncIterator[StreamChunk]:
        """Stream chat completion response."""
        pass
    
    @abstractmethod
    def supports_feature(self, feature: str) -> bool:
        """Check if provider/model supports a feature."""
        pass
```

### 7.2 AWS Bedrock Provider

**Authentication:** Uses boto3 default credential chain (AWS CLI, environment variables, IAM roles)

**API:** Bedrock Runtime `converse_stream` API

**Key Implementation Details:**
- Use `bedrock-runtime` client
- Handle `contentBlockDelta` events for streaming
- Parse `reasoningContent` blocks for thinking models
- Convert images to base64 for `image` content blocks
- Convert documents to base64 for `document` content blocks

### 7.3 OpenAI-Compatible Provider

**Authentication:** API key in header (often ignored by local servers)

**API:** `/v1/chat/completions` with `stream=true`

**Compatibility Targets:**

| Server | Default Port | Notes |
|--------|--------------|-------|
| LM Studio | 1234 | Full OpenAI compatibility |
| Ollama | 11434 | Use `/v1` endpoint prefix |
| llama.cpp | 8080 | Via `--api-server` flag |

**Key Implementation Details:**
- Use `httpx.AsyncClient` for streaming
- Parse Server-Sent Events (SSE) format
- Handle `<think>` or `<reasoning>` tags for CoT models
- Convert images to base64 data URLs for vision models

---

## 8. Document Generation Service

### 8.1 Service Interface

```python
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from typing import Optional

@dataclass
class GeneratedDocument:
    filename: str
    content: str
    title: str
    created_at: datetime
    model: str
    
class DocumentService:
    def __init__(self, config: DocumentConfig):
        self.config = config
    
    def extract_document(self, response: str) -> Optional[GeneratedDocument]:
        """
        Extract document from AI response if document markers present.
        Returns None if no document detected.
        """
        pass
    
    def create_document(
        self,
        content: str,
        title: Optional[str] = None,
        model: str = "unknown"
    ) -> GeneratedDocument:
        """Create a document from arbitrary content."""
        pass
    
    def save_document(
        self,
        doc: GeneratedDocument,
        path: Optional[Path] = None
    ) -> Path:
        """Save document to filesystem. Returns saved path."""
        pass
    
    def to_capture_payload(
        self,
        doc: GeneratedDocument,
        source_id: str
    ) -> CapturePayload:
        """Convert document to CapturePayload for Source mode."""
        pass
```

### 8.2 Document Detection Patterns

```python
import re

DOCUMENT_PATTERNS = [
    # Explicit marker: <!-- DOCUMENT: filename.md -->
    re.compile(r'<!--\s*DOCUMENT:\s*(?P<filename>[\w\-\.]+)\s*-->'),
    
    # Fenced block with download attribute
    re.compile(r'```(?P<lang>\w+)?\s*download(?:=(?P<filename>[\w\-\.]+))?'),
    
    # Natural language triggers (for prompting model)
    re.compile(r'(?:here is|I\'ve created|the document is ready)', re.IGNORECASE),
]

def detect_document_intent(response: str) -> bool:
    """Check if response contains document creation intent."""
    return any(p.search(response) for p in DOCUMENT_PATTERNS)
```

### 8.3 Export Formats

| Format | Extension | Content |
|--------|-----------|---------|
| Markdown | `.md` | Raw markdown with optional YAML frontmatter |
| Plain Text | `.txt` | Stripped markdown, plain text only |
| HTML | `.html` | Rendered markdown as standalone HTML |

### 8.4 Metadata Frontmatter (Optional)

When `include_metadata = true` in config:

```markdown
---
title: Summary Notes
created: 2024-12-26T14:30:00Z
model: Claude 3.5 Sonnet
source: ai_chat
---

# Summary Notes

- Point one
- Point two
```

---

## 9. Streaming & Reasoning Support

### 9.1 Streaming Implementation

```python
async def handle_stream(self, provider: BaseProvider, messages: list[Message]):
    response_content = ""
    reasoning_content = ""
    
    async for chunk in provider.stream_chat(messages, max_tokens, temperature):
        if chunk.is_reasoning:
            reasoning_content += chunk.reasoning
            self.ui.update_reasoning(reasoning_content)
        else:
            response_content += chunk.content
            self.ui.update_response(response_content)
        
        if chunk.done:
            self.ui.finalize_response(response_content, reasoning_content)
            self._check_document_intent(response_content)
```

### 9.2 Reasoning Detection Patterns

| Model Type | Reasoning Format | Detection Method |
|------------|------------------|------------------|
| Claude (Bedrock) | `reasoningContent` block | API response structure |
| DeepSeek R1 | `<think>...</think>` | Tag parsing |
| QwQ / Qwen | `<reasoning>...</reasoning>` | Tag parsing |
| Custom | Configurable pattern | Regex from config |

### 9.3 UI Reasoning Display

- Reasoning section collapsed by default
- Toggle button: "▶ Show reasoning (X tokens)"
- Distinct styling (muted color, smaller font)
- Does not count toward copy content unless expanded

---

## 10. File & Image Handling

### 10.1 Supported Formats

| Type | Formats | Max Size | Notes |
|------|---------|----------|-------|
| Images | PNG, JPG, GIF, WebP | 10MB | Converted to base64 |
| Documents | PDF, TXT, MD, DOCX | 25MB | Extracted text or base64 |

### 10.2 Attachment Flow

1. User pastes image/document OR clicks attachment button
2. Application validates format and size
3. Thumbnail/preview displayed in input area
4. On send, content encoded based on provider requirements
5. If model doesn't support type, show warning and exclude

### 10.3 Capability Gating

```python
def validate_attachments(self, model_config: ModelConfig, attachments: list):
    errors = []
    for att in attachments:
        if att.is_image and not model_config.supports_images:
            errors.append(f"Model does not support images: {att.name}")
        if att.is_document and not model_config.supports_documents:
            errors.append(f"Model does not support documents: {att.name}")
    return errors
```

---

## 11. Error Handling

### 11.1 Error Categories

| Category | Examples | User Message |
|----------|----------|--------------|
| Configuration | Missing TOML, invalid schema | "Configuration error: {details}. Please check models.toml" |
| Connection | Server unreachable, timeout | "Cannot connect to {model}. Is the server running?" |
| Authentication | AWS credentials, API key | "Authentication failed for {provider}. Check credentials." |
| Rate Limit | Bedrock throttling | "Rate limited. Please wait and try again." |
| Model Error | Context length, unsupported | "Model error: {details}" |

### 11.2 Graceful Degradation

- If a configured model is unreachable at startup, mark as "unavailable" in dropdown
- Allow switching models mid-conversation
- Preserve conversation history on errors

---

## 12. Build & Distribution

### 12.1 Dependencies

```
# requirements.txt
PyQt6>=6.6.0
httpx>=0.27.0
boto3>=1.34.0
pydantic>=2.5.0
markdown>=3.5.0
pygments>=2.17.0
tomli>=2.0.0;python_version<"3.11"
qasync>=0.24.0                    # Qt + asyncio integration
```

### 12.2 pyproject.toml

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "ai-chat"
version = "1.0.0"
description = "Chat interface for local and AWS Bedrock AI models"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "PyQt6>=6.6.0",
    "httpx>=0.27.0",
    "boto3>=1.34.0",
    "pydantic>=2.5.0",
    "markdown>=3.5.0",
    "pygments>=2.17.0",
    "tomli>=2.0.0;python_version<'3.11'",
    "qasync>=0.24.0",
]

[project.scripts]
ai-chat = "ai_chat.main:main"

[project.entry-points."myapp.sources"]
ai_chat = "ai_chat.source:AIChatSource"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
ai_chat = ["resources/*", "resources/icons/*"]
```

### 12.3 Packaging

| Platform | Method | Output |
|----------|--------|--------|
| All | pip install | `ai-chat` CLI command |
| All | pip install | `ai_chat` importable package |
| Windows | PyInstaller | `.exe` installer |
| macOS | PyInstaller | `.app` bundle |
| Linux | PyInstaller | AppImage |

### 12.4 CLI Interface

```bash
# Run standalone with default config
ai-chat

# Run with custom config
ai-chat --config /path/to/models.toml

# Validate configuration
ai-chat --validate-config
```

### 12.5 Programmatic Usage (Source Mode)

```python
from ai_chat import AIChatSource
from ai_chat.contracts import SourceContext, CapturePayload

# Create source instance (optionally with custom config path)
source = AIChatSource(config_path="/path/to/models.toml")

# Create context with host callbacks
context = SourceContext(
    request_capture=lambda payload: print(f"Captured: {payload.content[:50]}..."),
    notify_status=lambda msg: print(f"Status: {msg}"),
    get_config=lambda key: None
)

# Create widget (call once, when source is first activated)
chat_widget = source.create_widget(context)

# Add to your layout
my_layout.addWidget(chat_widget)

# Later: Get current selection or last response
selection = source.get_selection()        # Selected text, if any
full_capture = source.get_full_capture()  # Last AI response

# On shutdown
source.shutdown()
```

---

## 13. Future Considerations

The following features are out of scope for v1.0 but may be considered for future releases:

- **Conversation persistence** - Save/load chat history to disk
- **System prompts** - Per-model system prompt configuration
- **Prompt templates** - Quick-insert prompt snippets
- **Token counting** - Display token usage per message
- **Multi-chat tabs** - Multiple concurrent conversations
- **Plugin system** - Extensible provider support
- **Export to PDF** - Direct PDF export with styling

---

## 14. Appendix

### A. Keyboard Shortcuts (v1.0)

| Action | Shortcut |
|--------|----------|
| Send message | `Ctrl/Cmd + Enter` |
| Copy last response | `Ctrl/Cmd + Shift + C` |
| Focus input | `Ctrl/Cmd + L` |
| Clear conversation | `Ctrl/Cmd + Shift + K` |
| Save as document | `Ctrl/Cmd + S` (when response selected) |

### B. Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `AI_CHAT_CONFIG` | Config file path | `./config/models.toml` |
| `AWS_PROFILE` | AWS credential profile | `default` |
| `AWS_REGION` | Default AWS region | From AWS config |

### C. Source Contracts Quick Reference

```python
# Enums
class SourceType(Enum):
    WEB = "web"
    PRIVATE_CHAT = "private_chat"
    RAG = "rag"
    TOOL = "tool"
    FILE = "file"

class FormatHint(Enum):
    MARKDOWN = "markdown"
    PLAIN = "plain"
    HTML = "html"

# Data contracts
@dataclass
class Attachment:
    filename: str
    mime_type: str
    data: bytes

@dataclass
class Provenance:
    source_id: str                    # "ai_chat"
    source_type: SourceType           # SourceType.PRIVATE_CHAT
    timestamp: datetime               # When captured
    title: Optional[str] = None       # Document/response title
    url: Optional[str] = None         # Not used for chat
    model: Optional[str] = None       # Model name used
    extra: dict[str, Any] = {}        # Additional metadata

@dataclass
class CapturePayload:
    content: str                      # Markdown or plain text
    provenance: Provenance            # Source metadata
    format_hint: FormatHint           # FormatHint.MARKDOWN
    attachments: list[Attachment]     # Optional file attachments

@dataclass
class SourceCapabilities:
    supports_selection: bool          # Can capture highlighted text
    supports_full_capture: bool       # Can capture full content
    supports_built_in_viewer: bool    # Has internal viewer

@dataclass
class SourceContext:
    request_capture: Callable[[CapturePayload], None]
    notify_status: Callable[[str], None]
    get_config: Callable[[str], Any]
```

### D. Glossary

- **CoT (Chain of Thought):** Reasoning steps shown before final answer
- **OpenAI-compatible:** APIs matching OpenAI's `/v1/chat/completions` spec
- **Streaming:** Incremental response delivery as tokens are generated
- **Source:** A plugin interface for embedding tools in a host application
- **CapturePayload:** Standardized data contract for content transfer between Source and host
- **ToolHostPane:** Host application widget that manages Source plugins
