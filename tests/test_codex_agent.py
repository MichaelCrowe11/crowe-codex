from claude_codex.core.agent import AgentConfig
from claude_codex.core.codex_agent import CodexAgent


def test_codex_agent_instantiation():
    agent = CodexAgent(
        config=AgentConfig(name="codex", provider="openai", api_key="sk-test")
    )
    assert agent.config.name == "codex"


def test_codex_agent_default_model():
    agent = CodexAgent(
        config=AgentConfig(name="codex", provider="openai", api_key="sk-test")
    )
    assert "gpt" in agent.model.lower()


def test_codex_agent_builder_prompt():
    agent = CodexAgent(
        config=AgentConfig(name="codex", provider="openai", api_key="sk-test")
    )
    blueprint = {"subtasks": ["build rate limiter"], "interfaces": ["RateLimiter class"]}
    prompt = agent.build_builder_prompt(blueprint)
    assert "BUILDER" in prompt
    assert "rate limiter" in prompt.lower()
