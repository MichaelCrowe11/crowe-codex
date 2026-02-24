import pytest
from crowe_codex.core.agent import Agent, AgentConfig
from crowe_codex.fitness.runner import (
    CandidateResult,
    FitnessEvaluator,
    FitnessRunner,
    FitnessScore,
)
from crowe_codex.fitness.quality import AgentFitnessEvaluator, StaticFitnessEvaluator


def test_fitness_score_total_weighted():
    score = FitnessScore(
        correctness=100.0,
        performance=100.0,
        readability=100.0,
        robustness=100.0,
        security=100.0,
    )
    assert score.total == 100.0


def test_fitness_score_zero():
    score = FitnessScore()
    assert score.total == 0.0


def test_fitness_score_partial():
    score = FitnessScore(correctness=80.0, robustness=60.0)
    # 80 * 0.35 + 60 * 0.20 = 28 + 12 = 40
    assert score.total == 40.0


def test_candidate_result_rank_key():
    r1 = CandidateResult(code="a", fitness=FitnessScore(correctness=90.0))
    r2 = CandidateResult(code="b", fitness=FitnessScore(correctness=50.0))
    assert r1.rank_key > r2.rank_key


def test_base_evaluator_returns_zeros():
    evaluator = FitnessEvaluator()
    import asyncio
    score = asyncio.get_event_loop().run_until_complete(
        evaluator.score("code", "task")
    )
    assert score.total == 0.0


@pytest.mark.asyncio
async def test_fitness_runner_no_evaluators():
    runner = FitnessRunner()
    score = await runner.evaluate("code", "task")
    assert score.total == 0.0


@pytest.mark.asyncio
async def test_fitness_runner_with_evaluator():
    class HighScorer(FitnessEvaluator):
        async def score(self, code, task):
            return FitnessScore(correctness=90.0, readability=80.0)

    runner = FitnessRunner(evaluators=[HighScorer()])
    score = await runner.evaluate("code", "task")
    assert score.correctness == 90.0
    assert score.readability == 80.0


@pytest.mark.asyncio
async def test_fitness_runner_rank_candidates():
    class Scorer(FitnessEvaluator):
        async def score(self, code, task):
            length_score = min(len(code) * 10.0, 100.0)
            return FitnessScore(correctness=length_score)

    runner = FitnessRunner(evaluators=[Scorer()])
    results = await runner.rank_candidates(["short", "much longer code"], "task")
    assert len(results) == 2
    assert results[0].rank_key >= results[1].rank_key


@pytest.mark.asyncio
async def test_static_evaluator_docstrings():
    evaluator = StaticFitnessEvaluator()
    code_with_docs = '"""\nDocstring here\n"""\ndef foo() -> int:\n    return 1'
    score = await evaluator.score(code_with_docs, "task")
    assert score.readability > 50.0


@pytest.mark.asyncio
async def test_static_evaluator_error_handling():
    evaluator = StaticFitnessEvaluator()
    code = "try:\n    x = 1\nexcept ValueError:\n    pass"
    score = await evaluator.score(code, "task")
    assert score.robustness > 30.0


class FakeAgent(Agent):
    def __init__(self, response):
        super().__init__(config=AgentConfig(name="fake", provider="test"))
        self._response = response

    async def execute(self, prompt, context=None):
        return self._response

    async def is_available(self):
        return True


@pytest.mark.asyncio
async def test_agent_evaluator_parses_json():
    agent = FakeAgent('{"correctness": 85, "performance": 70, "readability": 90, "robustness": 75, "security": 80}')
    evaluator = AgentFitnessEvaluator(agent)
    score = await evaluator.score("code", "task")
    assert score.correctness == 85.0
    assert score.security == 80.0


@pytest.mark.asyncio
async def test_agent_evaluator_handles_bad_json():
    agent = FakeAgent("not json at all")
    evaluator = AgentFitnessEvaluator(agent)
    score = await evaluator.score("code", "task")
    assert score.total == 0.0
