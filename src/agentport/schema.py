from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class ModelProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE_OPENAI = "azure_openai"
    OLLAMA = "ollama"
    LOCAL = "local"


class ModelConfig(BaseModel):
    provider: ModelProvider = Field(description="LLM provider name")
    model: str = Field(description="Model identifier (e.g., gpt-4, claude-3-opus)")
    model_kwargs: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional model configuration parameters"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature"
    )
    max_tokens: Optional[int] = Field(
        default=None,
        description="Maximum tokens to generate"
    )


class ToolType(str, Enum):
    FUNCTION = "function"
    REST_API = "rest_api"
    MCP = "mcp"


class ToolArgument(BaseModel):
    name: str = Field(description="Argument name")
    type: str = Field(description="JSON schema type (string, number, boolean, object, array)")
    description: Optional[str] = Field(default=None, description="Argument description")
    required: bool = Field(default=False, description="Whether argument is required")
    default: Optional[Any] = Field(default=None, description="Default value")
    enum: Optional[list[str]] = Field(default=None, description="Allowed enum values")


class Tool(BaseModel):
    id: Optional[str] = Field(default=None, description="Unique tool identifier")
    name: str = Field(description="Tool name (must be unique within agent)")
    description: str = Field(description="Tool purpose and functionality")
    type: ToolType = Field(default=ToolType.FUNCTION, description="Tool implementation type")
    code: Optional[str] = Field(
        default=None,
        description="Tool implementation code (Python function or JSON for REST)"
    )
    arguments: list[ToolArgument] = Field(
        default_factory=list,
        description="Tool input parameter definitions (JSON Schema)"
    )
    output_schema: Optional[dict[str, Any]] = Field(
        default=None,
        description="Expected output schema definition"
    )
    enabled: bool = Field(default=True, description="Whether tool is active")


class ToolRule(BaseModel):
    rule_type: str = Field(description="Rule type (e.g., 'always', 'never', 'dynamic')")
    tool_name: Optional[str] = Field(default=None, description="Target tool name")
    condition: Optional[str] = Field(
        default=None,
        description="Rule condition expression or description"
    )
    description: Optional[str] = Field(default=None, description="Rule explanation")


class MemoryBlock(BaseModel):
    id: Optional[str] = Field(default=None, description="Unique block identifier")
    label: str = Field(
        description="Block label (e.g., 'human', 'persona', 'system', 'custom')"
    )
    text: str = Field(description="Block content text")
    enabled: bool = Field(default=True, description="Whether block is active in context")
    in_context: bool = Field(
        default=True,
        description="Whether block is included in LLM context window"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional block metadata"
    )


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class Message(BaseModel):
    role: MessageRole = Field(description="Message sender role")
    content: str = Field(description="Message content text")
    tool_call_id: Optional[str] = Field(
        default=None,
        description="Associated tool call identifier"
    )
    tool_name: Optional[str] = Field(
        default=None,
        description="Tool that produced this message (if tool role)"
    )
    timestamp: Optional[datetime] = Field(
        default=None,
        description="Message timestamp"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional message metadata"
    )


class EnvVar(BaseModel):
    name: str = Field(description="Environment variable name")
    value: str = Field(description="Environment variable value")
    description: Optional[str] = Field(default=None, description="Variable description")
    secret: bool = Field(
        default=False,
        description="Whether value is sensitive (should not be logged)"
    )


class AgentMetadata(BaseModel):
    name: str = Field(description="Agent display name")
    description: Optional[str] = Field(default=None, description="Agent description")
    version: str = Field(default="1.0.0", description="Agent version (semver)")
    author: Optional[str] = Field(default=None, description="Agent author")
    tags: list[str] = Field(
        default_factory=list,
        description="Agent categorization tags"
    )
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


class AgentState(BaseModel):
    llm_model_config: ModelConfig = Field(description="LLM configuration")
    system_prompt: str = Field(description="System prompt/instructions")
    tools: list[Tool] = Field(default_factory=list, description="Available tools")
    tool_rules: list[ToolRule] = Field(
        default_factory=list,
        description="Tool usage rules and constraints"
    )
    memory_blocks: list[MemoryBlock] = Field(
        default_factory=list,
        description="Memory/context blocks"
    )
    message_history: list[Message] = Field(
        default_factory=list,
        description="Conversation message history"
    )
    env_vars: list[EnvVar] = Field(
        default_factory=list,
        description="Environment variables for agent execution"
    )


class AgentFile(BaseModel):
    version: str = Field(default="1.0", description="Agent file format version")
    metadata: AgentMetadata = Field(description="Agent metadata")
    state: AgentState = Field(description="Agent runtime state")
    legacy_model_config: Optional[dict[str, Any]] = Field(
        default=None,
        description="Legacy field for backward compatibility"
    )

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        if not v.startswith(("1.", "2.")):
            raise ValueError("Version must be 1.x or 2.x")
        return v
