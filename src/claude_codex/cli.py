"""claude-codex CLI entry point."""

from __future__ import annotations

import asyncio

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from claude_codex import __version__

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="claude-codex")
def main() -> None:
    """claude-codex: Cross-vendor adversarial AI code verification engine."""
    pass


@main.command()
@click.argument("task")
@click.option("--rounds", "-r", default=1, help="Number of adversarial rounds")
@click.option("--target", "-t", default=".", help="Target directory")
def adversarial(task: str, rounds: int, target: str) -> None:
    """Run adversarial code synthesis (build/attack/fuzz cycle)."""
    console.print(Panel(f"[bold]Adversarial Synthesis[/bold]: {task}", style="red"))
    console.print(f"[dim]Rounds: {rounds} | Target: {target}[/dim]")
    asyncio.run(_run_strategy("adversarial", task, rounds=rounds))


@main.command()
@click.argument("task")
def consensus(task: str) -> None:
    """Run consensus mode (compare Claude vs Codex output)."""
    console.print(Panel(f"[bold]Consensus Mode[/bold]: {task}", style="blue"))
    asyncio.run(_run_strategy("consensus", task))


@main.command()
@click.argument("task")
@click.option("--preset", "-p", default="standard",
              type=click.Choice(["trivial", "standard", "security", "performance", "full", "audit"]))
def auto(task: str, preset: str) -> None:
    """Auto-select the best strategy for the task."""
    console.print(Panel(f"[bold]Auto Mode[/bold] ({preset}): {task}", style="green"))
    console.print("[dim]Adaptive routing coming in v0.5.0. Using consensus.[/dim]")
    asyncio.run(_run_strategy("consensus", task))


@main.command(name="verify-deps")
@click.argument("path")
def verify_deps(path: str) -> None:
    """Verify supply chain safety of dependencies."""
    console.print(Panel(f"[bold]Supply Chain Verification[/bold]: {path}", style="yellow"))
    console.print("[dim]Coming in v1.0.0[/dim]")


@main.command(name="security-audit")
@click.option("--compliance", "-c", multiple=True, help="Compliance frameworks (soc2, hipaa, pci-dss)")
@click.option("--target", "-t", default=".", help="Target directory")
def security_audit(compliance: tuple[str, ...], target: str) -> None:
    """Run a full security audit."""
    console.print(Panel(f"[bold]Security Audit[/bold]: {target}", style="yellow"))
    console.print(f"[dim]Compliance: {', '.join(compliance) or 'general'}[/dim]")
    console.print("[dim]Coming in v1.0.0[/dim]")


async def _run_strategy(strategy_name: str, task: str, **kwargs) -> None:
    """Run a named strategy through the engine."""
    from claude_codex.core.engine import DualEngine

    engine = DualEngine()

    if strategy_name == "adversarial":
        from claude_codex.strategies.adversarial import Adversarial
        strategy = Adversarial(rounds=kwargs.get("rounds", 1))
    else:
        from claude_codex.strategies.consensus import Consensus
        strategy = Consensus()

    try:
        result = await engine.run(strategy, task=task)
        _print_result(result)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[dim]Ensure API keys are configured. Run: claude-codex --help[/dim]")


def _print_result(result) -> None:
    """Pretty-print a pipeline result."""
    table = Table(title="claude-codex Confidence Report", show_lines=True)
    table.add_column("Check", style="cyan", width=25)
    table.add_column("Status", style="green", width=15)

    c = result.confidence
    table.add_row("Architecture preserved", "[green]OK[/green]" if c.architecture_preserved else "[red]FAIL[/red]")
    table.add_row("Tests passing", "[green]OK[/green]" if c.tests_passing else "[red]FAIL[/red]")
    table.add_row("Vulnerabilities", f"[green]{c.vulnerabilities_found}[/green]" if c.vulnerabilities_found == 0 else f"[red]{c.vulnerabilities_found}[/red]")
    table.add_row("Dependencies verified", "[green]OK[/green]" if c.dependencies_verified else "[yellow]SKIP[/yellow]")
    table.add_row("OWASP clean", "[green]OK[/green]" if c.owasp_clean else "[red]FAIL[/red]")
    table.add_row("Models consulted", str(c.models_consulted))
    table.add_row("Cross-vendor agreement", f"{c.cross_vendor_agreement:.0%}")
    table.add_row("Confidence Score", f"[bold]{c.score}/100[/bold]")

    console.print(table)

    if result.code:
        console.print("\n[bold]Output:[/bold]")
        console.print(result.code[:1000])


if __name__ == "__main__":
    main()
