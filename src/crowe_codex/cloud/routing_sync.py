"""Cloud Routing Sync: share learned routing intelligence across teams."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RoutingEntry:
    """A single routing decision and its outcome."""

    task_hash: str
    task_signals: list[str]
    strategy: str
    score: float
    timestamp: float = 0.0
    user_id: str = ""
    team_id: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()

    def to_dict(self) -> dict:
        return {
            "task_hash": self.task_hash,
            "task_signals": self.task_signals,
            "strategy": self.strategy,
            "score": self.score,
            "timestamp": self.timestamp,
            "user_id": self.user_id,
            "team_id": self.team_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> RoutingEntry:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class TeamRoutingProfile:
    """Aggregated routing intelligence for a team."""

    team_id: str
    entries: list[RoutingEntry] = field(default_factory=list)
    strategy_scores: dict[str, list[float]] = field(default_factory=dict)

    @property
    def best_strategies(self) -> dict[str, str]:
        """Per-signal best strategy based on average score."""
        signal_strategies: dict[str, dict[str, list[float]]] = {}

        for entry in self.entries:
            for signal in entry.task_signals:
                if signal not in signal_strategies:
                    signal_strategies[signal] = {}
                strat = entry.strategy
                if strat not in signal_strategies[signal]:
                    signal_strategies[signal][strat] = []
                signal_strategies[signal][strat].append(entry.score)

        result = {}
        for signal, strategies in signal_strategies.items():
            best = max(strategies, key=lambda s: sum(strategies[s]) / len(strategies[s]))
            result[signal] = best
        return result

    @property
    def total_runs(self) -> int:
        return len(self.entries)

    @property
    def average_score(self) -> float:
        if not self.entries:
            return 0.0
        return sum(e.score for e in self.entries) / len(self.entries)


class CloudRoutingSync:
    """Syncs routing intelligence between local and cloud storage.

    In local mode: persists to disk as JSON.
    In cloud mode: would sync to a REST API (future SaaS feature).
    """

    def __init__(
        self,
        team_id: str = "default",
        persist_path: Path | None = None,
        api_url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.team_id = team_id
        self._persist_path = persist_path or (
            Path.home() / ".crowe-codex" / "routing" / f"{team_id}.json"
        )
        self._api_url = api_url
        self._api_key = api_key
        self._profile = self._load()

    def record(self, entry: RoutingEntry) -> None:
        """Record a routing decision."""
        entry.team_id = self.team_id
        self._profile.entries.append(entry)
        self._save()

    def get_profile(self) -> TeamRoutingProfile:
        """Get the current team routing profile."""
        return self._profile

    def get_recommendation(self, signals: list[str]) -> str | None:
        """Get the best strategy recommendation for given task signals."""
        best = self._profile.best_strategies
        for signal in signals:
            if signal in best:
                return best[signal]
        return None

    def merge_remote(self, remote_entries: list[RoutingEntry]) -> int:
        """Merge routing entries from remote (team sync)."""
        existing_hashes = {
            (e.task_hash, e.timestamp) for e in self._profile.entries
        }
        added = 0
        for entry in remote_entries:
            if (entry.task_hash, entry.timestamp) not in existing_hashes:
                self._profile.entries.append(entry)
                added += 1
        if added > 0:
            self._save()
        return added

    def export_entries(self, since: float = 0.0) -> list[RoutingEntry]:
        """Export routing entries since a given timestamp (for sync upload)."""
        return [e for e in self._profile.entries if e.timestamp >= since]

    async def sync(self) -> dict[str, int]:
        """Sync with cloud backend (stub — returns local stats)."""
        # Future: POST to self._api_url with self.export_entries()
        # Future: GET from self._api_url and self.merge_remote()
        return {
            "uploaded": 0,
            "downloaded": 0,
            "local_entries": len(self._profile.entries),
        }

    def _load(self) -> TeamRoutingProfile:
        if self._persist_path.exists():
            try:
                data = json.loads(self._persist_path.read_text())
                entries = [RoutingEntry.from_dict(e) for e in data.get("entries", [])]
                return TeamRoutingProfile(
                    team_id=self.team_id,
                    entries=entries,
                )
            except (json.JSONDecodeError, OSError):
                pass
        return TeamRoutingProfile(team_id=self.team_id)

    def _save(self) -> None:
        self._persist_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "team_id": self.team_id,
            "entries": [e.to_dict() for e in self._profile.entries],
        }
        self._persist_path.write_text(json.dumps(data, indent=2))
