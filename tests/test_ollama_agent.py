from claude_codex.core.agent import AgentConfig
from claude_codex.core.ollama_agent import OllamaAgent, DeepParallelRouter


def test_ollama_agent_instantiation():
    agent = OllamaAgent(
        config=AgentConfig(name="ollama", provider="ollama", model="deepparallel")
    )
    assert agent.config.provider == "ollama"


def test_ollama_agent_default_model():
    agent = OllamaAgent(
        config=AgentConfig(name="ollama", provider="ollama")
    )
    assert agent.model == "Mcrowe1210/DeepParallel"


def test_deep_parallel_router_general():
    router = DeepParallelRouter()
    model = router.route("implement a REST API endpoint")
    assert model == "Mcrowe1210/DeepParallel"


def test_deep_parallel_router_physics():
    router = DeepParallelRouter()
    model = router.route("simulate particle collision dynamics")
    assert "Physics" in model


def test_deep_parallel_router_engineering():
    router = DeepParallelRouter()
    model = router.route("optimize structural load bearing calculation")
    assert "Engineering" in model


def test_deep_parallel_router_drug_discovery():
    router = DeepParallelRouter()
    model = router.route("analyze molecular binding affinity for drug candidate")
    assert "DrugDiscovery" in model


def test_deep_parallel_router_computational():
    router = DeepParallelRouter()
    model = router.route("optimize matrix multiplication algorithm performance")
    assert "Computational" in model


def test_deep_parallel_router_lifesci():
    router = DeepParallelRouter()
    model = router.route("analyze gene expression patterns in RNA sequencing data")
    assert "LifeSci" in model


def test_specialist_prompt():
    agent = OllamaAgent(
        config=AgentConfig(name="ollama", provider="ollama")
    )
    prompt = agent.build_specialist_prompt("def hello(): pass", "build greeting function")
    assert "SPECIALIST" in prompt
    assert "hello" in prompt
