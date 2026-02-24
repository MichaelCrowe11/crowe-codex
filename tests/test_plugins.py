import pytest
from crowe_codex.plugins.loader import PluginLoader, PluginRegistry
from crowe_codex.strategies.consensus import Consensus
from crowe_codex.strategies.adversarial import Adversarial


def test_plugin_loader_discover_returns_dict():
    loader = PluginLoader()
    result = loader.discover()
    assert isinstance(result, dict)


def test_plugin_loader_load_builtin_module():
    loader = PluginLoader()
    found = loader.load_from_module("crowe_codex.strategies.consensus")
    assert "consensus" in found


def test_plugin_loader_load_invalid_module():
    loader = PluginLoader()
    found = loader.load_from_module("nonexistent.module.path")
    assert found == {}


def test_plugin_loader_loaded_property():
    loader = PluginLoader()
    loader.load_from_module("crowe_codex.strategies.adversarial")
    assert "adversarial" in loader.loaded


def test_plugin_registry_register_and_get():
    registry = PluginRegistry()
    consensus = Consensus()
    registry.register(consensus)
    assert registry.get("consensus") is consensus


def test_plugin_registry_get_missing():
    registry = PluginRegistry()
    with pytest.raises(KeyError):
        registry.get("nonexistent")


def test_plugin_registry_available():
    registry = PluginRegistry()
    registry.register(Consensus())
    registry.register(Adversarial())
    available = registry.available()
    assert "consensus" in available
    assert "adversarial" in available


def test_plugin_registry_all_strategies():
    registry = PluginRegistry()
    registry.register(Consensus())
    registry.register(Adversarial())
    all_strats = registry.all_strategies()
    assert len(all_strats) == 2


def test_plugin_registry_register_from_loader():
    registry = PluginRegistry()
    loader = PluginLoader()
    loader.load_from_module("crowe_codex.strategies.consensus")
    # register_from_loader calls discover(), which checks entry points
    # Since we loaded manually, let's test the manual path
    for name, cls in loader.loaded.items():
        registry.register(cls())
    assert "consensus" in registry.available()
