# AgentPort 🚀

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/) 
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://github.com/BodhiVajra/agentport/blob/main/LICENSE) 
[![Built by Hangzhou Programmer](https://img.shields.io/badge/Built%20by-Hangzhou%20Programmer-orange.svg)](https://github.com/BodhiVajra/agentport) 
[![Stars](https://img.shields.io/github/stars/BodhiVajra/agentport.svg)](https://github.com/BodhiVajra/agentport)

**Built with ❤️ by a Hangzhou programmer for the AI agent era.**
**杭州程序员为AI agent时代而打造。**

**The missing piece for stateful AI agents: portable, interchangeable, GitHub-native.**
**有状态的AI智能体的缺失拼图：可移植、可互换、GitHub原生。**

Support Letta(.af) ⇄ OpenClaw migration · CLI tools · GitHub Action · Cross-framework portability.
**支持 Letta(.af) ⇄ OpenClaw 双向迁移 · CLI 工具 · GitHub Action · 跨框架可移植性。**

Your agent, your digital life. No lock-in, no rebuild. Migrate anytime, anywhere.
**你的agent，你的数字生命。无锁定，无需重建。随时迁移，随处使用。**

[Install](#install) | [Quickstart](#quickstart) | [CLI Usage](#cli-usage) | [HangZhou Programmer Example](#HangZhou-programmer-example) | [Roadmap](#roadmap)

## Install / 安装

```bash
pip install agentport
```
**Coming soon to PyPI! 即将发布 PyPI，敬请期待！**

## Quickstart / 快速开始

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

## Multi-Framework Migration

**解决agent框架快速迭代带来的反复训练痛点，先支持Letta + OpenClaw。**

AgentPort 让你的 agent 真正具备"数字生命"——不依赖于特定框架，随时迁移、备份、分享。

```bash
# Migrate Letta .af to OpenClaw format
agentport migrate examples/hangzhou-code-reviewer.af --from letta --to openclaw

# Migrate OpenClaw JSON to Letta .af format
agentport migrate examples/hangzhou-openclaw-reviewer.json --from openclaw --to letta
```

### Supported Migrations

| From | To | Status |
|------|-----|--------|
| Letta (.af) | OpenClaw (.json) | ✅ |
| OpenClaw (.json) | Letta (.af) | ✅ |

### Migration Features

- **Rich Table Output**: Shows comparison before/after migration
- **Preserves Identity**: Agent name, description, author
- **Maps Concepts**: Tools ↔ Skills, Memory Blocks ↔ Memory, Model Config ↔ Settings
- **Auto-Conversion**: Handles field naming differences automatically

## Roadmap

- [x] Core Schema: Pydantic models for .af format
- [x] Load/Save .af files
- [x] CLI tool with import/export commands
- [x] Basic converters (JSON state)
- [x] Legacy format auto-normalization
- [x] GitHub Action for automatic export
- [x] Letta <-> OpenClaw migration