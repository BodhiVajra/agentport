from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional

from agentport.schema import AgentFile

if TYPE_CHECKING:
    from agentport.core import AgentPort


T = Any


class FrameworkAdapter(ABC):
    @abstractmethod
    def to_apf(self, source_data: dict) -> AgentFile:
        pass

    @abstractmethod
    def from_apf(self, agent_file: AgentFile) -> dict:
        pass

    @abstractmethod
    def validate_migration(self, before: AgentFile, after: AgentFile) -> dict:
        pass


class LettaAdapter(FrameworkAdapter):
    def to_apf(self, source_data: dict) -> AgentFile:
        from agentport.core import AgentPort
        from agentport.schema import AgentFile

        agent = AgentPort._from_agent_file(AgentFile.model_validate(source_data))
        return AgentFile(
            version="1.0",
            metadata=agent.metadata,
            state=agent.state,
        )

    def from_apf(self, agent_file: AgentFile) -> dict:
        from agentport.converters.converters import to_json

        return to_json_file_format(agent_file)

    def validate_migration(self, before: AgentFile, after: AgentFile) -> dict:
        return {
            "name_preserved": before.metadata.name == after.metadata.name,
            "description_preserved": before.metadata.description == after.metadata.description,
            "author_preserved": before.metadata.author == after.metadata.author,
            "system_prompt_preserved": before.state.system_prompt == after.state.system_prompt,
            "tools_count": len(before.state.tools),
            "memory_blocks_count": len(before.state.memory_blocks),
        }


class OpenClawAdapter(FrameworkAdapter):
    def to_apf(self, source_data: dict) -> AgentFile:
        from agentport.converters.openclaw import from_openclaw_to_letta

        return from_openclaw_to_letta(source_data)

    def from_apf(self, agent_file: AgentFile) -> dict:
        from agentport.converters.openclaw import from_letta_to_openclaw

        return from_letta_to_openclaw_agentfile(agent_file)

    def validate_migration(self, before: AgentFile, after: AgentFile) -> dict:
        return {
            "name_preserved": before.metadata.name == after.metadata.name,
            "description_preserved": before.metadata.description == after.metadata.description,
            "author_preserved": before.metadata.author == after.metadata.author,
            "system_prompt_preserved": before.state.system_prompt == after.state.system_prompt,
            "tools_count": len(before.state.tools),
            "memory_blocks_count": len(before.state.memory_blocks),
        }


ADAPTERS = {
    "letta": LettaAdapter(),
    "openclaw": OpenClawAdapter(),
}


def register_adapter(name: str, adapter: FrameworkAdapter) -> None:
    ADAPTERS[name] = adapter


def get_adapter(name: str) -> Optional[FrameworkAdapter]:
    return ADAPTERS.get(name)


def to_json_file_format(agent_file: AgentFile) -> dict:
    import json
    return json.loads(json.dumps(agent_file.model_dump(exclude_none=True, mode="json")))


def from_letta_to_openclaw_agentfile(agent_file: AgentFile) -> dict:
    from agentport.converters.openclaw import from_letta_to_openclaw
    from agentport.core import AgentPort

    agent = AgentPort._from_agent_file(agent_file)
    openclaw_agent = from_letta_to_openclaw(agent)
    return openclaw_agent.to_dict()


__all__ = [
    "FrameworkAdapter",
    "LettaAdapter",
    "OpenClawAdapter",
    "ADAPTERS",
    "register_adapter",
    "get_adapter",
]