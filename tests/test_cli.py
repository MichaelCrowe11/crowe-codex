from click.testing import CliRunner
from claude_codex.cli import main


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "adversarial" in result.output
    assert "consensus" in result.output


def test_cli_adversarial_help():
    runner = CliRunner()
    result = runner.invoke(main, ["adversarial", "--help"])
    assert result.exit_code == 0
    assert "rounds" in result.output


def test_cli_consensus_help():
    runner = CliRunner()
    result = runner.invoke(main, ["consensus", "--help"])
    assert result.exit_code == 0


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
