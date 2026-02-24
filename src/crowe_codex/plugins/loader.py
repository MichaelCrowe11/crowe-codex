"""Plugin loader: discovers and loads custom strategies from entry points."""

from __future__ import annotations

import importlib
import importlib.metadata
from crowe_codex.strategies.base import Strategy


ENTRY_POINT_GROUP = "crowe_codex.strategies"


class PluginLoader:
    """Discovers and loads strategy plugins from Python entry points."""

    def __init__(self) -> None:
        self._plugins: dict[str, type[Strategy]] = {}

    def discover(self) -> dict[str, type[Strategy]]:
        """Scan installed packages for crowe_codex strategy entry points."""
        try:
            eps = importlib.metadata.entry_points()
            # Python 3.12+ returns a SelectableGroups, 3.9-3.11 returns dict
            if hasattr(eps, "select"):
                group_eps = eps.select(group=ENTRY_POINT_GROUP)
            else:
                group_eps = eps.get(ENTRY_POINT_GROUP, [])

            for ep in group_eps:
                try:
                    cls = ep.load()
                    if isinstance(cls, type) and issubclass(cls, Strategy) and cls is not Strategy:
                        self._plugins[ep.name] = cls
                except Exception:
                    continue
        except Exception:
            pass

        return dict(self._plugins)

    def load_from_module(self, module_path: str) -> dict[str, type[Strategy]]:
        """Load strategies from a specific module path."""
        found: dict[str, type[Strategy]] = {}
        try:
            module = importlib.import_module(module_path)
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, Strategy)
                    and attr is not Strategy
                    and hasattr(attr, "name")
                    and attr.name
                ):
                    found[attr.name] = attr
                    self._plugins[attr.name] = attr
        except ImportError:
            pass
        return found

    @property
    def loaded(self) -> dict[str, type[Strategy]]:
        return dict(self._plugins)


class PluginRegistry:
    """Central registry for all available strategies (built-in + plugins)."""

    def __init__(self) -> None:
        self._strategies: dict[str, Strategy] = {}

    def register(self, strategy: Strategy) -> None:
        self._strategies[strategy.name] = strategy

    def get(self, name: str) -> Strategy:
        if name not in self._strategies:
            raise KeyError(f"Strategy '{name}' not registered")
        return self._strategies[name]

    def available(self) -> list[str]:
        return list(self._strategies.keys())

    def all_strategies(self) -> dict[str, Strategy]:
        return dict(self._strategies)

    def register_from_loader(self, loader: PluginLoader) -> int:
        """Instantiate and register all discovered strategy plugins."""
        plugins = loader.discover()
        count = 0
        for name, cls in plugins.items():
            try:
                instance = cls()
                self.register(instance)
                count += 1
            except Exception:
                continue
        return count
