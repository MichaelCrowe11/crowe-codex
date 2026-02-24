import pytest
from crowe_codex.core.agent import AgentConfig
from crowe_codex.core.nim_agent import NimAgent, NIM_ENDPOINTS, NimBatchRequest


def test_nim_agent_instantiation():
    agent = NimAgent(config=AgentConfig(name="nim", provider="nvidia"))
    assert agent.config.provider == "nvidia"


def test_nim_agent_default_config():
    agent = NimAgent()
    assert agent.config.name == "nim"
    assert agent.config.provider == "nvidia"
    assert "nemotron" in agent.config.model


def test_nim_agent_batch_size():
    agent = NimAgent(batch_size=10)
    assert agent.batch_size == 10


@pytest.mark.asyncio
async def test_nim_agent_not_available_without_key():
    agent = NimAgent(config=AgentConfig(name="nim", provider="nvidia"))
    assert await agent.is_available() is False


@pytest.mark.asyncio
async def test_nim_agent_available_with_key():
    agent = NimAgent(config=AgentConfig(name="nim", provider="nvidia", api_key="nvapi-test"))
    assert await agent.is_available() is True


@pytest.mark.asyncio
async def test_nim_agent_fallback_when_unavailable():
    agent = NimAgent(config=AgentConfig(name="nim", provider="nvidia"))
    result = await agent.execute("test prompt")
    assert "NIM_UNAVAILABLE" in result


@pytest.mark.asyncio
async def test_nim_agent_batch_fallback():
    agent = NimAgent(config=AgentConfig(name="nim", provider="nvidia"))
    results = await agent.batch_execute(["prompt1", "prompt2"])
    assert len(results) == 2
    assert all("NIM_UNAVAILABLE" in r for r in results)


def test_nim_endpoints_defined():
    assert "code-review" in NIM_ENDPOINTS
    assert "vulnerability-scan" in NIM_ENDPOINTS


def test_nim_batch_request():
    req = NimBatchRequest(prompts=["a", "b"], model="test")
    assert len(req.prompts) == 2
    assert req.max_tokens == 4096


def test_nim_accelerator_prompt():
    agent = NimAgent()
    prompt = agent.build_accelerator_prompt("def foo(): pass", task="optimize")
    assert "performance" in prompt.lower()
    assert "def foo(): pass" in prompt
