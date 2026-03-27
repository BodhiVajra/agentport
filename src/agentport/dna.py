from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    """Memory layer types in Agent DNA architecture."""
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    ANNOTATION = "annotation"


class PriorityLevel(str, Enum):
    """Priority levels for memory blocks."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    ARCHIVE = "archive"


class CoreIdentity(BaseModel):
    """Core Identity Layer - the immutable 'soul' of the agent.
    
    Contains the fundamental identity that requires human review to modify.
    """
    name: str = Field(..., description="Agent name")
    description: str = Field(..., description="Agent description")
    author: Optional[str] = Field(None, description="Original author")
    human_vision: str = Field(
        ..., 
        description="Human-defined original intent, e.g., 'code reviewer', 'writing assistant'"
    )
    version: str = Field(default="1.0", description="DNA version")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    locked: bool = Field(default=False, description="Lock to prevent AI self-evolution")


class MemoryBlockDNA(BaseModel):
    """Single memory block with DNA-aware metadata."""
    id: str = Field(..., description="Unique memory block ID")
    memory_type: MemoryType = Field(..., description="Memory layer type")
    content: str = Field(..., description="Memory content")
    priority: PriorityLevel = Field(default=PriorityLevel.MEDIUM)
    tags: list[str] = Field(default_factory=list)
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = None
    access_count: int = Field(default=0)
    compressed: bool = Field(default=False, description="Whether this block is compressed")
    compression_ratio: Optional[float] = Field(None, description="Compression ratio if compressed")


class LayeredMemorySystem(BaseModel):
    """Layered Memory System - the 'evolutionary' memory of the agent.
    
    Four layers:
    - Episodic: Raw conversation history
    - Semantic: Knowledge chunks after classification
    - Procedural: Tools and workflows
    - Annotation: Human-defined tags and priorities
    """
    episodic: list[MemoryBlockDNA] = Field(default_factory=list)
    semantic: list[MemoryBlockDNA] = Field(default_factory=list)
    procedural: list[MemoryBlockDNA] = Field(default_factory=list)
    annotations: list[MemoryBlockDNA] = Field(default_factory=list)
    
    total_tokens_estimate: int = Field(default=0, description="Estimated token count")
    compressed_tokens: int = Field(default=0, description="Tokens after compression")
    
    def get_all_memories(self) -> list[MemoryBlockDNA]:
        """Get all memory blocks across layers."""
        return (
            self.episodic + 
            self.semantic + 
            self.procedural + 
            self.annotations
        )
    
    def get_by_type(self, memory_type: MemoryType) -> list[MemoryBlockDNA]:
        """Get memories by specific type."""
        if memory_type == MemoryType.EPISODIC:
            return self.episodic
        elif memory_type == MemoryType.SEMANTIC:
            return self.semantic
        elif memory_type == MemoryType.PROCEDURAL:
            return self.procedural
        elif memory_type == MemoryType.ANNOTATION:
            return self.annotations
        return []


class ToolDNA(BaseModel):
    """Tool definition with DNA-aware metadata."""
    name: str
    description: str
    type: str = Field(default="function")
    code: Optional[str] = None
    enabled: bool = True
    parameters: dict = Field(default_factory=dict)
    version: str = Field(default="1.0")
    last_used: Optional[datetime] = None
    usage_count: int = 0
    success_rate: float = Field(default=1.0, ge=0.0, le=1.0)


class ToolWorkflowLayer(BaseModel):
    """Tool & Workflow Layer - the 'capabilities' of the agent."""
    tools: list[ToolDNA] = Field(default_factory=list)
    workflows: list[dict] = Field(default_factory=list, description="Predefined workflow sequences")
    tool_rules: list[str] = Field(default_factory=list)
    
    def get_tool(self, name: str) -> Optional[ToolDNA]:
        """Get tool by name."""
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None


class AdapterCapability(BaseModel):
    """Supported framework adapter capability."""
    framework: str
    supported: bool = True
    bidirectional: bool = True
    last_verified: Optional[datetime] = None


class FrameworkAdapterLayer(BaseModel):
    """Framework Adapter Layer - the 'portability' of the agent.
    
    Currently supports Letta (.af) and OpenClaw (.json).
    Future: LangChain, CrewAI, AutoGen, etc.
    """
    supported_formats: list[str] = Field(
        default_factory=lambda: [".af", ".json", ".apf"]
    )
    adapters: list[AdapterCapability] = Field(default_factory=list)
    default_export_format: str = Field(default=".apf")
    
    def add_adapter(self, framework: str, bidirectional: bool = True) -> None:
        """Add a new framework adapter."""
        self.adapters.append(AdapterCapability(
            framework=framework,
            bidirectional=bidirectional,
            last_verified=datetime.now()
        ))


class AgentDNA(BaseModel):
    """Agent DNA - Digital Neural Architecture.
    
    4-layer + 1-engine architecture:
    1. Core Identity Layer (immutable soul)
    2. Layered Memory System (evolutionary memory)
    3. Tool & Workflow Layer (capabilities)
    4. Framework Adapter Layer (portability)
    + Intelligent Memory Engine (compression)
    """
    version: str = Field(default="1.0", description="DNA schema version")
    
    core_identity: CoreIdentity = Field(..., description="Layer 1: Core Identity")
    memory_system: LayeredMemorySystem = Field(..., description="Layer 2: Layered Memory")
    tool_layer: ToolWorkflowLayer = Field(..., description="Layer 3: Tools & Workflows")
    adapter_layer: FrameworkAdapterLayer = Field(..., description="Layer 4: Framework Adapters")
    
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    
    def summary(self) -> str:
        """Get DNA summary."""
        memories = self.memory_system.get_all_memories()
        return (
            f"AgentDNA({self.core_identity.name}): "
            f"{len(memories)} memories, "
            f"{len(self.tool_layer.tools)} tools, "
            f"{len(self.adapter_layer.supported_formats)} formats"
        )


class APFFile(BaseModel):
    """AgentPort File format - universal agent interchange format.
    
    More neutral than .af, like a Docker image for agents.
    """
    version: str = Field(default="1.0")
    dna: AgentDNA
    signature: Optional[str] = Field(None, description="DNA integrity signature")
    created_at: datetime = Field(default_factory=datetime.now)
    source_framework: Optional[str] = None
    
    def to_file(self, path: str) -> None:
        """Save to .apf file."""
        import yaml
        from pathlib import Path
        
        content = self.model_dump(mode="json", exclude_none=True)
        content["created_at"] = content["created_at"].isoformat()
        
        Path(path).write_text(
            yaml.dump(content, allow_unicode=True, default_flow_style=False),
            encoding="utf-8"
        )
    
    @classmethod
    def from_file(cls, path: str) -> APFFile:
        """Load from .apf file."""
        import yaml
        from pathlib import Path
        
        content = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        return cls.model_validate(content)


__all__ = [
    "MemoryType",
    "PriorityLevel",
    "CoreIdentity",
    "MemoryBlockDNA",
    "LayeredMemorySystem",
    "ToolDNA",
    "ToolWorkflowLayer",
    "AdapterCapability",
    "FrameworkAdapterLayer",
    "AgentDNA",
    "APFFile",
]