from claude_codex.core.agent import AgentConfig
from claude_codex.core.claude_agent import ClaudeAgent


def test_claude_agent_instantiation():
    agent = ClaudeAgent(
        config=AgentConfig(
            name="claude",
            provider="anthropic",
            model="claude-opus-4-6",
            api_key="sk-test",
        )
    )
    assert agent.config.name == "claude"
    assert agent.config.model == "claude-opus-4-6"


def test_claude_agent_default_model():
    agent = ClaudeAgent(
        config=AgentConfig(name="claude", provider="anthropic", api_key="sk-test")
    )
    assert agent.model == "claude-opus-4-6"


def test_claude_agent_architect_prompt():
    agent = ClaudeAgent(
        config=AgentConfig(name="claude", provider="anthropic", api_key="sk-test")
    )
    prompt = agent.build_architect_prompt("implement rate limiter")
    assert "rate limiter" in prompt
    assert "ARCHITECT" in prompt


def test_claude_agent_dispatch_prompt():
    agent = ClaudeAgent(
        config=AgentConfig(name="claude", provider="anthropic", api_key="sk-test")
    )
    stage_outputs = {"stage_2": "def rate_limit(): pass", "stage_3": "no vulnerabilities"}
    prompt = agent.build_dispatch_prompt("implement rate limiter", stage_outputs)
    assert "DISPATCH" in prompt
    assert "rate limiter" in prompt
    assert "stage_2" in prompt
