from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml

from agentport.schema import (
    AgentFile,
    AgentMetadata,
    AgentState,
    EnvVar,
    MemoryBlock,
    Message,
    ModelConfig,
    ModelProvider,
    Tool,
    ToolRule,
)


class ValidationError(Exception):
    pass


class AgentPort:
    def __init__(
        self,
        name: str,
        system_prompt: str,
        model_config: ModelConfig,
        description: Optional[str] = None,
        version: str = "1.0.0",
        author: Optional[str] = None,
        tags: Optional[list[str]] = None,
        tools: Optional[list[Tool]] = None,
        tool_rules: Optional[list[ToolRule]] = None,
        memory_blocks: Optional[list[MemoryBlock]] = None,
        message_history: Optional[list[Message]] = None,
        env_vars: Optional[list[EnvVar]] = None,
    ) -> None:
        self.metadata = AgentMetadata(
            name=name,
            description=description,
            version=version,
            author=author,
            tags=tags or [],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.state = AgentState(
            llm_model_config=model_config,
            system_prompt=system_prompt,
            tools=tools or [],
            tool_rules=tool_rules or [],
            memory_blocks=memory_blocks or [],
            message_history=message_history or [],
            env_vars=env_vars or [],
        )

    @classmethod
    def from_af(cls, file_path: str | Path) -> AgentPort:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Agent file not found: {path}")

        content = path.read_text(encoding="utf-8")
        if path.suffix.lower() in (".yaml", ".yml"):
            data = yaml.safe_load(content)
        elif path.suffix.lower() == ".af":
            try:
                data = yaml.safe_load(content)
            except yaml.YAMLError:
                data = json.loads(content)
        else:
            data = json.loads(content)

        data = cls._normalize_legacy_format(data)
        agent_file = AgentFile.model_validate(data)
        return cls._from_agent_file(agent_file)

    @classmethod
    def _normalize_legacy_format(cls, data: dict[str, Any]) -> dict[str, Any]:
        needs_normalization = False
        if "metadata" not in data or "state" not in data:
            needs_normalization = True
        elif not data.get("metadata", {}).get("name"):
            needs_normalization = True
        elif "llm_model_config" not in data.get("state", {}):
            needs_normalization = True
        
        if needs_normalization:
            metadata = data.get("metadata", {})
            if not metadata or "name" not in metadata:
                metadata = {
                    "name": data.get("agent_name", "Unnamed Agent"),
                    "description": data.get("description"),
                    "version": data.get("version", "1.0.0"),
                }
                created_by = data.get("created_by")
                created_at = data.get("created_at")
                if created_by:
                    metadata["author"] = created_by
                if created_at:
                    metadata["created_at"] = created_at

            model_config = data.get("model_config", {})
            if isinstance(model_config, dict):
                provider = model_config.get("provider", "openai")
                model = model_config.get("model", "")
                state = {
                    "llm_model_config": {
                        "provider": provider,
                        "model": model,
                        "temperature": model_config.get("temperature", 0.7),
                        "max_tokens": model_config.get("max_tokens"),
                        "model_kwargs": {},
                    },
                    "system_prompt": data.get("system_prompt", ""),
                    "tools": cls._normalize_tools(data.get("tools", [])),
                    "tool_rules": data.get("tool_rules", []),
                    "memory_blocks": cls._normalize_memory_blocks(data.get("memory_blocks", [])),
                    "message_history": cls._normalize_messages(data.get("message_history", [])),
                    "env_vars": cls._normalize_env_vars(data.get("env_vars", {})),
                }
            else:
                state = {
                    "llm_model_config": {"provider": "openai", "model": "", "temperature": 0.7, "model_kwargs": {}},
                    "system_prompt": data.get("system_prompt", ""),
                    "tools": [],
                    "tool_rules": [],
                    "memory_blocks": [],
                    "message_history": [],
                    "env_vars": [],
                }

            data = {"version": data.get("version", "1.0"), "metadata": metadata, "state": state}

        return data

    @staticmethod
    def _normalize_tools(tools: list[Any]) -> list[dict[str, Any]]:
        normalized = []
        for tool in tools:
            if isinstance(tool, dict):
                normalized_tool = {
                    "name": tool.get("name", ""),
                    "description": tool.get("description", ""),
                    "type": "function",
                    "code": tool.get("code"),
                    "arguments": [],
                    "enabled": True,
                }
                schema = tool.get("schema")
                if schema and isinstance(schema, dict):
                    props = schema.get("properties", {})
                    args = []
                    for prop_name, prop_info in props.items():
                        arg = {
                            "name": prop_name,
                            "type": prop_info.get("type", "string"),
                            "description": prop_info.get("description"),
                            "required": prop_name in schema.get("required", []),
                        }
                        if "enum" in prop_info:
                            arg["enum"] = prop_info["enum"]
                        args.append(arg)
                    normalized_tool["arguments"] = args
                normalized.append(normalized_tool)
        return normalized

    @staticmethod
    def _normalize_memory_blocks(blocks: list[Any]) -> list[dict[str, Any]]:
        normalized = []
        for block in blocks:
            if isinstance(block, dict):
                normalized.append({
                    "label": block.get("label", "custom"),
                    "text": block.get("value", block.get("text", "")),
                    "enabled": True,
                    "in_context": block.get("in_context", True),
                    "metadata": {},
                })
        return normalized

    @staticmethod
    def _normalize_messages(messages: list[Any]) -> list[dict[str, Any]]:
        normalized = []
        for msg in messages:
            if isinstance(msg, dict):
                normalized.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", ""),
                    "in_context": msg.get("in_context", True),
                })
        return normalized

    @staticmethod
    def _normalize_env_vars(env_vars: Any) -> list[dict[str, Any]]:
        if isinstance(env_vars, dict):
            return [{"name": k, "value": str(v), "secret": False} for k, v in env_vars.items()]
        if isinstance(env_vars, list):
            return env_vars
        return []

    @classmethod
    def _from_agent_file(cls, agent_file: AgentFile) -> AgentPort:
        metadata = agent_file.metadata
        state = agent_file.state

        port = cls(
            name=metadata.name,
            system_prompt=state.system_prompt,
            model_config=state.llm_model_config,
            description=metadata.description,
            version=metadata.version,
            author=metadata.author,
            tags=metadata.tags,
            tools=state.tools,
            tool_rules=state.tool_rules,
            memory_blocks=state.memory_blocks,
            message_history=state.message_history,
            env_vars=state.env_vars,
        )
        return port

    def to_af(
        self,
        file_path: Optional[str | Path] = None,
        format: str = "yaml",
    ) -> str:
        agent_file = AgentFile(
            version="1.0",
            metadata=self.metadata,
            state=self.state,
        )

        if format == "yaml":
            content = yaml.dump(
                agent_file.model_dump(exclude_none=True, mode="json"),
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )
        elif format == "json":
            content = json.dumps(
                agent_file.model_dump(exclude_none=True, mode="json"),
                indent=2,
                ensure_ascii=False,
            )
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'yaml' or 'json'.")

        if file_path:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

        return content

    def validate(self) -> tuple[bool, list[str]]:
        errors: list[str] = []

        if not self.metadata.name:
            errors.append("Agent name is required")
        if not self.state.system_prompt:
            errors.append("System prompt is required")
        if not self.state.llm_model_config.provider:
            errors.append("Model provider is required")
        if not self.state.llm_model_config.model:
            errors.append("Model name is required")

        tool_names = set()
        for tool in self.state.tools:
            if tool.name in tool_names:
                errors.append(f"Duplicate tool name: {tool.name}")
            tool_names.add(tool.name)

            if not tool.description:
                errors.append(f"Tool '{tool.name}' description is required")

        for rule in self.state.tool_rules:
            if rule.tool_name and rule.tool_name not in tool_names:
                errors.append(f"Tool rule references unknown tool: {rule.tool_name}")

        return len(errors) == 0, errors

    def add_tool(self, tool: Tool) -> None:
        if any(t.name == tool.name for t in self.state.tools):
            raise ValueError(f"Tool with name '{tool.name}' already exists")
        self.state.tools.append(tool)
        self._mark_updated()

    def remove_tool(self, tool_name: str) -> None:
        for i, tool in enumerate(self.state.tools):
            if tool.name == tool_name:
                self.state.tools.pop(i)
                self._mark_updated()
                return
        raise ValueError(f"Tool not found: {tool_name}")

    def add_memory_block(self, block: MemoryBlock) -> None:
        self.state.memory_blocks.append(block)
        self._mark_updated()

    def remove_memory_block(self, block_id: str) -> None:
        for i, block in enumerate(self.state.memory_blocks):
            if block.id == block_id:
                self.state.memory_blocks.pop(i)
                self._mark_updated()
                return
        raise ValueError(f"Memory block not found: {block_id}")

    def add_message(self, message: Message) -> None:
        self.state.message_history.append(message)

    def add_env_var(self, env_var: EnvVar) -> None:
        if any(e.name == env_var.name for e in self.state.env_vars):
            raise ValueError(f"Environment variable '{env_var.name}' already exists")
        self.state.env_vars.append(env_var)
        self._mark_updated()

    def get_env_dict(self) -> dict[str, str]:
        return {e.name: e.value for e in self.state.env_vars}

    def _mark_updated(self) -> None:
        self.metadata.updated_at = datetime.now()

    def model_dump(self) -> dict[str, Any]:
        return {
            "metadata": self.metadata.model_dump(),
            "state": self.state.model_dump(),
        }

    def __repr__(self) -> str:
        return (
            f"AgentPort(name='{self.metadata.name}', "
            f"model='{self.state.llm_model_config.provider.value}:{self.state.llm_model_config.model}', "
            f"tools={len(self.state.tools)}, "
            f"memory_blocks={len(self.state.memory_blocks)})"
        )
