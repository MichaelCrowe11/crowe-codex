# claude-codex

Cross-vendor adversarial AI code verification engine.

OpenAI, Anthropic, and your own models — adversarially verifying each other's output. No single company's blind spots make it to production.

## Install

```bash
pip install claude-codex
```

## Quick Start

```bash
# Adversarial code synthesis
claude-codex adversarial "implement rate limiter middleware"

# Cross-vendor consensus
claude-codex consensus "add input validation to user endpoint"

# Auto-select best strategy
claude-codex auto "fix memory leak in worker pool"
```

## SDK

```python
from claude_codex import DualEngine
from claude_codex.strategies import Adversarial

engine = DualEngine()
result = engine.run(Adversarial(), task="implement rate limiter")
print(result.confidence.score)  # 0-100
```

## License

MIT
