from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

from agentport import AgentPort, ValidationError
from agentport.converters import to_json, from_json

app = typer.Typer(
    name="agentport",
    help="Portable AI agents: Letta .af format support, cross-framework migration",
    add_completion=False,
)


@app.command()
def export(
    path: Annotated[str, typer.Argument(help="Input .af file path")],
    format: Annotated[Optional[str], typer.Option("--format", "-f", help="Output format: yaml, json")] = "yaml",
    output: Annotated[Optional[str], typer.Option("--output", "-o", help="Output file path")] = None,
) -> None:
    """Export an agent file to specified format."""
    try:
        file_path = Path(path)
        if not file_path.exists():
            raise typer.Exit(code=1, message=f"File not found: {path}")

        agent = AgentPort.from_af(file_path)

        if format not in ("yaml", "json"):
            raise typer.Exit(code=1, message="Format must be 'yaml' or 'json'")

        output_path = output or file_path.with_suffix(f".{format}")
        if format == "yaml":
            content = agent.to_af(output_path, format="yaml")
        else:
            content = to_json(agent)
            output_path.write_text(content, encoding="utf-8")

        typer.echo(f"✓ Exported to: {output_path}")

    except FileNotFoundError as e:
        raise typer.Exit(code=1, message=str(e))
    except ValidationError as e:
        raise typer.Exit(code=1, message=f"Validation error: {e}")
    except Exception as e:
        raise typer.Exit(code=1, message=f"Export failed: {e}")


@app.command()
def import_(
    af_file: Annotated[str, typer.Argument(help="Input .af file path")],
    to_format: Annotated[Optional[str], typer.Option("--to", "-t", help="Target format: json, yaml")] = None,
    output: Annotated[Optional[str], typer.Option("--output", "-o", help="Output file path")] = None,
) -> None:
    """Import an .af file and optionally convert to another format."""
    try:
        file_path = Path(af_file)
        if not file_path.exists():
            raise typer.Exit(code=1, message=f"File not found: {af_file}")

        agent = AgentPort.from_af(file_path)

        if to_format is None:
            typer.echo(f"✓ Loaded agent: {agent.metadata.name}")
            typer.echo(f"  Model: {agent.state.llm_model_config.provider.value}:{agent.state.llm_model_config.model}")
            typer.echo(f"  Tools: {len(agent.state.tools)}")
            return

        if to_format not in ("json", "yaml"):
            raise typer.Exit(code=1, message="Target format must be 'json' or 'yaml'")

        output_path = output or file_path.with_suffix(f".{to_format}")

        if to_format == "json":
            content = to_json(agent)
            output_path.write_text(content, encoding="utf-8")
        else:
            agent.to_af(output_path, format="yaml")

        typer.echo(f"✓ Converted to: {output_path}")

    except FileNotFoundError as e:
        raise typer.Exit(code=1, message=str(e))
    except ValidationError as e:
        raise typer.Exit(code=1, message=f"Validation error: {e}")
    except Exception as e:
        raise typer.Exit(code=1, message=f"Import failed: {e}")


@app.command()
def validate(
    path: Annotated[str, typer.Argument(help="Input .af file path")],
) -> None:
    """Validate an agent file schema."""
    try:
        file_path = Path(path)
        if not file_path.exists():
            raise typer.Exit(code=1, message=f"File not found: {path}")

        agent = AgentPort.from_af(file_path)
        is_valid, errors = agent.validate()

        if is_valid:
            typer.secho("✓ Agent is valid", fg=typer.colors.GREEN)
            typer.echo(f"  Name: {agent.metadata.name}")
            typer.echo(f"  Model: {agent.state.llm_model_config.provider.value}:{agent.state.llm_model_config.model}")
            typer.echo(f"  Tools: {len(agent.state.tools)}")
            typer.echo(f"  Memory blocks: {len(agent.state.memory_blocks)}")
        else:
            typer.secho("✗ Agent validation failed", fg=typer.colors.RED)
            for error in errors:
                typer.echo(f"  - {error}")
            raise typer.Exit(code=1)

    except FileNotFoundError as e:
        raise typer.Exit(code=1, message=str(e))
    except ValidationError as e:
        raise typer.Exit(code=1, message=f"Validation error: {e}")
    except Exception as e:
        raise typer.Exit(code=1, message=f"Validation failed: {e}")


@app.command()
def info(
    path: Annotated[str, typer.Argument(help="Input .af file path")],
) -> None:
    """Show detailed information about an agent file."""
    try:
        file_path = Path(path)
        if not file_path.exists():
            raise typer.Exit(code=1, message=f"File not found: {path}")

        agent = AgentPort.from_af(file_path)

        typer.echo(typer.style("Agent Information", bold=True))
        typer.echo(f"  Name: {agent.metadata.name}")
        if agent.metadata.description:
            typer.echo(f"  Description: {agent.metadata.description}")
        typer.echo(f"  Version: {agent.metadata.version}")
        typer.echo(f"  Author: {agent.metadata.author or 'N/A'}")
        typer.echo(f"  Tags: {', '.join(agent.metadata.tags) or 'None'}")
        typer.echo(f"  Created: {agent.metadata.created_at}")
        typer.echo(f"  Updated: {agent.metadata.updated_at}")

        typer.echo()
        typer.echo(typer.style("Model Configuration", bold=True))
        typer.echo(f"  Provider: {agent.state.llm_model_config.provider.value}")
        typer.echo(f"  Model: {agent.state.llm_model_config.model}")
        typer.echo(f"  Temperature: {agent.state.llm_model_config.temperature}")
        if agent.state.llm_model_config.max_tokens:
            typer.echo(f"  Max tokens: {agent.state.llm_model_config.max_tokens}")

        if agent.state.tools:
            typer.echo()
            typer.echo(typer.style(f"Tools ({len(agent.state.tools)})", bold=True))
            for tool in agent.state.tools:
                status = "✓" if tool.enabled else "✗"
                typer.echo(f"  {status} {tool.name}: {tool.description[:50]}...")

        if agent.state.memory_blocks:
            typer.echo()
            typer.echo(typer.style(f"Memory Blocks ({len(agent.state.memory_blocks)})", bold=True))
            for block in agent.state.memory_blocks:
                status = "✓" if block.enabled else "✗"
                in_context = "📚" if block.in_context else "📦"
                typer.echo(f"  {status} {in_context} {block.label}: {block.text[:40]}...")

        if agent.state.env_vars:
            typer.echo()
            typer.echo(typer.style(f"Environment Variables ({len(agent.state.env_vars)})", bold=True))
            for env in agent.state.env_vars:
                secret = "🔒" if env.secret else "🔓"
                typer.echo(f"  {secret} {env.name}")

    except FileNotFoundError as e:
        raise typer.Exit(code=1, message=str(e))
    except Exception as e:
        raise typer.Exit(code=1, message=f"Failed to load agent: {e}")


@app.command()
def convert(
    path: Annotated[str, typer.Argument(help="Input file path")],
    from_format: Annotated[str, typer.Option("--from", help="Source format: letta, langchain, crewai")],
    to_format: Annotated[str, typer.Option("--to", help="Target format: agent.af, langchain, crewai")],
    output: Annotated[Optional[str], typer.Option("--output", "-o", help="Output file path")] = None,
) -> None:
    """Convert between different agent formats."""
    try:
        if from_format == "letta":
            agent = AgentPort.from_af(path)
        elif from_format == "langchain":
            with open(path) as f:
                import json
                data = json.load(f)
            from agentport.schema import ModelConfig, ModelProvider
            config = ModelConfig(
                provider=ModelProvider.OPENAI if "gpt" in data.get("model", "") else ModelProvider.ANTHROPIC,
                model=data.get("model", "gpt-4")
            )
            agent = AgentPort(
                name=data.get("name", "langchain-agent"),
                system_prompt=data.get("system_message", "You are a helpful agent."),
                model_config=config,
            )
        elif from_format == "crewai":
            with open(path) as f:
                import json
                data = json.load(f)
            from agentport.schema import ModelConfig, ModelProvider
            config = ModelConfig(
                provider=ModelProvider.OPENAI if "gpt" in data.get("model", {}).get("model_name", "") else ModelProvider.ANTHROPIC,
                model=data.get("model", {}).get("model_name", "gpt-4")
            )
            agent = AgentPort(
                name=data.get("name", "crewai-agent"),
                system_prompt=data.get("goal", "Complete tasks."),
                model_config=config,
            )
        else:
            raise typer.Exit(code=1, message=f"Unsupported source format: {from_format}")

        if to_format == "agent.af":
            output_path = output or Path(path).with_suffix(".af")
            agent.to_af(output_path)
        elif to_format == "langchain":
            output_path = output or Path(path).stem + "_langchain.json"
            import json
            data = {
                "name": agent.metadata.name,
                "system_message": agent.state.system_prompt,
                "model": agent.state.llm_model_config.model,
            }
            with open(output_path, "w") as f:
                json.dump(data, f, indent=2)
        elif to_format == "crewai":
            output_path = output or Path(path).stem + "_crewai.json"
            import json
            data = {
                "name": agent.metadata.name,
                "goal": agent.state.system_prompt,
                "model": {
                    "model_name": agent.state.llm_model_config.model,
                    "provider": agent.state.llm_model_config.provider.value,
                },
            }
            with open(output_path, "w") as f:
                json.dump(data, f, indent=2)
        else:
            raise typer.Exit(code=1, message=f"Unsupported target format: {to_format}")

        typer.secho(f"✓ Converted from {from_format} to {to_format}", fg=typer.colors.GREEN)
        typer.echo(f"  Output: {output_path}")

    except FileNotFoundError as e:
        raise typer.Exit(code=1, message=str(e))
    except Exception as e:
        raise typer.Exit(code=1, message=f"Conversion failed: {e}")


@app.command()
def migrate(
    path: Annotated[str, typer.Argument(help="Input agent file path")],
    from_format: Annotated[str, typer.Option("--from", "-f", help="Source format: letta, openclaw")] = "letta",
    to_format: Annotated[str, typer.Option("--to", "-t", help="Target format: letta, openclaw")] = "openclaw",
    output: Annotated[Optional[str], typer.Option("--output", "-o", help="Output file path")] = None,
) -> None:
    """Migrate agents between frameworks (Letta <-> OpenClaw)."""
    try:
        from rich.console import Console
        from rich.table import Table

        console = Console()

        file_path = Path(path)
        if not file_path.exists():
            raise typer.Exit(code=1, message=f"File not found: {path}")

        from agentport.converters import (
            from_openclaw_file,
            from_letta_to_openclaw,
            to_openclaw_file,
        )

        if from_format == "letta" and to_format == "openclaw":
            agent = AgentPort.from_af(file_path)
            openclaw = from_letta_to_openclaw(agent)
            
            output_path = Path(output) if output else file_path.with_suffix(".openclaw.json")
            content = __import__("json").dumps(openclaw.to_dict(), indent=2, ensure_ascii=False)
            output_path.write_text(content, encoding="utf-8")
            
            table = Table(title="Migration: Letta → OpenClaw")
            table.add_column("Property", style="cyan")
            table.add_column("Letta (.af)", style="yellow")
            table.add_column("OpenClaw (JSON)", style="green")
            
            table.add_row("Name", agent.metadata.name, openclaw.name or agent.metadata.name)
            table.add_row("Tools", str(len(agent.state.tools)), str(len(openclaw.skills)))
            table.add_row("Memory Blocks", str(len(agent.state.memory_blocks)), str(len(openclaw.memory)))
            table.add_row("Model", agent.state.llm_model_config.model, openclaw.settings.get("llm", {}).get("model", "N/A"))
            
            console.print(table)
            console.print(f"\n✓ Migrated to: {output_path}")

        elif from_format == "openclaw" and to_format == "letta":
            agent = from_openclaw_file(file_path)
            
            output_path = Path(output) if output else file_path.with_suffix(".af")
            agent.to_af(output_path, format="yaml")
            
            table = Table(title="Migration: OpenClaw → Letta")
            table.add_column("Property", style="cyan")
            table.add_column("OpenClaw (JSON)", style="yellow")
            table.add_column("Letta (.af)", style="green")
            
            oc_data = __import__("json").loads(file_path.read_text(encoding="utf-8"))
            
            table.add_row("Name", oc_data.get("name", "N/A"), agent.metadata.name)
            table.add_row("Skills", str(len(oc_data.get("skills", []))), str(len(agent.state.tools)))
            table.add_row("Memory", str(len(oc_data.get("memory", []))), str(len(agent.state.memory_blocks)))
            table.add_row("Model", oc_data.get("settings", {}).get("llm", {}).get("model", "N/A"), agent.state.llm_model_config.model)
            
            console.print(table)
            console.print(f"\n✓ Migrated to: {output_path}")

        else:
            raise typer.Exit(code=1, message="Supported migrations: letta->openclaw, openclaw->letta")

    except FileNotFoundError as e:
        raise typer.Exit(code=1, message=str(e))
    except Exception as e:
        raise typer.Exit(code=1, message=f"Migration failed: {e}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()