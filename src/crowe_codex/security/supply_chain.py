"""Supply chain verification: triple-verify dependencies, anti-slopsquatting."""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field

from crowe_codex.core.agent import Agent


@dataclass
class DependencyInfo:
    """Information about a single dependency."""

    name: str
    version: str = ""
    source: str = ""  # pypi, npm, etc.
    verified: bool = False
    risk_level: str = "unknown"  # safe, low, medium, high, critical
    risk_reasons: list[str] = field(default_factory=list)
    verified_by: list[str] = field(default_factory=list)


@dataclass
class SupplyChainReport:
    """Complete supply chain verification report."""

    dependencies: list[DependencyInfo] = field(default_factory=list)
    agents_used: list[str] = field(default_factory=list)
    slopsquatting_suspects: list[str] = field(default_factory=list)

    @property
    def total_deps(self) -> int:
        return len(self.dependencies)

    @property
    def verified_count(self) -> int:
        return len([d for d in self.dependencies if d.verified])

    @property
    def risk_count(self) -> int:
        return len([
            d for d in self.dependencies
            if d.risk_level in ("high", "critical")
        ])

    @property
    def is_safe(self) -> bool:
        return self.risk_count == 0 and len(self.slopsquatting_suspects) == 0

    @property
    def summary(self) -> str:
        return (
            f"Supply Chain: {self.verified_count}/{self.total_deps} verified, "
            f"{self.risk_count} risks, "
            f"{len(self.slopsquatting_suspects)} slopsquatting suspects"
        )


# Common typosquatting patterns
SQUATTING_PATTERNS = [
    (r"^python-", "python- prefix often used in typosquatting"),
    (r"-python$", "-python suffix often used in typosquatting"),
    (r"(.)\1{3,}", "excessive repeated characters"),
]

# Known legitimate packages that match squatting patterns
KNOWN_SAFE = {
    "python-dateutil", "python-dotenv", "python-jose",
    "python-multipart", "python-json-logger",
}


def detect_slopsquatting(package_name: str) -> list[str]:
    """Check if a package name looks like a slopsquatting attempt."""
    if package_name in KNOWN_SAFE:
        return []

    warnings: list[str] = []
    for pattern, reason in SQUATTING_PATTERNS:
        if re.search(pattern, package_name):
            warnings.append(reason)

    # Check for common misspellings of popular packages
    popular = {
        "requests": ["requets", "reqeusts", "request", "requsts"],
        "numpy": ["numppy", "numpi", "nympy"],
        "pandas": ["pandsa", "pnadas", "pandass"],
        "flask": ["flaskk", "flaask"],
        "django": ["djnago", "dajngo", "djangoo"],
        "pytest": ["pytets", "pytset"],
        "pydantic": ["pydanctic", "pydanticv"],
    }
    for legit, typos in popular.items():
        if package_name in typos:
            warnings.append(f"possible typosquat of '{legit}'")

    return warnings


class SupplyChainVerifier:
    """Cross-vendor supply chain verification."""

    def __init__(self, agents: dict[str, Agent]) -> None:
        self._agents = {k: v for k, v in agents.items() if k != "dispatch"}

    async def verify(
        self,
        dependencies: list[str],
        ecosystem: str = "pypi",
    ) -> SupplyChainReport:
        """Verify a list of dependencies using multiple agents."""
        # Phase 1: Local slopsquatting detection
        suspects: list[str] = []
        dep_infos: list[DependencyInfo] = []

        for dep in dependencies:
            name = dep.split(">=")[0].split("==")[0].split("<=")[0].strip()
            version = ""
            for sep in (">=", "==", "<=", "~=", "!="):
                if sep in dep:
                    version = dep.split(sep, 1)[1].strip()
                    break

            squatting_warnings = detect_slopsquatting(name)
            if squatting_warnings:
                suspects.append(name)

            dep_infos.append(DependencyInfo(
                name=name,
                version=version,
                source=ecosystem,
                risk_reasons=squatting_warnings,
                risk_level="high" if squatting_warnings else "unknown",
            ))

        # Phase 2: Cross-vendor AI verification
        verify_tasks = {}
        for agent_name, agent in self._agents.items():
            prompt = self._build_verify_prompt(dep_infos, ecosystem)
            verify_tasks[agent_name] = agent.execute(prompt)

        results = dict(
            zip(verify_tasks.keys(), await asyncio.gather(*verify_tasks.values()))
        )

        # Phase 3: Merge AI verification results
        for agent_name, response in results.items():
            self._merge_verification(dep_infos, response, agent_name)

        return SupplyChainReport(
            dependencies=dep_infos,
            agents_used=list(results.keys()),
            slopsquatting_suspects=suspects,
        )

    def _build_verify_prompt(
        self, deps: list[DependencyInfo], ecosystem: str
    ) -> str:
        dep_list = "\n".join(
            f"- {d.name}{(' ' + d.version) if d.version else ''}"
            for d in deps
        )
        return (
            f"Verify these {ecosystem} dependencies for supply chain safety.\n\n"
            f"Dependencies:\n{dep_list}\n\n"
            "For each dependency, assess:\n"
            "1. Is this a real, legitimate package?\n"
            "2. Is the name a possible typosquat of a popular package?\n"
            "3. Are there known security advisories?\n"
            "4. Is the maintainer trustworthy?\n\n"
            "Rate each: SAFE, LOW_RISK, MEDIUM_RISK, HIGH_RISK, or CRITICAL\n"
            "Format: PACKAGE_NAME: RISK_LEVEL - reason"
        )

    def _merge_verification(
        self,
        deps: list[DependencyInfo],
        response: str,
        agent_name: str,
    ) -> None:
        """Merge an agent's verification response into dependency info."""
        response_lower = response.lower()
        for dep in deps:
            name_lower = dep.name.lower()
            if name_lower in response_lower:
                dep.verified_by.append(agent_name)

                # Check risk level from response
                for risk in ("critical", "high_risk", "medium_risk", "low_risk", "safe"):
                    # Look for the risk level near the package name
                    idx = response_lower.find(name_lower)
                    if idx >= 0:
                        context = response_lower[idx:idx + 200]
                        if risk.replace("_", " ") in context or risk in context:
                            dep.risk_level = risk.split("_")[0]
                            break

                if len(dep.verified_by) >= 2:
                    dep.verified = True
