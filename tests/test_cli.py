from click.testing import CliRunner
from crowe_codex.cli import main


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "1.0.0" in result.output


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "adversarial" in result.output
    assert "consensus" in result.output
    assert "verify" in result.output
    assert "pipeline" in result.output
    assert "mesh" in result.output
    assert "evolve" in result.output
    assert "auto" in result.output
    assert "strategies" in result.output


def test_cli_adversarial_help():
    runner = CliRunner()
    result = runner.invoke(main, ["adversarial", "--help"])
    assert result.exit_code == 0
    assert "rounds" in result.output


def test_cli_consensus_help():
    runner = CliRunner()
    result = runner.invoke(main, ["consensus", "--help"])
    assert result.exit_code == 0


def test_cli_verify_help():
    runner = CliRunner()
    result = runner.invoke(main, ["verify", "--help"])
    assert result.exit_code == 0
    assert "iterations" in result.output


def test_cli_pipeline_help():
    runner = CliRunner()
    result = runner.invoke(main, ["pipeline", "--help"])
    assert result.exit_code == 0


def test_cli_mesh_help():
    runner = CliRunner()
    result = runner.invoke(main, ["mesh", "--help"])
    assert result.exit_code == 0


def test_cli_evolve_help():
    runner = CliRunner()
    result = runner.invoke(main, ["evolve", "--help"])
    assert result.exit_code == 0
    assert "population" in result.output
    assert "generations" in result.output


def test_cli_auto_help():
    runner = CliRunner()
    result = runner.invoke(main, ["auto", "--help"])
    assert result.exit_code == 0
    assert "preset" in result.output


def test_cli_verify_deps_help():
    runner = CliRunner()
    result = runner.invoke(main, ["verify-deps", "--help"])
    assert result.exit_code == 0


def test_cli_security_audit_help():
    runner = CliRunner()
    result = runner.invoke(main, ["security-audit", "--help"])
    assert result.exit_code == 0
    assert "compliance" in result.output


def test_cli_strategies_list():
    runner = CliRunner()
    result = runner.invoke(main, ["strategies"])
    assert result.exit_code == 0
    assert "adversarial" in result.output
    assert "consensus" in result.output
    assert "verification_loop" in result.output
    assert "pipeline" in result.output
    assert "cognitive_mesh" in result.output
    assert "evolutionary" in result.output
    assert "adaptive_router" in result.output
