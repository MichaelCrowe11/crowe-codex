import pytest

from crowe_codex.core.agent import Agent, AgentConfig, AgentRegistry


def test_agent_is_abstract():
    with pytest.raises(TypeError):
        Agent(config=AgentConfig(name="test", provider="test"))


def test_agent_config_creation():
    config = AgentConfig(
        name="claude",
        provider="anthropic",
        model="claude-opus-4-6",
    )
    assert config.name == "claude"
    assert config.provider == "anthropic"


class MockAgent(Agent):
    async def execute(self, prompt, context=None):
        return f"mock: {prompt}"

    async def is_available(self):
        return True


def test_concrete_agent_instantiation():
    agent = MockAgent(config=AgentConfig(name="mock", provider="test"))
    assert agent.config.name == "mock"


@pytest.mark.asyncio
async def test_mock_agent_execute():
    agent = MockAgent(config=AgentConfig(name="mock", provider="test"))
    result = await agent.execute("hello")
    assert result == "mock: hello"


def test_registry_register_and_get():
    registry = AgentRegistry()
    agent = MockAgent(config=AgentConfig(name="mock", provider="test"))
    registry.register("mock", agent)
    assert registry.get("mock") is agent


def test_registry_get_missing_raises():
    registry = AgentRegistry()
    with pytest.raises(KeyError):
        registry.get("nonexistent")


def test_registry_list_available():
    registry = AgentRegistry()
    agent = MockAgent(config=AgentConfig(name="mock", provider="test"))
    registry.register("mock", agent)
    assert "mock" in registry.available()
