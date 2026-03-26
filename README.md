# AgentPort 🚀
**Built by a China programmer who wants AI agents to have real portability.**

[![Python](https://img.shields.io/pypi/pyversions/agentport.svg)](https://pypi.org/project/agentport/)
[![License](https://img.shields.io/pypi/l/agentport.svg)](https://github.com/BodhiVajra/agentport/blob/main/LICENSE)
[![Stars](https://img.shields.io/github/stars/BodhiVajra/agentport.svg)](https://github.com/BodhiVajra/agentport)

**The missing piece for stateful AI agents: portable, interchangeable, GitHub-native.**

支持 .af（Letta官方格式） + 跨框架转换 + CLI + GitHub Action。  
让你的agent像Docker容器一样：随时 checkpoint、迁移、版本控制、分享。

**Why?** AI agents正在从"一次性"走向"终身数字生命"。AgentPort 让它们真正 portable。

**Built with ❤️ by a Hangzhou programmer for the AI agent era.**

[Install](#install) | [Quickstart](#quickstart) | [CLI Usage](#cli-usage) | [HangZhou Programmer Example](#HangZhou-programmer-example) | [Roadmap](#roadmap)

## Install

```bash
pip install agentport
```

**即将发布 PyPI，敬请期待！**

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

# New API (v1.0+)
print(agent.metadata.name)          # agent name
print(agent.metadata.description)   # agent description
print(agent.metadata.author)         # author
print(agent.state.llm_model_config.model)       # model name
print(agent.state.llm_model_config.provider)    # provider (Enum)
print(agent.state.system_prompt)   # system prompt
print(agent.state.tools)            # list of Tool objects
print(agent.state.memory_blocks)    # list of MemoryBlock objects
```

### Save to .af file

```python
agent.to_af("output.af", format="yaml")

# Export to JSON
agent.to_af("output.json", format="json")
```

### Legacy Format Support

AgentPort automatically converts legacy .af files to the new format:

```python
# Legacy format (agent_name, model_config at root level)
agent = AgentPort.from_af("legacy.af")

# Automatically normalized to new format:
# - agent_name -> metadata.name
# - model_config -> state.llm_model_config
# - memory_blocks[].value -> memory_blocks[].text
```

## CLI Usage

Install AgentPort and use the CLI:

```bash
# Validate an agent file
agentport validate examples/hangzhou-code-reviewer.af

# Show agent details
agentport info examples/hangzhou-code-reviewer.af

# Export agent to different formats
agentport export examples/hangzhou-code-reviewer.af --format json

# Import from .af and convert to JSON
agentport import examples/hangzhou-code-reviewer.af --to json
```

### Commands

| Command | Description |
|---------|-------------|
| `agentport validate <file.af>` | Validate agent file schema |
| `agentport info <file.af>` | Show agent details |
| `agentport export <file.af> [--format yaml\|json]` | Export to specified format |
| `agentport import <file.af> [--to json]` | Import and convert .af file |

## Hangzhou Programmer Example

示例：examples/hangzhou-code-reviewer.af  
一个专为杭州程序员打造的代码审查agent。你可以用AgentPort轻松迁移到任何支持.af 的框架，随时在通勤地铁上继续审查代码。

Meet **Jinxiang**, a backend engineer in HangZhou. He's working on a team with developers across China, using Claude Code for code review.

### The Problem

Jinxiang's team reviews 50+ PRs daily. Manual code review is:
- Time-consuming (2-3 hours per day)
- Inconsistent (different reviewers have different standards)
- Missing security issues (hard to catch everything)

### The Solution: AgentPort Code Reviewer

```bash
# Load the HangZhou code-reviewer agent
agentport info examples/hangzhou-code-reviewer.af
```

The `hangzhou-code-reviewer.af` agent includes:
- **System Prompt**: Expert code reviewer specializing in Python/JS/TS
- **Tools**: `review_code`, `suggest_pr_optimization`, `check_alipay_compatible`, `optimize_for_china_cloud`
- **Memory**: Persona + guidelines + context blocks

### Real Workflow

```python
from agentport import AgentPort

agent = AgentPort.from_af("examples/hangzhou-code-reviewer.af")

# Jinxiang's workflow:
# 1. Pull request arrives
# 2. Feed diff to agent.review_code()
# 3. Get structured feedback with severity levels

# Output example:
{
    "file": "src/auth.py",
    "issues": [
        {"severity": "critical", "line": 42, "message": "SQL injection risk", "suggestion": "Use parameterized query"},
        {"severity": "major", "line": 78, "message": "Missing error handling", "suggestion": "Add try-except block"},
        {"severity": "minor", "line": 15, "message": "PEP 8 violation", "suggestion": "Add space around operators"}
    ]
}
```

### Benefits

- ⏱️ **Save 2 hours/day** - Automated first-pass review
- 🔒 **Catch security issues** - Always run security checks
- 📊 **Consistent quality** - Same standards every time
- 📚 **Learn and improve** - Agent suggests test cases
- 🇨🇳 **China Cloud Ready** - Special tools for Alipay/compatible and China cloud optimization

### Portability

Jinxiang can share his reviewer agent:

```bash
# Export and share
agentport export examples/hangzhou-code-reviewer.af --format yaml

# Team member imports
agentport import examples/hangzhou-code-reviewer.af
```

Now the whole team uses the same expert reviewer!

## Roadmap

- [x] Core Schema: Pydantic models for .af format
- [x] Load/Save .af files
- [x] CLI tool with import/export commands
- [x] Basic converters (JSON state)
- [x] Legacy format auto-normalization
- [x] GitHub Action for automatic export