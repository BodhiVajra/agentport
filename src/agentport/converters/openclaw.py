from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from agentport.core import AgentPort
from agentport.schema import (
    AgentMetadata,
    AgentState,
    EnvVar,
    MemoryBlock,
    Message,
    ModelConfig,
    ModelProvider,
    Tool,
    ToolArgument,
    ToolRule,
)


class OpenClawAgent:
    """OpenClaw agent format representation.
    
    OpenClaw uses a JSON-based state format with:
    - persona: System prompt and agent identity
    - skills: List of skill definitions (equivalent to tools)
    - memory: Agent memory/context
    - settings: Model configuration
    """

    def __init__(
        self,
        persona: str,
        skills: list[dict[str, Any]],
        memory: list[dict[str, Any]],
        settings: dict[str, Any],
        name: Optional[str] = None,
        description: Optional[str] = None,
        version: str = "1.0",
        author: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        self.persona = persona
        self.skills = skills
        self.memory = memory
        self.settings = settings
        self.name = name
        self.description = description
        self.version = version
        self.author = author
        self.metadata = metadata or {}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OpenClawAgent:
        """Create OpenClawAgent from dictionary."""
        return cls(
            persona=data.get("persona", ""),
            skills=data.get("skills", []),
            memory=data.get("memory", []),
            settings=data.get("settings", {}),
            name=data.get("name"),
            description=data.get("description"),
            version=data.get("version", "1.0"),
            author=data.get("author"),
            metadata=data.get("metadata", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "persona": self.persona,
            "skills": self.skills,
            "memory": self.memory,
            "settings": self.settings,
            "version": self.version,
        }
        if self.name:
            result["name"] = self.name
        if self.description:
            result["description"] = self.description
        if self.author:
            result["author"] = self.author
        if self.metadata:
            result["metadata"] = self.metadata
        return result


def from_letta_to_openclaw(agent: AgentPort) -> OpenClawAgent:
    """Convert Letta/AgentPort format to OpenClaw format.

    Args:
        agent: AgentPort instance with Letta .af format data.

    Returns:
        OpenClawAgent instance.

    Mapping:
        - metadata.name -> name
        - metadata.description -> description
        - metadata.author -> author
        - state.system_prompt -> persona
        - state.tools -> skills (transformed)
        - state.memory_blocks -> memory
        - state.llm_model_config -> settings.llm
    """
    tools = list(agent.state.tools) if agent.state.tools else []
    memory_blocks = list(agent.state.memory_blocks) if agent.state.memory_blocks else []
    model_config = agent.state.llm_model_config

    skills = []
    for tool in tools:
        skill = {
            "name": tool.name,
            "description": tool.description,
            "enabled": getattr(tool, "enabled", True),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        }
        
        if hasattr(tool, "arguments") and tool.arguments:
            for arg in tool.arguments:
                prop = {
                    "type": arg.type,
                    "description": arg.description,
                }
                if hasattr(arg, "enum") and arg.enum:
                    prop["enum"] = arg.enum
                skill["parameters"]["properties"] = arg.name
                skill["parameters"]["properties"] = prop
                if arg.required:
                    skill["parameters"]["required"] = arg.name

        if hasattr(tool, "code") and tool.code:
            skill["handler"] = {
                "type": "python",
                "code": tool.code,
            }

        skills.append(skill)

    memory = []
    for block in memory_blocks:
        mem_item = {
            "type": block.label,
            "content": block.text,
            "enabled": block.enabled,
        }
        if hasattr(block, "in_context") and block.in_context:
            mem_item["context"] = True
        memory.append(mem_item)

    settings = {
        "llm": {
            "provider": model_config.provider.value if hasattr(model_config.provider, "value") else str(model_config.provider),
            "model": model_config.model,
            "temperature": model_config.temperature,
            "max_tokens": model_config.max_tokens,
        },
        "model_kwargs": model_config.model_kwargs or {},
    }

    persona = agent.state.system_prompt or ""

    return OpenClawAgent(
        persona=persona,
        skills=skills,
        memory=memory,
        settings=settings,
        name=agent.metadata.name,
        description=agent.metadata.description,
        version=agent.metadata.version or "1.0",
        author=agent.metadata.author,
        metadata={
            "created_at": agent.metadata.created_at.isoformat() if agent.metadata.created_at else datetime.now().isoformat(),
            "tags": list(agent.metadata.tags) if agent.metadata.tags else [],
        },
    )


def from_openclaw_to_letta(
    openclaw_data: dict[str, Any] | OpenClawAgent,
    name: Optional[str] = None,
) -> AgentPort:
    """Convert OpenClaw format to Letta/AgentPort format.

    Args:
        openclaw_data: OpenClaw JSON data or OpenClawAgent instance.
        name: Optional name override.

    Returns:
        AgentPort instance.

    Mapping:
        - name -> metadata.name
        - description -> metadata.description
        - persona -> state.system_prompt
        - skills -> state.tools (transformed)
        - memory -> state.memory_blocks
        - settings.llm -> state.llm_model_config
    """
    if isinstance(openclaw_data, dict):
        openclaw = OpenClawAgent.from_dict(openclaw_data)
    else:
        openclaw = openclaw_data

    agent_name = name or openclaw.name or "Unnamed Agent"

    tools = []
    for skill in openclaw.skills:
        params = skill.get("parameters", {})
        arguments = []
        
        properties = params.get("properties", {})
        if isinstance(properties, dict):
            for param_name, param_info in properties.items():
                arg = ToolArgument(
                    name=param_name,
                    type=param_info.get("type", "string"),
                    description=param_info.get("description", ""),
                    required=param_name in params.get("required", []),
                    enum=param_info.get("enum"),
                )
                arguments.append(arg)

        handler = skill.get("handler", {})
        code = ""
        if isinstance(handler, dict):
            code = handler.get("code", "")

        tool = Tool(
            name=skill.get("name", "unnamed_tool"),
            description=skill.get("description", ""),
            type="function",
            enabled=skill.get("enabled", True),
            arguments=arguments,
            code=code,
        )
        tools.append(tool)

    memory_blocks = []
    for mem in openclaw.memory:
        block = MemoryBlock(
            label=mem.get("type", "general"),
            text=mem.get("content", ""),
            enabled=mem.get("enabled", True),
            in_context=mem.get("context", True),
        )
        memory_blocks.append(block)

    llm_settings = openclaw.settings.get("llm", {})
    provider_str = llm_settings.get("provider", "openai")
    
    try:
        provider = ModelProvider(provider_str)
    except ValueError:
        provider = ModelProvider.OPENAI

    model_config = ModelConfig(
        provider=provider,
        model=llm_settings.get("model", "gpt-4"),
        temperature=llm_settings.get("temperature", 0.7),
        max_tokens=llm_settings.get("max_tokens", 4096),
        model_kwargs=openclaw.settings.get("model_kwargs", {}),
    )

    metadata = AgentMetadata(
        name=agent_name,
        description=openclaw.description or "",
        version=openclaw.version,
        author=openclaw.author,
        tags=openclaw.metadata.get("tags", []),
    )

    state = AgentState(
        system_prompt=openclaw.persona,
        llm_model_config=model_config,
        tools=tools,
        memory_blocks=memory_blocks,
    )

    return AgentPort(
        name=agent_name,
        system_prompt=openclaw.persona,
        model_config=model_config,
        description=openclaw.description,
        version=openclaw.version,
        author=openclaw.author,
        tags=openclaw.metadata.get("tags", []),
        tools=tools,
        memory_blocks=memory_blocks,
    )


def from_openclaw_file(file_path: str | Path) -> AgentPort:
    """Load and convert OpenClaw JSON file to AgentPort.

    Args:
        file_path: Path to OpenClaw JSON file.

    Returns:
        AgentPort instance.

    Raises:
        FileNotFoundError: If file does not exist.
        ValueError: If JSON is invalid.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    content = path.read_text(encoding="utf-8")
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}") from e

    return from_openclaw_to_letta(data)


def to_openclaw_file(agent: AgentPort, file_path: str | Path) -> None:
    """Save AgentPort to OpenClaw JSON file.

    Args:
        agent: AgentPort instance to convert.
        file_path: Output file path.
    """
    openclaw = from_letta_to_openclaw(agent)
    content = json.dumps(
        openclaw.to_dict(),
        indent=2,
        ensure_ascii=False,
    )
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


__all__ = [
    "OpenClawAgent",
    "from_letta_to_openclaw",
    "from_openclaw_to_letta",
    "from_openclaw_file",
    "to_openclaw_file",
]
