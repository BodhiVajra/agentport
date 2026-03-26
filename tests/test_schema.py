from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import yaml

from agentport import AgentPort, ValidationError
from agentport.schema import (
    AgentFile,
    AgentMetadata,
    AgentState,
    EnvVar,
    MemoryBlock,
    Message,
    MessageRole,
    ModelConfig,
    ModelProvider,
    Tool,
    ToolArgument,
    ToolRule,
    ToolType,
)


class TestModelConfig:
    def test_default_values(self) -> None:
        config = ModelConfig(provider=ModelProvider.OPENAI, model="gpt-4")
        assert config.provider == ModelProvider.OPENAI
        assert config.model == "gpt-4"
        assert config.temperature == 0.7
        assert config.max_tokens is None

    def test_custom_values(self) -> None:
        config = ModelConfig(
            provider=ModelProvider.ANTHROPIC,
            model="claude-3-opus",
            temperature=0.3,
            max_tokens=4096,
        )
        assert config.temperature == 0.3
        assert config.max_tokens == 4096

    def test_temperature_bounds(self) -> None:
        with pytest.raises(ValueError):
            ModelConfig(provider=ModelProvider.OPENAI, model="gpt-4", temperature=3.0)


class TestTool:
    def test_tool_creation(self) -> None:
        tool = Tool(
            name="search",
            description="Search for information",
            type=ToolType.FUNCTION,
        )
        assert tool.name == "search"
        assert tool.enabled is True

    def test_tool_with_arguments(self) -> None:
        arg = ToolArgument(
            name="query",
            type="string",
            description="Search query",
            required=True,
        )
        tool = Tool(
            name="search",
            description="Search for information",
            arguments=[arg],
        )
        assert len(tool.arguments) == 1
        assert tool.arguments[0].name == "query"


class TestMemoryBlock:
    def test_memory_block_creation(self) -> None:
        block = MemoryBlock(
            label="persona",
            text="You are a helpful assistant.",
            in_context=True,
        )
        assert block.label == "persona"
        assert block.enabled is True

    def test_memory_block_with_metadata(self) -> None:
        block = MemoryBlock(
            label="human",
            text="User preferences",
            metadata={"priority": "high"},
        )
        assert block.metadata["priority"] == "high"


class TestMessage:
    def test_message_creation(self) -> None:
        msg = Message(
            role=MessageRole.USER,
            content="Hello, how are you?",
        )
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello, how are you?"

    def test_tool_message(self) -> None:
        msg = Message(
            role=MessageRole.TOOL,
            content="Search results: ...",
            tool_call_id="call_123",
            tool_name="search",
        )
        assert msg.role == MessageRole.TOOL
        assert msg.tool_call_id == "call_123"


class TestEnvVar:
    def test_env_var_creation(self) -> None:
        env = EnvVar(
            name="OPENAI_API_KEY",
            value="sk-...",
            secret=True,
        )
        assert env.name == "OPENAI_API_KEY"
        assert env.secret is True


class TestAgentFile:
    def test_agent_file_creation(self) -> None:
        metadata = AgentMetadata(name="test-agent", version="1.0.0")
        state = AgentState(
            model_config=ModelConfig(provider=ModelProvider.OPENAI, model="gpt-4"),
            system_prompt="You are helpful.",
        )
        agent_file = AgentFile(
            version="1.0",
            metadata=metadata,
            state=state,
        )
        assert agent_file.version == "1.0"
        assert agent_file.metadata.name == "test-agent"

    def test_invalid_version(self) -> None:
        with pytest.raises(ValueError):
            AgentFile(
                version="3.0",
                metadata=AgentMetadata(name="test"),
                state=AgentState(
                    model_config=ModelConfig(provider=ModelProvider.OPENAI, model="gpt-4"),
                    system_prompt="test",
                ),
            )


class TestAgentPort:
    def test_agent_port_creation(self) -> None:
        config = ModelConfig(provider=ModelProvider.OPENAI, model="gpt-4")
        agent = AgentPort(
            name="my-agent",
            system_prompt="You are helpful.",
            model_config=config,
        )
        assert agent.metadata.name == "my-agent"
        assert agent.state.system_prompt == "You are helpful."

    def test_add_tool(self) -> None:
        config = ModelConfig(provider=ModelProvider.OPENAI, model="gpt-4")
        agent = AgentPort(
            name="my-agent",
            system_prompt="You are helpful.",
            model_config=config,
        )
        tool = Tool(name="test-tool", description="A test tool")
        agent.add_tool(tool)
        assert len(agent.state.tools) == 1

    def test_add_duplicate_tool(self) -> None:
        config = ModelConfig(provider=ModelProvider.OPENAI, model="gpt-4")
        agent = AgentPort(
            name="my-agent",
            system_prompt="You are helpful.",
            model_config=config,
        )
        tool = Tool(name="test-tool", description="A test tool")
        agent.add_tool(tool)
        with pytest.raises(ValueError):
            agent.add_tool(tool)

    def test_remove_tool(self) -> None:
        config = ModelConfig(provider=ModelProvider.OPENAI, model="gpt-4")
        agent = AgentPort(
            name="my-agent",
            system_prompt="You are helpful.",
            model_config=config,
        )
        tool = Tool(name="test-tool", description="A test tool")
        agent.add_tool(tool)
        agent.remove_tool("test-tool")
        assert len(agent.state.tools) == 0

    def test_add_memory_block(self) -> None:
        config = ModelConfig(provider=ModelProvider.OPENAI, model="gpt-4")
        agent = AgentPort(
            name="my-agent",
            system_prompt="You are helpful.",
            model_config=config,
        )
        block = MemoryBlock(label="persona", text="You are a coding expert.")
        agent.add_memory_block(block)
        assert len(agent.state.memory_blocks) == 1

    def test_add_env_var(self) -> None:
        config = ModelConfig(provider=ModelProvider.OPENAI, model="gpt-4")
        agent = AgentPort(
            name="my-agent",
            system_prompt="You are helpful.",
            model_config=config,
        )
        env = EnvVar(name="API_KEY", value="secret", secret=True)
        agent.add_env_var(env)
        assert len(agent.state.env_vars) == 1

    def test_get_env_dict(self) -> None:
        config = ModelConfig(provider=ModelProvider.OPENAI, model="gpt-4")
        agent = AgentPort(
            name="my-agent",
            system_prompt="You are helpful.",
            model_config=config,
        )
        agent.add_env_var(EnvVar(name="KEY1", value="value1"))
        agent.add_env_var(EnvVar(name="KEY2", value="value2"))
        env_dict = agent.get_env_dict()
        assert env_dict["KEY1"] == "value1"
        assert env_dict["KEY2"] == "value2"


class TestAgentPortValidation:
    def test_valid_agent(self) -> None:
        config = ModelConfig(provider=ModelProvider.OPENAI, model="gpt-4")
        agent = AgentPort(
            name="valid-agent",
            system_prompt="You are helpful.",
            model_config=config,
        )
        is_valid, errors = agent.validate()
        assert is_valid is True
        assert len(errors) == 0

    def test_missing_name(self) -> None:
        config = ModelConfig(provider=ModelProvider.OPENAI, model="gpt-4")
        agent = AgentPort(
            name="",
            system_prompt="You are helpful.",
            model_config=config,
        )
        is_valid, errors = agent.validate()
        assert is_valid is False
        assert "Agent name is required" in errors

    def test_missing_system_prompt(self) -> None:
        config = ModelConfig(provider=ModelProvider.OPENAI, model="gpt-4")
        agent = AgentPort(
            name="test-agent",
            system_prompt="",
            model_config=config,
        )
        is_valid, errors = agent.validate()
        assert is_valid is False
        assert "System prompt is required" in errors

    def test_duplicate_tool_names(self) -> None:
        config = ModelConfig(provider=ModelProvider.OPENAI, model="gpt-4")
        agent = AgentPort(
            name="test-agent",
            system_prompt="You are helpful.",
            model_config=config,
        )
        agent.add_tool(Tool(name="tool", description="Tool 1"))
        agent.add_tool(Tool(name="tool", description="Tool 2"))
        is_valid, errors = agent.validate()
        assert is_valid is False
        assert any("Duplicate tool name" in e for e in errors)


class TestAgentPortSerialization:
    def test_to_af_yaml(self, tmp_path: Path) -> None:
        config = ModelConfig(provider=ModelProvider.OPENAI, model="gpt-4")
        agent = AgentPort(
            name="test-agent",
            system_prompt="You are helpful.",
            model_config=config,
        )
        output_path = tmp_path / "test.af"
        content = agent.to_af(output_path, format="yaml")
        assert output_path.exists()
        assert "version:" in content
        assert "test-agent" in content

    def test_to_af_json(self, tmp_path: Path) -> None:
        config = ModelConfig(provider=ModelProvider.OPENAI, model="gpt-4")
        agent = AgentPort(
            name="test-agent",
            system_prompt="You are helpful.",
            model_config=config,
        )
        output_path = tmp_path / "test.json"
        content = agent.to_af(output_path, format="json")
        assert output_path.exists()
        data = json.loads(content)
        assert data["metadata"]["name"] == "test-agent"

    def test_from_af_yaml(self, tmp_path: Path) -> None:
        config = ModelConfig(provider=ModelProvider.OPENAI, model="gpt-4")
        agent = AgentPort(
            name="test-agent",
            system_prompt="You are helpful.",
            model_config=config,
        )
        output_path = tmp_path / "test.af"
        agent.to_af(output_path, format="yaml")

        loaded = AgentPort.from_af(output_path)
        assert loaded.metadata.name == "test-agent"
        assert loaded.state.system_prompt == "You are helpful."

    def test_from_af_json(self, tmp_path: Path) -> None:
        config = ModelConfig(provider=ModelProvider.OPENAI, model="gpt-4")
        agent = AgentPort(
            name="test-agent",
            system_prompt="You are helpful.",
            model_config=config,
        )
        output_path = tmp_path / "test.json"
        agent.to_af(output_path, format="json")

        loaded = AgentPort.from_af(output_path)
        assert loaded.metadata.name == "test-agent"

    def test_file_not_found(self) -> None:
        with pytest.raises(FileNotFoundError):
            AgentPort.from_af("nonexistent.af")


class TestAgentPortRepr:
    def test_repr(self) -> None:
        config = ModelConfig(provider=ModelProvider.OPENAI, model="gpt-4")
        agent = AgentPort(
            name="test-agent",
            system_prompt="You are helpful.",
            model_config=config,
        )
        repr_str = repr(agent)
        assert "test-agent" in repr_str
        assert "gpt-4" in repr_str
