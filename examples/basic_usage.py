"""Basic crowe-codex usage examples."""

import asyncio

from crowe_codex import DualEngine
from crowe_codex.strategies import (
    Adversarial,
    Consensus,
    CognitiveMesh,
    Evolutionary,
    Pipeline,
    VerificationLoop,
)


async def run_consensus():
    """Run a simple consensus comparison."""
    engine = DualEngine()
    result = await engine.run(
        Consensus(),
        task="implement a thread-safe LRU cache",
    )
    print(f"Confidence: {result.confidence.score}/100")
    print(f"Cross-vendor agreement: {result.confidence.cross_vendor_agreement:.0%}")


async def run_adversarial():
    """Run adversarial build/attack/fuzz cycles."""
    engine = DualEngine()
    result = await engine.run(
        Adversarial(rounds=2),
        task="implement rate limiter middleware",
    )
    print(f"Vulnerabilities found: {result.confidence.vulnerabilities_found}")
    print(f"OWASP clean: {result.confidence.owasp_clean}")


async def run_verification():
    """Run verification loop — one writes code, another writes tests."""
    engine = DualEngine()
    result = await engine.run(
        VerificationLoop(iterations=2),
        task="implement JWT token validator",
    )
    print(f"Tests passing: {result.confidence.tests_passing}")


async def run_evolutionary():
    """Run evolutionary generation — breed best code candidates."""
    engine = DualEngine()
    result = await engine.run(
        Evolutionary(population=4, generations=2),
        task="implement concurrent task scheduler",
    )
    print(f"Score: {result.confidence.score}/100")


if __name__ == "__main__":
    asyncio.run(run_consensus())
