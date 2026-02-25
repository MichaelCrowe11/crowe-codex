"""Security audit examples for crowe-codex."""

import asyncio

from crowe_codex.core.engine import DualEngine
from crowe_codex.security.owasp import OWASPScanner
from crowe_codex.security.supply_chain import SupplyChainVerifier
from crowe_codex.security.threat_model import ThreatModelEngine
from crowe_codex.security.compliance import ComplianceMapper
from crowe_codex.security.attestation import AttestationGenerator


async def full_security_audit(code: str):
    """Run a complete security audit with all modules."""
    engine = DualEngine()
    agents = engine._agents

    # OWASP Top 10 scan
    owasp = OWASPScanner(agents)
    owasp_report = await owasp.scan(code)
    print(f"OWASP: {owasp_report.summary}")

    # Threat modeling (STRIDE)
    threats = ThreatModelEngine(agents)
    threat_model = await threats.analyze(code)
    print(f"Threats: {len(threat_model.threats)} found, {len(threat_model.critical_threats)} critical")

    # Compliance check
    compliance = ComplianceMapper(agents)
    compliance_report = await compliance.assess(code, frameworks=["soc2", "hipaa"])
    print(f"Compliance: {compliance_report.pass_rate:.0%} pass rate")

    # Generate attestation
    gen = AttestationGenerator()
    attestation = gen.generate(
        code=code,
        owasp=owasp_report,
        threat_model=threat_model,
        compliance=compliance_report,
        agents_used=list(agents.keys()),
        strategy="security_audit",
    )
    print(f"Score: {attestation.overall_score}/100 — {attestation.verdict}")


async def verify_dependencies():
    """Verify supply chain safety of dependencies."""
    engine = DualEngine()
    verifier = SupplyChainVerifier(engine._agents)
    result = await verifier.verify(
        ["requests", "flask", "pydantic", "cryptography"],
        ecosystem="pypi",
    )
    print(result.summary)
    for dep in result.dependencies:
        print(f"  {dep.name}: {dep.risk_level}")


if __name__ == "__main__":
    sample_code = '''
    from flask import Flask, request
    app = Flask(__name__)

    @app.route("/login", methods=["POST"])
    def login():
        username = request.form["username"]
        password = request.form["password"]
        # TODO: add authentication
        return "OK"
    '''
    asyncio.run(full_security_audit(sample_code))
