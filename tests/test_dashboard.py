from crowe_codex.cloud.dashboard import (
    DashboardStore,
    ProjectSnapshot,
    TeamDashboard,
)
from crowe_codex.security.attestation import AttestationGenerator
from crowe_codex.security.owasp import OWASPReport


def test_project_snapshot_creation():
    snap = ProjectSnapshot(project_name="my-api", security_score=85)
    assert snap.project_name == "my-api"
    assert snap.timestamp != ""


def test_project_snapshot_serialization():
    snap = ProjectSnapshot(
        project_name="api",
        security_score=90,
        confidence_score=88,
        strategy_used="adversarial",
    )
    d = snap.to_dict()
    s2 = ProjectSnapshot.from_dict(d)
    assert s2.security_score == 90
    assert s2.strategy_used == "adversarial"


def test_project_snapshot_from_attestation():
    gen = AttestationGenerator()
    owasp = OWASPReport(findings=[], agents_used=["claude"])
    att = gen.generate(code="code", owasp=owasp, strategy="adversarial")
    snap = ProjectSnapshot.from_attestation("my-project", att, confidence_score=95)
    assert snap.project_name == "my-project"
    assert snap.owasp_clean is True
    assert snap.confidence_score == 95


def test_team_dashboard_empty():
    dash = TeamDashboard(team_id="test")
    assert dash.total_runs == 0
    assert dash.average_security_score == 0.0
    assert dash.projects == []


def test_team_dashboard_with_snapshots():
    snaps = [
        ProjectSnapshot(project_name="api", security_score=90, owasp_clean=True),
        ProjectSnapshot(project_name="api", security_score=80, owasp_clean=True),
        ProjectSnapshot(project_name="web", security_score=70, owasp_clean=False),
    ]
    dash = TeamDashboard(team_id="test", snapshots=snaps)
    assert dash.total_runs == 3
    assert set(dash.projects) == {"api", "web"}
    assert dash.average_security_score == 80.0


def test_team_dashboard_owasp_compliance_rate():
    snaps = [
        ProjectSnapshot(project_name="a", security_score=90, owasp_clean=True),
        ProjectSnapshot(project_name="b", security_score=80, owasp_clean=True),
        ProjectSnapshot(project_name="c", security_score=50, owasp_clean=False),
    ]
    dash = TeamDashboard(team_id="test", snapshots=snaps)
    assert abs(dash.owasp_compliance_rate - 2 / 3) < 0.01


def test_team_dashboard_latest_snapshot():
    snaps = [
        ProjectSnapshot(project_name="api", security_score=70, timestamp="2026-01-01"),
        ProjectSnapshot(project_name="api", security_score=90, timestamp="2026-02-01"),
    ]
    dash = TeamDashboard(team_id="test", snapshots=snaps)
    latest = dash.latest_snapshot("api")
    assert latest is not None
    assert latest.security_score == 90


def test_team_dashboard_trend_improving():
    snaps = [
        ProjectSnapshot(project_name="api", security_score=70, timestamp="2026-01-01"),
        ProjectSnapshot(project_name="api", security_score=90, timestamp="2026-02-01"),
    ]
    dash = TeamDashboard(team_id="test", snapshots=snaps)
    assert dash.trend("api") == "improving"


def test_team_dashboard_trend_declining():
    snaps = [
        ProjectSnapshot(project_name="api", security_score=90, timestamp="2026-01-01"),
        ProjectSnapshot(project_name="api", security_score=60, timestamp="2026-02-01"),
    ]
    dash = TeamDashboard(team_id="test", snapshots=snaps)
    assert dash.trend("api") == "declining"


def test_team_dashboard_trend_stable():
    snaps = [
        ProjectSnapshot(project_name="api", security_score=80, timestamp="2026-01-01"),
    ]
    dash = TeamDashboard(team_id="test", snapshots=snaps)
    assert dash.trend("api") == "stable"


def test_team_dashboard_summary():
    snaps = [
        ProjectSnapshot(project_name="api", security_score=85, owasp_clean=True),
    ]
    dash = TeamDashboard(team_id="test", snapshots=snaps)
    summary = dash.summary()
    assert summary["total_projects"] == 1
    assert summary["total_runs"] == 1
    assert "api" in summary["projects"]


def test_dashboard_store_record_and_persist(tmp_path):
    path = tmp_path / "dashboard.json"
    store = DashboardStore(team_id="test", persist_path=path)
    store.record_snapshot(ProjectSnapshot(
        project_name="api", security_score=90,
    ))

    store2 = DashboardStore(team_id="test", persist_path=path)
    dash = store2.get_dashboard()
    assert dash.total_runs == 1


def test_dashboard_store_record_attestation(tmp_path):
    path = tmp_path / "dashboard.json"
    store = DashboardStore(team_id="test", persist_path=path)

    gen = AttestationGenerator()
    att = gen.generate(
        code="code",
        owasp=OWASPReport(findings=[], agents_used=["claude"]),
    )
    snap = store.record_attestation("my-project", att, confidence_score=92)
    assert snap.project_name == "my-project"
    assert snap.confidence_score == 92


def test_dashboard_store_summary(tmp_path):
    path = tmp_path / "dashboard.json"
    store = DashboardStore(team_id="test", persist_path=path)
    store.record_snapshot(ProjectSnapshot(project_name="api", security_score=85))
    summary = store.get_summary()
    assert summary["total_runs"] == 1
