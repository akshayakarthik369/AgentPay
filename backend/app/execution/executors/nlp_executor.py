"""
NLP Executor — handles Sentiment Analysis, Summarization, Classification, NLP tasks.
Produces deterministic, task-aware demo output clearly labelled as synthetic.
"""
import hashlib
from typing import List
from app.execution.base import BaseExecutor, ExecutorResult, LogFn

_SENTIMENT_THEMES = [
    "product quality", "delivery speed", "customer service",
    "price / value", "ease of use", "packaging experience",
]

_POSITIVE_PHRASES = [
    "customers frequently highlight outstanding quality",
    "delivery speed is consistently praised across feedback",
    "many reviewers cite exceptional value for money",
]

_NEGATIVE_PHRASES = [
    "some respondents note inconsistency in packaging",
    "a subset of feedback mentions delayed resolution times",
    "a minority of responses indicate unmet expectations on service",
]


def _seeded_int(seed_str: str, lo: int, hi: int) -> int:
    """Deterministically derive an integer in [lo, hi] from a string seed."""
    digest = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
    return lo + (digest % (hi - lo + 1))


class NLPExecutor(BaseExecutor):

    @property
    def executor_name(self) -> str:
        return "NLP Sentiment & Text Analysis Executor"

    @property
    def supported_capabilities(self) -> List[str]:
        return ["nlp", "sentiment analysis", "summarization", "text analysis", "classification"]

    def execute(
        self,
        task_title: str,
        task_description: str,
        category: str,
        required_capability: str,
        agent_name: str,
        agent_capabilities: List[str],
        bid_proposal: str,
        log_fn: LogFn,
    ) -> ExecutorResult:

        log_fn("info", "init", f"NLP Executor initialised for task: '{task_title}'")
        log_fn("info", "context", f"Required capability: {required_capability} | Category: {category}")
        log_fn("info", "loading", "Task description parsed and tokenised")

        seed = task_title + category
        positive_pct = _seeded_int(seed + "pos", 52, 68)
        negative_pct = _seeded_int(seed + "neg", 12, 25)
        neutral_pct = 100 - positive_pct - negative_pct
        confidence = round(0.75 + (_seeded_int(seed + "conf", 0, 20) / 100), 2)
        theme_idx = _seeded_int(seed + "theme", 0, len(_SENTIMENT_THEMES) - 3)
        top_themes = _SENTIMENT_THEMES[theme_idx: theme_idx + 3]

        log_fn("info", "analysis", f"Sentiment distribution computed: +{positive_pct}% / ~{neutral_pct}% / -{negative_pct}%")
        log_fn("info", "themes", f"Dominant themes identified: {', '.join(top_themes)}")

        positive_note = _POSITIVE_PHRASES[_seeded_int(seed + "pos_phrase", 0, len(_POSITIVE_PHRASES) - 1)]
        negative_note = _NEGATIVE_PHRASES[_seeded_int(seed + "neg_phrase", 0, len(_NEGATIVE_PHRASES) - 1)]

        output_text = (
            f"# NLP Analysis Report — {task_title}\n\n"
            f"**Executor:** {agent_name} using {self.executor_name}\n\n"
            f"## Sentiment Distribution (Demonstration)\n"
            f"- Positive: **{positive_pct}%**\n"
            f"- Neutral:  **{neutral_pct}%**\n"
            f"- Negative: **{negative_pct}%**\n\n"
            f"## Dominant Themes\n"
            + "".join(f"- {t.title()}\n" for t in top_themes) +
            f"\n## Key Observations\n"
            f"- {positive_note.capitalize()}.\n"
            f"- {negative_note.capitalize()}.\n\n"
            f"## Summary\n"
            f"Based on the task specification: *\"{task_description[:200]}{'...' if len(task_description) > 200 else ''}\"*\n"
            f"the analysis yields an overall **{'positive' if positive_pct > 55 else 'mixed'}** sentiment signal "
            f"with a model confidence of **{confidence:.0%}**.\n\n"
            f"> ⚠️ *Demonstration analysis generated from the task specification. "
            f"No real dataset was supplied; outputs are synthetic and illustrative only.*"
        )

        structured_output = {
            "executor": self.executor_name,
            "task_title": task_title,
            "sentiment_distribution": {
                "positive_pct": positive_pct,
                "neutral_pct": neutral_pct,
                "negative_pct": negative_pct,
            },
            "dominant_themes": top_themes,
            "overall_sentiment": "positive" if positive_pct > 55 else "mixed",
            "confidence": confidence,
            "key_observations": [positive_note, negative_note],
            "demo_note": "Synthetic demonstration analysis — no real dataset supplied.",
        }

        log_fn("info", "formatting", "Output formatted and structured result compiled")
        log_fn("info", "complete", f"NLP execution complete — confidence {confidence:.0%}")

        return ExecutorResult(output_text=output_text, structured_output=structured_output,
                              metadata={"executor": self.executor_name, "confidence": confidence})
