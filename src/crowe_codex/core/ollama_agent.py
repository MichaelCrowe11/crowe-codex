"""Ollama agent adapter for Stage 3 (Specialist) with DeepParallel routing."""

from __future__ import annotations

from ollama import AsyncClient

from crowe_codex.core.agent import Agent, AgentConfig

DEFAULT_MODEL = "Mcrowe1210/DeepParallel"

DOMAIN_MODELS = {
    "physics": "Mcrowe1210/DeepParallel-Physics",
    "engineering": "Mcrowe1210/DeepParallel-Engineering",
    "drug_discovery": "Mcrowe1210/DeepParallel-Nemotron-DrugDiscovery",
    "computational": "Mcrowe1210/DeepParallel-Computational",
    "scientific": "Mcrowe1210/DeepParallel-Scientific-v3",
    "lifesci": "Mcrowe1210/DeepParallel-LifeSci",
    "optimized": "Mcrowe1210/DeepParallel-Optimized",
    "ultimate": "Mcrowe1210/DeepParallel-Ultimate",
}

DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "physics": ["physics", "particle", "quantum", "collision", "dynamics", "thermodynamic",
                 "electromagnetic", "gravity", "wave", "photon", "momentum"],
    "engineering": ["structural", "mechanical", "load", "bearing", "circuit", "CAD",
                    "manufacturing", "tolerance", "material strength", "civil"],
    "drug_discovery": ["drug", "molecular", "binding", "affinity", "compound", "pharmacol",
                       "protein folding", "receptor", "inhibitor", "therapeutic"],
    "computational": ["algorithm", "matrix", "parallel computing", "optimization",
                      "computational complexity", "GPU compute", "numerical"],
    "scientific": ["experiment", "hypothesis", "research", "scientific method",
                   "data analysis", "statistical", "peer review"],
    "lifesci": ["gene", "RNA", "DNA", "protein", "cell", "biolog", "genomic",
                "sequencing", "microbi", "enzyme", "metabol"],
}


class DeepParallelRouter:
    """Routes tasks to the best DeepParallel specialist model."""

    def route(self, task: str) -> str:
        task_lower = task.lower()
        scores: dict[str, int] = {}

        for domain, keywords in DOMAIN_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in task_lower)
            if score > 0:
                scores[domain] = score

        if not scores:
            return DEFAULT_MODEL

        best_domain = max(scores, key=lambda k: scores[k])
        return DOMAIN_MODELS[best_domain]


class OllamaAgent(Agent):
    """Ollama agent for local model inference with DeepParallel routing."""

    def __init__(self, config: AgentConfig) -> None:
        super().__init__(config)
        self.model = config.model or DEFAULT_MODEL
        self._router = DeepParallelRouter()
        self._client: AsyncClient | None = None

    def _get_client(self) -> AsyncClient:
        if self._client is None:
            host = self.config.base_url or "http://localhost:11434"
            self._client = AsyncClient(host=host)
        return self._client

    async def execute(self, prompt: str, context: dict[str, object] | None = None) -> str:
        client = self._get_client()
        model = self.model
        if context and "task" in context:
            model = self._router.route(str(context["task"]))

        response = await client.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response["message"]["content"]

    async def is_available(self) -> bool:
        try:
            client = self._get_client()
            await client.list()
            return True
        except Exception:
            return False

    def build_specialist_prompt(self, code: str, task: str) -> str:
        return (
            "You are the SPECIALIST stage of the crowe-codex pipeline.\n\n"
            "Your role:\n"
            "1. Review this code for domain-specific correctness\n"
            "2. Fuzz test inputs and identify edge cases\n"
            "3. Verify all dependencies exist on real package registries\n"
            "4. Check for known CVE patterns\n"
            "5. Validate domain-specific best practices\n\n"
            f"Task: {task}\n\n"
            f"Code to review:\n```\n{code}\n```\n\n"
            "Respond with:\n"
            '- "issues": list of issues found (empty if clean)\n'
            '- "edge_cases": edge cases to test\n'
            '- "dependency_check": verification of each import/dependency\n'
            '- "domain_notes": domain-specific observations\n'
        )
