"""crowe-codex CLI entry point."""

from __future__ import annotations

import asyncio

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from crowe_codex import __version__

console = Console()

STRATEGY_NAMES = [
    "adversarial",
    "consensus",
    "verification_loop",
    "pipeline",
    "cognitive_mesh",
    "evolutionary",
    "adaptive_router",
]


@click.group()
@click.version_option(version=__version__, prog_name="crowe-codex")
def main() -> None:
    """crowe-codex: Cross-vendor adversarial AI code verification engine."""
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
@click.option("--iterations", "-i", default=2, help="Number of verify iterations")
def verify(task: str, iterations: int) -> None:
    """Run verification loop (code/test cross-verification)."""
    console.print(Panel(f"[bold]Verification Loop[/bold]: {task}", style="cyan"))
    console.print(f"[dim]Iterations: {iterations}[/dim]")
    asyncio.run(_run_strategy("verification_loop", task, iterations=iterations))


@main.command()
@click.argument("task")
def pipeline(task: str) -> None:
    """Run sequential pipeline (architect -> build -> review -> dispatch)."""
    console.print(Panel(f"[bold]Pipeline Mode[/bold]: {task}", style="magenta"))
    asyncio.run(_run_strategy("pipeline", task))


@main.command()
@click.argument("task")
def mesh(task: str) -> None:
    """Run cognitive mesh (all agents in parallel, merge best parts)."""
    console.print(Panel(f"[bold]Cognitive Mesh[/bold]: {task}", style="yellow"))
    asyncio.run(_run_strategy("cognitive_mesh", task))


@main.command()
@click.argument("task")
@click.option("--population", "-p", default=3, help="Population size per generation")
@click.option("--generations", "-g", default=2, help="Number of generations")
def evolve(task: str, population: int, generations: int) -> None:
    """Run evolutionary generation (breed best code candidates)."""
    console.print(Panel(f"[bold]Evolutionary Generation[/bold]: {task}", style="green"))
    console.print(f"[dim]Population: {population} | Generations: {generations}[/dim]")
    asyncio.run(_run_strategy("evolutionary", task, population=population, generations=generations))


@main.command()
@click.argument("task")
@click.option("--preset", "-p", default="standard",
              type=click.Choice(["trivial", "standard", "security", "performance", "full", "audit"]))
def auto(task: str, preset: str) -> None:
    """Auto-select the best strategy for the task (adaptive routing)."""
    console.print(Panel(f"[bold]Auto Mode[/bold] ({preset}): {task}", style="green"))
    asyncio.run(_run_strategy("adaptive_router", task))


@main.command(name="verify-deps")
@click.argument("deps", nargs=-1, required=True)
@click.option("--ecosystem", "-e", default="pypi", help="Package ecosystem (pypi, npm)")
def verify_deps(deps: tuple[str, ...], ecosystem: str) -> None:
    """Verify supply chain safety of dependencies."""
    console.print(Panel("[bold]Supply Chain Verification[/bold]", style="yellow"))
    console.print(f"[dim]Checking {len(deps)} dependencies ({ecosystem})[/dim]")
    asyncio.run(_run_supply_chain(list(deps), ecosystem))


@main.command(name="security-audit")
@click.argument("code_or_file")
@click.option("--compliance", "-c", multiple=True, help="Compliance frameworks (soc2, hipaa, pci_dss)")
@click.option("--owasp/--no-owasp", default=True, help="Run OWASP Top 10 scan")
@click.option("--threats/--no-threats", default=True, help="Run threat modeling")
def security_audit(
    code_or_file: str, compliance: tuple[str, ...],
    owasp: bool, threats: bool,
) -> None:
    """Run a full security audit on code or a file."""
    console.print(Panel("[bold]Security Audit[/bold]", style="yellow"))
    console.print(f"[dim]OWASP: {'ON' if owasp else 'OFF'} | Threats: {'ON' if threats else 'OFF'} | Compliance: {', '.join(compliance) or 'general'}[/dim]")
    asyncio.run(_run_security_audit(code_or_file, list(compliance), owasp, threats))


async def _run_supply_chain(deps: list[str], ecosystem: str) -> None:
    """Run supply chain verification."""
    from crowe_codex.core.engine import DualEngine
    from crowe_codex.security.supply_chain import SupplyChainVerifier

    engine = DualEngine()
    try:
        verifier = SupplyChainVerifier(engine._agents)
        result = await verifier.verify(deps, ecosystem)
        console.print(f"\n[bold]{result.summary}[/bold]")
        for dep in result.dependencies:
            status = "[green]SAFE[/green]" if dep.risk_level == "safe" else f"[red]{dep.risk_level.upper()}[/red]"
            console.print(f"  {dep.name}: {status}")
        if result.slopsquatting_suspects:
            console.print(f"\n[red]Slopsquatting suspects: {', '.join(result.slopsquatting_suspects)}[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


async def _run_security_audit(
    code_or_file: str, compliance_frameworks: list[str],
    run_owasp: bool, run_threats: bool,
) -> None:
    """Run a comprehensive security audit."""
    from pathlib import Path
    from crowe_codex.core.engine import DualEngine
    from crowe_codex.security.attestation import AttestationGenerator

    # Read code from file or use as literal
    code = code_or_file
    if Path(code_or_file).exists():
        code = Path(code_or_file).read_text()

    engine = DualEngine()
    agents = engine._agents
    owasp_report = None
    threat_model = None
    compliance_report = None

    try:
        if run_owasp and agents:
            from crowe_codex.security.owasp import OWASPScanner
            scanner = OWASPScanner(agents)
            owasp_report = await scanner.scan(code)
            console.print(f"[bold]{owasp_report.summary}[/bold]")

        if run_threats and agents:
            from crowe_codex.security.threat_model import ThreatModelEngine
            threat_engine = ThreatModelEngine(agents)
            threat_model = await threat_engine.analyze(code)
            console.print(f"[bold]{threat_model.summary}[/bold]")

        if compliance_frameworks and agents:
            from crowe_codex.security.compliance import ComplianceMapper
            mapper = ComplianceMapper(agents)
            compliance_report = await mapper.assess(code, frameworks=compliance_frameworks)
            console.print(f"[bold]{compliance_report.summary}[/bold]")

        gen = AttestationGenerator()
        attestation = gen.generate(
            code=code,
            owasp=owasp_report,
            threat_model=threat_model,
            compliance=compliance_report,
            agents_used=list(agents.keys()),
            strategy="security_audit",
        )

        # Print attestation report
        table = Table(title="Security Attestation", show_lines=True)
        table.add_column("Check", style="cyan", width=25)
        table.add_column("Result", style="green", width=30)

        table.add_row("Overall Score", f"[bold]{attestation.overall_score}/100[/bold]")
        table.add_row("Verdict", f"[bold]{attestation.verdict}[/bold]")

        if owasp_report:
            table.add_row("OWASP Clean", "[green]YES[/green]" if owasp_report.is_clean else f"[red]NO ({owasp_report.vulnerability_count} issues)[/red]")
        if threat_model:
            table.add_row("Threats", f"{len(threat_model.threats)} ({len(threat_model.critical_threats)} critical)")
        if compliance_report:
            table.add_row("Compliance", f"{compliance_report.pass_rate:.0%} pass rate")

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[dim]Ensure API keys are configured. Run: crowe-codex --help[/dim]")


@main.command()
def strategies() -> None:
    """List all available strategies."""
    table = Table(title="Available Strategies", show_lines=True)
    table.add_column("Strategy", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("CLI Command", style="green")

    rows = [
        ("adversarial", "Build/attack/fuzz cycles with cross-vendor verification", "adversarial"),
        ("consensus", "Same task through multiple agents, compare and merge", "consensus"),
        ("verification_loop", "One writes code, another writes tests, cross-verify", "verify"),
        ("pipeline", "Sequential handoff: architect -> build -> review -> dispatch", "pipeline"),
        ("cognitive_mesh", "All agents in parallel, dispatch merges best parts", "mesh"),
        ("evolutionary", "Multiple candidates, fitness-scored, breed best traits", "evolve"),
        ("adaptive_router", "Learns which strategy works best per task type", "auto"),
    ]
    for name, desc, cmd in rows:
        table.add_row(name, desc, cmd)

    console.print(table)


async def _run_strategy(strategy_name: str, task: str, **kwargs) -> None:
    """Run a named strategy through the engine."""
    from crowe_codex.core.engine import DualEngine

    engine = DualEngine()
    strategy = _build_strategy(strategy_name, **kwargs)

    try:
        result = await engine.run(strategy, task=task)
        _print_result(result)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[dim]Ensure API keys are configured. Run: crowe-codex --help[/dim]")


def _build_strategy(name: str, **kwargs):
    """Instantiate a strategy by name."""
    if name == "adversarial":
        from crowe_codex.strategies.adversarial import Adversarial
        return Adversarial(rounds=kwargs.get("rounds", 1))
    elif name == "verification_loop":
        from crowe_codex.strategies.verification import VerificationLoop
        return VerificationLoop(iterations=kwargs.get("iterations", 2))
    elif name == "pipeline":
        from crowe_codex.strategies.pipeline_strategy import Pipeline
        return Pipeline()
    elif name == "cognitive_mesh":
        from crowe_codex.strategies.mesh import CognitiveMesh
        return CognitiveMesh()
    elif name == "evolutionary":
        from crowe_codex.strategies.evolutionary import Evolutionary
        return Evolutionary(
            population=kwargs.get("population", 3),
            generations=kwargs.get("generations", 2),
        )
    elif name == "adaptive_router":
        from crowe_codex.strategies.router import AdaptiveRouter
        from crowe_codex.strategies.adversarial import Adversarial
        from crowe_codex.strategies.consensus import Consensus
        from crowe_codex.strategies.verification import VerificationLoop
        from crowe_codex.strategies.mesh import CognitiveMesh
        from crowe_codex.strategies.evolutionary import Evolutionary
        from crowe_codex.strategies.pipeline_strategy import Pipeline

        router = AdaptiveRouter(strategies={
            "adversarial": Adversarial(),
            "consensus": Consensus(),
            "verification_loop": VerificationLoop(),
            "pipeline": Pipeline(),
            "cognitive_mesh": CognitiveMesh(),
            "evolutionary": Evolutionary(),
        })
        return router
    else:
        from crowe_codex.strategies.consensus import Consensus
        return Consensus()


def _print_result(result) -> None:
    """Pretty-print a pipeline result."""
    table = Table(title="crowe-codex Confidence Report", show_lines=True)
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
