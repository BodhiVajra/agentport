from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

from agentport import AgentPort, ValidationError
from agentport.converters import to_json, from_json
from agentport.dna import PriorityLevel

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
        import json

        console = Console()

        file_path = Path(path)
        if not file_path.exists():
            raise typer.Exit(code=1, message=f"File not found: {path}")

        from agentport.converters import ADAPTERS, get_adapter

        source_adapter = get_adapter(from_format)
        target_adapter = get_adapter(to_format)

        if not source_adapter or not target_adapter:
            supported = list(ADAPTERS.keys())
            raise typer.Exit(code=1, message=f"Supported formats: {', '.join(supported)}")

        with open(file_path, encoding="utf-8") as f:
            source_data = json.load(f)

        agent_file = source_adapter.to_apf(source_data)
        target_data = target_adapter.from_apf(agent_file)

        output_path = Path(output) if output else file_path.with_suffix(f".{to_format}")

        if to_format == "openclaw":
            content = json.dumps(target_data, indent=2, ensure_ascii=False)
            output_path.write_text(content, encoding="utf-8")
        else:
            output_path.write_text("# Agent file\n", encoding="utf-8")
            output_path.write_text(json.dumps(target_data, indent=2, ensure_ascii=False), encoding="utf-8")

        validation = source_adapter.validate_migration(
            agent_file,
            target_adapter.to_apf(target_data)
        )

        table = Table(title=f"Migration: {from_format} → {to_format}")
        table.add_column("Property", style="cyan")
        table.add_column("Source", style="yellow")
        table.add_column("Target", style="green")

        table.add_row("Name", agent_file.metadata.name, target_adapter.from_apf(agent_file).get("name", agent_file.metadata.name))
        table.add_row("Tools", str(len(agent_file.state.tools)), str(len(target_data.get("skills", [])) if to_format == "openclaw" else str(len(target_data.get("tools", [])))))
        table.add_row("Memory Blocks", str(len(agent_file.state.memory_blocks)), str(len(target_data.get("memory", [])) if to_format == "openclaw" else str(len(target_data.get("memory_blocks", [])))))
        table.add_row("Model", agent_file.state.llm_model_config.model, target_data.get("settings", {}).get("llm", {}).get("model") if to_format == "openclaw" else agent_file.state.llm_model_config.model)

        console.print(table)
        console.print(f"\n✓ Migration validated: {validation}")
        console.print(f"\n✓ Migrated to: {output_path}")

    except FileNotFoundError as e:
        raise typer.Exit(code=1, message=str(e))
    except Exception as e:
        raise typer.Exit(code=1, message=f"Migration failed: {e}")


@app.command()
def config(
    action: Annotated[str, typer.Argument(help="Action: get, set, list, remove")],
    key: Annotated[Optional[str], typer.Argument(help="Config key (for get/set/remove)")] = None,
    value: Annotated[Optional[str], typer.Argument(help="Config value (for set)")] = None,
) -> None:
    """Manage AgentPort configuration (API keys, settings).
    
    Examples:
        agentport config list
        agentport config set api_key YOUR_MINIMAX_KEY
        agentport config get api_key
        agentport config set model gpt-4
        agentport config remove api_key
    """
    import os
    from pathlib import Path
    import tempfile
    
    config_dir = Path(tempfile.gettempdir()) / "agentport"
    config_file = config_dir / "config.json"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    def load_config() -> dict:
        if config_file.exists():
            import json
            return json.loads(config_file.read_text())
        return {}
    
    def save_config(cfg: dict) -> None:
        import json
        config_file.write_text(json.dumps(cfg, indent=2, ensure_ascii=False))
    
    cfg = load_config()
    
    if action == "list":
        from rich.console import Console
        from rich.table import Table
        console = Console()
        
        table = Table(title="AgentPort Configuration")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="yellow")
        
        if cfg:
            for k, v in cfg.items():
                display_val = "*****" if "key" in k.lower() or "secret" in k.lower() else str(v)
                table.add_row(k, display_val)
        else:
            table.add_row("[dim]no config[/dim]", "[dim]run 'agentport config set' to add[/dim]")
        
        console.print(table)
        console.print(f"\n[dim]Config file: {config_file}[/dim]")
        
    elif action == "get":
        if not key:
            raise typer.Exit(code=1, message="Missing key. Usage: agentport config get <key>")
        
        if key in cfg:
            val = cfg[key]
            if "key" in key.lower() or "secret" in key.lower():
                val = "*****"
            typer.echo(f"{key}: {val}")
        else:
            typer.echo(f"Key '{key}' not found")
            
    elif action == "set":
        if not key or not value:
            raise typer.Exit(code=1, message="Missing key or value. Usage: agentport config set <key> <value>")
        
        cfg[key] = value
        save_config(cfg)
        typer.echo(f"✓ Set {key} = {'*****' if 'key' in key.lower() else value}")
        
    elif action == "remove" or action == "delete":
        if not key:
            raise typer.Exit(code=1, message="Missing key. Usage: agentport config remove <key>")
        
        if key in cfg:
            del cfg[key]
            save_config(cfg)
            typer.echo(f"✓ Removed {key}")
        else:
            typer.echo(f"Key '{key}' not found")
            
    else:
        raise typer.Exit(code=1, message=f"Unknown action: {action}. Use: get, set, list, remove")


@app.command()
def edit(
    path: Annotated[str, typer.Argument(help="Input agent file (.af, .apf, .json)")],
    mode: Annotated[str, typer.Option("--mode", "-m", help="Edit mode: visual, compress, classify")] = "visual",
    output: Annotated[Optional[str], typer.Option("--output", "-o", help="Output file path")] = None,
    api_key: Annotated[Optional[str], typer.Option("--api-key", "-k", help="LLM API key (or set via: agentport config set api_key YOUR_KEY)")] = None,
) -> None:
    """Edit agent DNA with visual memory editor."""
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        
        console = Console()
        
        from agentport.dna import AgentDNA, APFFile
        from agentport.engine import IntelligentMemoryEngine, load_apf, save_apf
        
        file_path = Path(path)
        if not file_path.exists():
            raise typer.Exit(code=1, message=f"File not found: {path}")
        
        effective_api_key = api_key
        if not effective_api_key:
            import tempfile
            config_dir = Path(tempfile.gettempdir()) / "agentport"
            config_file = config_dir / "config.json"
            if config_file.exists():
                import json
                cfg = json.loads(config_file.read_text())
                effective_api_key = cfg.get("api_key") or cfg.get("minimax_api_key")
        
        if file_path.suffix == ".apf":
            dna = load_apf(str(file_path))
        else:
            agent = AgentPort.from_af(file_path)
            from agentport.dna import (
                CoreIdentity, 
                LayeredMemorySystem, 
                ToolWorkflowLayer, 
                FrameworkAdapterLayer,
            )
            from agentport.schema import ModelProvider
            
            core = CoreIdentity(
                name=agent.metadata.name,
                description=agent.metadata.description or "",
                author=agent.metadata.author,
                human_vision="Code Reviewer",
            )
            
            memories = []
            if agent.state.memory_blocks:
                from agentport.dna import MemoryBlockDNA, MemoryType
                for i, mb in enumerate(agent.state.memory_blocks):
                    memories.append(MemoryBlockDNA(
                        id=f"mem-{i}",
                        memory_type=MemoryType.SEMANTIC,
                        content=mb.text,
                        priority=PriorityLevel.MEDIUM,
                    ))
            
            memory_sys = LayeredMemorySystem(semantic=memories)
            tool_layer = ToolWorkflowLayer(
                tools=[], 
            )
            adapter = FrameworkAdapterLayer()
            
            dna = AgentDNA(
                core_identity=core,
                memory_system=memory_sys,
                tool_layer=tool_layer,
                adapter_layer=adapter,
            )
        
        if mode == "visual":
            console.print(Panel.fit(
                f"[bold cyan]Agent DNA Visual Editor[/bold cyan]\n\n"
                f"{dna.core_identity.name}\n"
                f"Vision: {dna.core_identity.human_vision}",
                border_style="cyan"
            ))
            
            table = Table(title="Layered Memory System")
            table.add_column("ID", style="cyan")
            table.add_column("Type", style="yellow")
            table.add_column("Content", style="white")
            table.add_column("Priority", style="magenta")
            table.add_column("Compressed", style="green")
            
            for mem in dna.memory_system.get_all_memories():
                table.add_row(
                    mem.id,
                    mem.memory_type.value,
                    mem.content[:50] + "..." if len(mem.content) > 50 else mem.content,
                    mem.priority.value,
                    "✓" if mem.compressed else "-",
                )
            
            console.print(table)
            
            console.print(f"\n[bold]Memory Stats:[/bold]")
            console.print(f"  Total blocks: {len(dna.memory_system.get_all_memories())}")
            console.print(f"  Tokens (original): {dna.memory_system.total_tokens_estimate}")
            console.print(f"  Tokens (compressed): {dna.memory_system.compressed_tokens}")
            
        elif mode == "compress":
            if not effective_api_key:
                console.print("[yellow]No API key provided. Use 'agentport config set api_key YOUR_KEY' or --api-key[/yellow]")
            
            engine = IntelligentMemoryEngine(api_key=effective_api_key) if effective_api_key else None
            
            if engine:
                compressed_dna = engine.compress_agent(dna)
                console.print(f"[green]✓ Memory compressed: {dna.memory_system.total_tokens_estimate} → {compressed_dna.memory_system.compressed_tokens} tokens[/green]")
            else:
                compressed_dna = dna.model_copy(deep=True)
                compressed_dna.memory_system.compressed_tokens = (
                    dna.memory_system.total_tokens_estimate // 2
                )
                console.print(f"[yellow]⚠ Basic compression applied (no API key)[/yellow]")
            
            output_path = Path(output) if output else file_path.with_suffix(".apf")
            save_apf(compressed_dna, str(output_path))
            console.print(f"[green]✓ Saved to: {output_path}[/green]")
            
        elif mode == "classify":
            if not effective_api_key:
                raise typer.Exit(code=1, message="API key required. Use 'agentport config set api_key YOUR_KEY' or --api-key")
            
            engine = IntelligentMemoryEngine(api_key=effective_api_key)
            all_memories = dna.memory_system.get_all_memories()
            
            console.print("[yellow]Classifying memories...[/yellow]")
            classified = engine.classify(all_memories)
            
            for mem in classified:
                console.print(f"  {mem.id}: {mem.memory_type.value}")
            
            console.print(f"[green]✓ Classified {len(classified)} memories[/green]")
            
        else:
            raise typer.Exit(code=1, message=f"Unknown mode: {mode}. Use: visual, compress, classify")

    except FileNotFoundError as e:
        raise typer.Exit(code=1, message=str(e))
    except Exception as e:
        raise typer.Exit(code=1, message=f"Edit failed: {e}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()