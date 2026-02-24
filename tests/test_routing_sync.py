import pytest
from crowe_codex.cloud.routing_sync import (
    CloudRoutingSync,
    RoutingEntry,
    TeamRoutingProfile,
)


def test_routing_entry_creation():
    entry = RoutingEntry(
        task_hash="abc123",
        task_signals=["security"],
        strategy="adversarial",
        score=85.0,
    )
    assert entry.timestamp > 0
    assert entry.strategy == "adversarial"


def test_routing_entry_serialization():
    entry = RoutingEntry(
        task_hash="abc",
        task_signals=["testing"],
        strategy="verification_loop",
        score=90.0,
    )
    d = entry.to_dict()
    e2 = RoutingEntry.from_dict(d)
    assert e2.strategy == "verification_loop"
    assert e2.score == 90.0


def test_team_profile_empty():
    profile = TeamRoutingProfile(team_id="test")
    assert profile.total_runs == 0
    assert profile.average_score == 0.0
    assert profile.best_strategies == {}


def test_team_profile_best_strategies():
    entries = [
        RoutingEntry(task_hash="a", task_signals=["security"], strategy="adversarial", score=90.0),
        RoutingEntry(task_hash="b", task_signals=["security"], strategy="consensus", score=70.0),
        RoutingEntry(task_hash="c", task_signals=["testing"], strategy="verification_loop", score=95.0),
    ]
    profile = TeamRoutingProfile(team_id="test", entries=entries)
    best = profile.best_strategies
    assert best["security"] == "adversarial"
    assert best["testing"] == "verification_loop"


def test_team_profile_average_score():
    entries = [
        RoutingEntry(task_hash="a", task_signals=["x"], strategy="s", score=80.0),
        RoutingEntry(task_hash="b", task_signals=["x"], strategy="s", score=90.0),
    ]
    profile = TeamRoutingProfile(team_id="test", entries=entries)
    assert profile.average_score == 85.0


def test_cloud_sync_record_and_retrieve(tmp_path):
    path = tmp_path / "routing.json"
    sync = CloudRoutingSync(team_id="test", persist_path=path)
    sync.record(RoutingEntry(
        task_hash="abc", task_signals=["security"],
        strategy="adversarial", score=88.0,
    ))
    profile = sync.get_profile()
    assert profile.total_runs == 1


def test_cloud_sync_persistence(tmp_path):
    path = tmp_path / "routing.json"
    s1 = CloudRoutingSync(team_id="test", persist_path=path)
    s1.record(RoutingEntry(
        task_hash="abc", task_signals=["testing"],
        strategy="verification_loop", score=90.0,
    ))

    s2 = CloudRoutingSync(team_id="test", persist_path=path)
    assert s2.get_profile().total_runs == 1


def test_cloud_sync_recommendation(tmp_path):
    path = tmp_path / "routing.json"
    sync = CloudRoutingSync(team_id="test", persist_path=path)
    sync.record(RoutingEntry(
        task_hash="a", task_signals=["security"],
        strategy="adversarial", score=95.0,
    ))
    rec = sync.get_recommendation(["security"])
    assert rec == "adversarial"


def test_cloud_sync_no_recommendation(tmp_path):
    path = tmp_path / "routing.json"
    sync = CloudRoutingSync(team_id="test", persist_path=path)
    assert sync.get_recommendation(["unknown"]) is None


def test_cloud_sync_merge_remote(tmp_path):
    path = tmp_path / "routing.json"
    sync = CloudRoutingSync(team_id="test", persist_path=path)
    remote = [
        RoutingEntry(task_hash="r1", task_signals=["perf"],
                    strategy="evolutionary", score=80.0, timestamp=100.0),
        RoutingEntry(task_hash="r2", task_signals=["simple"],
                    strategy="consensus", score=85.0, timestamp=200.0),
    ]
    added = sync.merge_remote(remote)
    assert added == 2
    assert sync.get_profile().total_runs == 2


def test_cloud_sync_merge_deduplicates(tmp_path):
    path = tmp_path / "routing.json"
    sync = CloudRoutingSync(team_id="test", persist_path=path)
    entry = RoutingEntry(
        task_hash="r1", task_signals=["perf"],
        strategy="evolutionary", score=80.0, timestamp=100.0,
    )
    sync.merge_remote([entry])
    added = sync.merge_remote([entry])  # Same entry again
    assert added == 0


def test_cloud_sync_export(tmp_path):
    path = tmp_path / "routing.json"
    sync = CloudRoutingSync(team_id="test", persist_path=path)
    sync.record(RoutingEntry(
        task_hash="a", task_signals=["x"],
        strategy="s", score=80.0,
    ))
    exported = sync.export_entries(since=0.0)
    assert len(exported) == 1


@pytest.mark.asyncio
async def test_cloud_sync_stub(tmp_path):
    path = tmp_path / "routing.json"
    sync = CloudRoutingSync(team_id="test", persist_path=path)
    result = await sync.sync()
    assert result["uploaded"] == 0
    assert result["downloaded"] == 0
