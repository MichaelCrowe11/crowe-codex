"""Strategy Marketplace: discover, share, and install community strategies."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from crowe_codex.strategies.base import Strategy
from crowe_codex.plugins.loader import PluginLoader, PluginRegistry


@dataclass
class StrategyListing:
    """A strategy listing in the marketplace."""

    name: str
    display_name: str
    description: str
    author: str
    version: str
    tags: list[str] = field(default_factory=list)
    install_source: str = ""  # pip package name or git URL
    downloads: int = 0
    rating: float = 0.0
    rating_count: int = 0
    stages_required: list[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "author": self.author,
            "version": self.version,
            "tags": self.tags,
            "install_source": self.install_source,
            "downloads": self.downloads,
            "rating": self.rating,
            "rating_count": self.rating_count,
            "stages_required": self.stages_required,
        }

    @classmethod
    def from_dict(cls, data: dict) -> StrategyListing:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @classmethod
    def from_strategy(
        cls,
        strategy: Strategy,
        author: str = "",
        description: str = "",
        version: str = "0.1.0",
    ) -> StrategyListing:
        """Create a listing from a Strategy instance."""
        return cls(
            name=strategy.name,
            display_name=strategy.name.replace("_", " ").title(),
            description=description or f"Strategy: {strategy.name}",
            author=author,
            version=version,
            stages_required=strategy.stages_needed(),
        )


@dataclass
class MarketplaceIndex:
    """Index of all available strategies in the marketplace."""

    listings: list[StrategyListing] = field(default_factory=list)

    def search(
        self,
        query: str = "",
        tags: list[str] | None = None,
        min_rating: float = 0.0,
    ) -> list[StrategyListing]:
        """Search marketplace listings."""
        results = list(self.listings)

        if query:
            query_lower = query.lower()
            results = [
                item for item in results
                if query_lower in item.name.lower()
                or query_lower in item.description.lower()
                or query_lower in item.display_name.lower()
            ]

        if tags:
            tag_set = set(tags)
            results = [item for item in results if tag_set & set(item.tags)]

        if min_rating > 0:
            results = [item for item in results if item.rating >= min_rating]

        return sorted(results, key=lambda item: item.downloads, reverse=True)

    def add_listing(self, listing: StrategyListing) -> None:
        """Add or update a listing."""
        existing = [item for item in self.listings if item.name == listing.name]
        if existing:
            self.listings.remove(existing[0])
        self.listings.append(listing)

    @property
    def total_listings(self) -> int:
        return len(self.listings)

    @property
    def categories(self) -> list[str]:
        """All unique tags across listings."""
        tags: set[str] = set()
        for listing in self.listings:
            tags.update(listing.tags)
        return sorted(tags)


# Built-in strategy metadata
BUILTIN_STRATEGIES: list[dict[str, object]] = [
    {
        "name": "adversarial",
        "display_name": "Adversarial Synthesis",
        "description": "Build/attack/fuzz cycles with cross-vendor verification. One agent builds, another attacks, a third fuzzes.",
        "author": "crowe-codex",
        "tags": ["security", "verification", "cross-vendor"],
    },
    {
        "name": "consensus",
        "display_name": "Consensus Mode",
        "description": "Same task through multiple agents, compare and merge the best results.",
        "author": "crowe-codex",
        "tags": ["comparison", "verification", "lightweight"],
    },
    {
        "name": "verification_loop",
        "display_name": "Verification Loop",
        "description": "One agent writes code, another writes tests, they cross-verify and iterate.",
        "author": "crowe-codex",
        "tags": ["testing", "verification", "tdd"],
    },
    {
        "name": "pipeline",
        "display_name": "Sequential Pipeline",
        "description": "Architect -> Build -> Specialist Review -> Dispatch. Clean handoff chain.",
        "author": "crowe-codex",
        "tags": ["sequential", "structured", "architecture"],
    },
    {
        "name": "cognitive_mesh",
        "display_name": "Cognitive Mesh",
        "description": "All agents solve in parallel, dispatch merges the best parts of each solution.",
        "author": "crowe-codex",
        "tags": ["parallel", "merge", "comprehensive"],
    },
    {
        "name": "evolutionary",
        "display_name": "Evolutionary Generation",
        "description": "Generate multiple candidates, score fitness, breed best traits across generations.",
        "author": "crowe-codex",
        "tags": ["evolutionary", "optimization", "genetic"],
    },
    {
        "name": "adaptive_router",
        "display_name": "Adaptive Router",
        "description": "Learns which strategy works best per task type. Improves over time.",
        "author": "crowe-codex",
        "tags": ["routing", "adaptive", "learning"],
    },
]


class StrategyMarketplace:
    """Local marketplace client for browsing, installing, and publishing strategies."""

    def __init__(
        self,
        persist_path: Path | None = None,
        api_url: str | None = None,
    ) -> None:
        self._persist_path = persist_path or (
            Path.home() / ".crowe-codex" / "marketplace" / "index.json"
        )
        self._api_url = api_url
        self._index = self._load()

        # Ensure built-in strategies are listed
        self._ensure_builtins()

    def browse(
        self,
        query: str = "",
        tags: list[str] | None = None,
        min_rating: float = 0.0,
    ) -> list[StrategyListing]:
        """Browse the marketplace."""
        return self._index.search(query=query, tags=tags, min_rating=min_rating)

    def get_listing(self, name: str) -> StrategyListing | None:
        """Get a specific strategy listing."""
        matches = [item for item in self._index.listings if item.name == name]
        return matches[0] if matches else None

    def publish(self, listing: StrategyListing) -> None:
        """Publish a strategy to the marketplace."""
        self._index.add_listing(listing)
        self._save()

    def rate(self, name: str, rating: float) -> bool:
        """Rate a strategy (1-5 stars)."""
        rating = max(1.0, min(5.0, rating))
        listing = self.get_listing(name)
        if not listing:
            return False

        # Update running average
        total = listing.rating * listing.rating_count + rating
        listing.rating_count += 1
        listing.rating = total / listing.rating_count
        self._save()
        return True

    def install_from_registry(self, registry: PluginRegistry) -> int:
        """Register all marketplace strategies that are installed locally."""
        loader = PluginLoader()
        plugins = loader.discover()
        count = 0
        for name, cls in plugins.items():
            try:
                instance = cls()
                registry.register(instance)
                # Update marketplace with discovery
                if not self.get_listing(name):
                    listing = StrategyListing.from_strategy(
                        instance, author="community"
                    )
                    self.publish(listing)
                count += 1
            except Exception:
                continue
        return count

    @property
    def total_listings(self) -> int:
        return self._index.total_listings

    @property
    def categories(self) -> list[str]:
        return self._index.categories

    def _ensure_builtins(self) -> None:
        """Ensure built-in strategies are in the index."""
        for info in BUILTIN_STRATEGIES:
            name = str(info["name"])
            if not self.get_listing(name):
                self._index.add_listing(StrategyListing(
                    name=name,
                    display_name=str(info["display_name"]),
                    description=str(info["description"]),
                    author=str(info["author"]),
                    version="1.0.0",
                    tags=list(info.get("tags", [])),
                ))
        self._save()

    def _load(self) -> MarketplaceIndex:
        if self._persist_path.exists():
            try:
                data = json.loads(self._persist_path.read_text())
                listings = [
                    StrategyListing.from_dict(item) for item in data.get("listings", [])
                ]
                return MarketplaceIndex(listings=listings)
            except (json.JSONDecodeError, OSError):
                pass
        return MarketplaceIndex()

    def _save(self) -> None:
        self._persist_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "listings": [item.to_dict() for item in self._index.listings],
        }
        self._persist_path.write_text(json.dumps(data, indent=2))
