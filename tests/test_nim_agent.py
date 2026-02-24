import asyncio
from claude_codex.core.agent import AgentConfig
from claude_codex.core.nim_agent import NimAgent


def test_nim_agent_instantiation():
    agent = NimAgent(config=AgentConfig(name="nim", provider="nvidia"))
    assert agent.config.provider == "nvidia"


def test_nim_agent_not_available_without_key():
    agent = NimAgent(config=AgentConfig(name="nim", provider="nvidia"))
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(agent.is_available())
        assert result is False
    finally:
        loop.close()


def test_nim_agent_available_with_key():
    agent = NimAgent(config=AgentConfig(name="nim", provider="nvidia", api_key="nvapi-test"))
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(agent.is_available())
        assert result is True
    finally:
        loop.close()
