from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

from agentport import AgentPort, ValidationError

app = typer.Typer(
    name="agentport",
    help="Portable AI agents: Letta .af format support, cross-framework migration",
    add_completion=False,
)

ConvertFrom = Annotated[str, typer.Option("--from", help="Source format: letta, langchain, crewai")]
ConvertTo = Annotated[str, typer.Option("--to", help="Target format: agent.af, langchain, crewai")]
InputFile = Annotated[str, typer.Option("--input", "-i", help="Input file path")]
OutputFile = Annotated[str, typer.Option("--output", "-o", help="Output file path")]
Format = Annotated[str, typer.Option("--format", help="Output format: yaml, json")]


@app.command()
def load(
    input: Annotated[str, typer.Argument(help="Input .af file path")],
) -> None:
    try:
        agent = AgentPort.from_af(input)
        typer.echo(f"Loaded agent: {agent.metadata.name}")
        typer.echo(f"Model: {agent.state.model_config.provider.value}:{agent.state.model_config.model}")
        typer.echo(f"Tools: {len(agent.state.tools)}")
        typer.echo(f"Memory blocks: {len(agent.state.memory_blocks)}")
    except FileNotFoundError as e:
        raise typer.Exit(code=1, message=str(e))
    except ValidationError as e:
        raise typer.Exit(code=1, message=f"Validation error: {e}")


@app.command()
def save(
    input: Annotated[str, typer.Argument(help="Input .af file path")],
    output: Annotated[Optional[str], typer.Option("--output", "-o")] = None,
    format: Annotated[Optional[str], typer.Option("--format")] = "yaml",
) -> None:
    try:
        agent = AgentPort.from_af(input)
        output_path = output or input
        agent.to_af(output_path, format=format or "yaml")
        typer.echo(f"Saved to: {output_path}")
    except FileNotFoundError as e:
        raise typer.Exit(code=1, message=str(e))
    except ValidationError as e:
        raise typer.Exit(code=1, message=f"Validation error: {e}")


@app.command()
def validate(
    input: Annotated[str, typer.Argument(help="Input .af file path")],
) -> None:
    try:
        agent = AgentPort.from_af(input)
        is_valid, errors = agent.validate()
        if is_valid:
            typer.echo("✓ Agent is valid", err=False)
        else:
            typer.echo("✗ Agent validation failed:", err=True)
            for error in errors:
                typer.echo(f"  - {error}", err=True)
            raise typer.Exit(code=1)
    except FileNotFoundError as e:
        raise typer.Exit(code=1, message=str(e))


@app.command()
def convert(
    input: Annotated[str, typer.Argument(help="Input file path")],
    from_format: ConvertFrom,
    to_format: ConvertTo,
    output: OutputFile = None,
) -> None:
    try:
        if from_format == "letta":
            agent = AgentPort.from_af(input)
        elif from_format == "langchain":
            agent = _convert_from_langchain(input)
        elif from_format == "crewai":
            agent = _convert_from_crewai(input)
        else:
            raise typer.Exit(code=1, message=f"Unsupported source format: {from_format}")

        if to_format == "agent.af":
            output_path = output or input.replace(".json", ".af").replace(".yaml", ".af")
            agent.to_af(output_path)
            typer.echo(f"Converted to: {output_path}")
        elif to_format == "langchain":
            _convert_to_langchain(agent, output or "agent_langchain.json")
        elif to_format == "crewai":
            _convert_to_crewai(agent, output or "agent_crewai.json")
        else:
            raise typer.Exit(code=1, message=f"Unsupported target format: {to_format}")

        typer.echo(f"✓ Converted from {from_format} to {to_format}")
    except FileNotFoundError as e:
        raise typer.Exit(code=1, message=str(e))
    except Exception as e:
        raise typer.Exit(code=1, message=f"Conversion error: {e}")


def _convert_from_langchain(file_path: str) -> AgentPort:
    import json

    with open(file_path) as f:
        data = json.load(f)

    from agentport.schema import ModelConfig, ModelProvider

    model = data.get("model", "gpt-4")
    provider = ModelProvider.OPENAI if "gpt" in model else ModelProvider.ANTHROPIC

    config = ModelConfig(provider=provider, model=model)

    return AgentPort(
        name=data.get("name", "langchain-agent"),
        system_prompt=data.get("system_message", "You are a helpful agent."),
        model_config=config,
    )


def _convert_from_crewai(file_path: str) -> AgentPort:
    import json

    with open(file_path) as f:
        data = json.load(f)

    from agentport.schema import ModelConfig, ModelProvider

    model = data.get("model", {}).get("model_name", "gpt-4")
    provider = ModelProvider.OPENAI if "gpt" in model else ModelProvider.ANTHROPIC

    config = ModelConfig(provider=provider, model=model)

    return AgentPort(
        name=data.get("name", "crewai-agent"),
        system_prompt=data.get("goal", "Complete tasks."),
        model_config=config,
    )


def _convert_to_langchain(agent: AgentPort, output_path: str) -> None:
    import json

    data = {
        "name": agent.metadata.name,
        "system_message": agent.state.system_prompt,
        "model": agent.state.model_config.model,
    }

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)


def _convert_to_crewai(agent: AgentPort, output_path: str) -> None:
    import json

    data = {
        "name": agent.metadata.name,
        "goal": agent.state.system_prompt,
        "model": {
            "model_name": agent.state.model_config.model,
            "provider": agent.state.model_config.provider.value,
        },
    }

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)


@app.command()
def info(
    input: Annotated[str, typer.Argument(help="Input .af file path")],
) -> None:
    try:
        agent = AgentPort.from_af(input)

        typer.echo(f"Agent: {agent.metadata.name}")
        if agent.metadata.description:
            typer.echo(f"Description: {agent.metadata.description}")
        typer.echo(f"Version: {agent.metadata.version}")
        typer.echo(f"Author: {agent.metadata.author or 'N/A'}")
        typer.echo(f"Created: {agent.metadata.created_at}")
        typer.echo(f"Updated: {agent.metadata.updated_at}")
        typer.echo()
        typer.echo(f"Model: {agent.state.model_config.provider.value}:{agent.state.model_config.model}")
        typer.echo(f"Temperature: {agent.state.model_config.temperature}")
        typer.echo()
        typer.echo(f"Tools: {len(agent.state.tools)}")
        for tool in agent.state.tools:
            typer.echo(f"  - {tool.name}: {tool.description}")
        typer.echo()
        typer.echo(f"Memory blocks: {len(agent.state.memory_blocks)}")
        for block in agent.state.memory_blocks:
            typer.echo(f"  - {block.label}: {block.text[:50]}...")
        typer.echo()
        typer.echo(f"Messages: {len(agent.state.message_history)}")
        typer.echo(f"Environment vars: {len(agent.state.env_vars)}")

    except FileNotFoundError as e:
        raise typer.Exit(code=1, message=str(e))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
