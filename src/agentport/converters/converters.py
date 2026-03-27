from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from agentport.core import AgentPort
from agentport.schema import AgentFile


def to_json(agent: AgentPort, indent: int = 2) -> str:
    """Convert an AgentPort instance to JSON string.

    Args:
        agent: The AgentPort instance to convert.
        indent: JSON indentation level (default: 2).

    Returns:
        JSON string representation of the agent.
    """
    agent_file = AgentFile(
        version="1.0",
        metadata=agent.metadata,
        state=agent.state,
    )
    return json.dumps(
        agent_file.model_dump(exclude_none=True, mode="json"),
        indent=indent,
        ensure_ascii=False,
    )


def from_json(json_str: str) -> AgentPort:
    """Create an AgentPort instance from JSON string.

    Args:
        json_str: JSON string containing agent data.

    Returns:
        AgentPort instance.

    Raises:
        ValueError: If JSON is invalid or missing required fields.
    """
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}") from e

    return _agentport_from_data(data)


def from_json_file(file_path: str | Path) -> AgentPort:
    """Load an AgentPort from a JSON file.

    Args:
        file_path: Path to the JSON file.

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
    return from_json(content)


def to_json_file(agent: AgentPort, file_path: str | Path, indent: int = 2) -> None:
    """Save an AgentPort instance to a JSON file.

    Args:
        agent: The AgentPort instance to save.
        file_path: Output file path.
        indent: JSON indentation level (default: 2).
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    content = to_json(agent, indent=indent)
    path.write_text(content, encoding="utf-8")


def _agentport_from_data(data: dict[str, Any]) -> AgentPort:
    """Create AgentPort from parsed JSON data.

    Args:
        data: Parsed JSON data dictionary.

    Returns:
        AgentPort instance.

    Raises:
        ValueError: If data is invalid.
    """
    try:
        agent_file = AgentFile.model_validate(data)
    except Exception as e:
        raise ValueError(f"Invalid agent data: {e}") from e

    metadata = agent_file.metadata
    state = agent_file.state

    from agentport.schema import (
        EnvVar,
        MemoryBlock,
        Message,
        ModelConfig,
        Tool,
        ToolRule,
    )

    return AgentPort(
        name=metadata.name,
        system_prompt=state.system_prompt,
        model_config=state.llm_model_config,
        description=metadata.description,
        version=metadata.version,
        author=metadata.author,
        tags=list(metadata.tags),
        tools=list(state.tools),
        tool_rules=list(state.tool_rules),
        memory_blocks=list(state.memory_blocks),
        message_history=list(state.message_history),
        env_vars=list(state.env_vars),
    )


__all__ = [
    "to_json",
    "from_json",
    "from_json_file",
    "to_json_file",
]
