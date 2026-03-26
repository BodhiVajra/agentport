# AgentPort 🚀

**The missing piece for stateful AI agents: portable, interchangeable, GitHub-native.**

支持 .af（Letta官方格式） + 跨框架转换 + CLI + GitHub Action。  
让你的agent像Docker容器一样：随时 checkpoint、迁移、版本控制、分享。

**Why?** AI agents正在从"一次性"走向"终身数字生命"。AgentPort 让它们真正 portable。

[Install](#install) | [Quickstart](#quickstart) | [Roadmap](#roadmap)

## Install

```bash
pip install agentport
```

Or using uv:

```bash
uv add agentport
```

## Quickstart

```python
from agentport import AgentPort
from agentport.schema import ModelConfig, ModelProvider, Tool, ToolArgument

config = ModelConfig(
    provider=ModelProvider.OPENAI,
    model="gpt-4",
    temperature=0.7,
)

agent = AgentPort(
    name="my-agent",
    system_prompt="You are a helpful coding assistant.",
    model_config=config,
    description="My first portable agent",
)

is_valid, errors = agent.validate()
print(f"Valid: {is_valid}, Errors: {errors}")

agent.to_af("my-agent.af")
loaded = AgentPort.from_af("my-agent.af")
print(loaded)
```

### Load from .af file

```python
from agentport import AgentPort

agent = AgentPort.from_af("path/to/agent.af")
print(agent.metadata.name)
print(agent.state.system_prompt)
```

### Save to .af file

```python
agent.to_af("output.af", format="yaml")
```

## Roadmap

- [ ] Core Schema: Pydantic models for .af format
- [ ] Load/Save .af files
- [ ] CLI tool with import/export commands
- [ ] Basic converters (JSON state)
- [ ] GitHub Action for automatic export