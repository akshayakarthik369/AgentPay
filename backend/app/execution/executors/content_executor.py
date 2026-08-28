"""
Content Generation Executor — handles Content, Writing, Creative tasks.
Produces structured content draft with headline, sections, and notes.
"""
import hashlib
from typing import List
from app.execution.base import BaseExecutor, ExecutorResult, LogFn

_TONES = ["professional", "conversational", "technical", "educational", "persuasive"]
_FORMATS = ["article", "white paper", "blog post", "executive summary", "structured report"]


def _seed_int(seed_str: str, lo: int, hi: int) -> int:
    digest = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
    return lo + (digest % (hi - lo + 1))


class ContentExecutor(BaseExecutor):

    @property
    def executor_name(self) -> str:
        return "Content Generation Executor"

    @property
    def supported_capabilities(self) -> List[str]:
        return ["content generation", "writing", "content", "copywriting", "creative writing"]

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

        log_fn("info", "init", f"Content Executor initialised for: '{task_title}'")
        log_fn("info", "planning", "Content structure and tone determined")

        seed = task_title + category
        tone_idx = _seed_int(seed + "tone", 0, len(_TONES) - 1)
        fmt_idx = _seed_int(seed + "fmt", 0, len(_FORMATS) - 1)
        tone = _TONES[tone_idx]
        fmt = _FORMATS[fmt_idx]
        word_count = _seed_int(seed + "wc", 350, 850)
        confidence = round(0.80 + (_seed_int(seed + "conf", 0, 18) / 100), 2)

        log_fn("info", "drafting", f"Drafting {fmt} in {tone} tone (~{word_count} words)")

        sections = [
            ("Introduction", f"This {fmt} addresses the core objective: {task_description[:150]}{'...' if len(task_description)>150 else ''}"),
            ("Key Points", f"The following areas are central to {task_title}: domain context, stakeholder value, and actionable outcomes."),
            ("Analysis", f"A {tone} examination of the subject reveals multiple dimensions worth addressing for the target audience."),
            ("Conclusion", f"In conclusion, this content fulfils the requirements of the task specification with a {tone} approach."),
        ]

        output_text = (
            f"# Content Draft — {task_title}\n\n"
            f"**Executor:** {agent_name} | **Format:** {fmt.title()} | **Tone:** {tone.title()}\n\n"
            + "".join(f"## {title}\n{body}\n\n" for title, body in sections) +
            f"---\n*Estimated word count: ~{word_count} words | Readability score: {_seed_int(seed+'read',65,82)}/100*\n\n"
            f"> ⚠️ *Demonstration content draft generated from task specification. "
            f"This is a synthetic skeleton — expand with domain-specific research for production use.*"
        )

        structured_output = {
            "executor": self.executor_name,
            "task_title": task_title,
            "format": fmt,
            "tone": tone,
            "word_count_estimate": word_count,
            "sections": [{"title": t, "preview": b[:100]} for t, b in sections],
            "confidence": confidence,
            "demo_note": "Synthetic demonstration draft — expand with real domain content.",
        }

        log_fn("info", "complete", f"Content draft produced — {len(sections)} sections, ~{word_count} words")
        return ExecutorResult(output_text=output_text, structured_output=structured_output,
                              metadata={"executor": self.executor_name, "confidence": confidence})
