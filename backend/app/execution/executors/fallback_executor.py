"""
Fallback Executor — handles unrecognised capabilities and categories.
Produces a generic but task-aware analytical report. Never silently fails.
"""
import hashlib
from typing import List
from app.execution.base import BaseExecutor, ExecutorResult, LogFn


def _seed_int(seed_str: str, lo: int, hi: int) -> int:
    digest = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
    return lo + (digest % (hi - lo + 1))


class FallbackExecutor(BaseExecutor):

    @property
    def executor_name(self) -> str:
        return "General Purpose Fallback Executor"

    @property
    def supported_capabilities(self) -> List[str]:
        return []  # Catches everything not claimed by a specialised executor

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

        log_fn("warning", "routing", f"No specialised executor for capability '{required_capability}' — using Fallback Executor")
        log_fn("info", "init", f"Fallback Executor initialised for: '{task_title}'")
        log_fn("info", "analysis", "Performing general-purpose task analysis")

        seed = task_title + category
        confidence = round(0.65 + (_seed_int(seed + "conf", 0, 20) / 100), 2)
        steps_performed = _seed_int(seed + "steps", 4, 8)

        steps = [
            f"Parsed task objective from specification: '{task_title}'",
            f"Identified domain context: {category} / {required_capability}",
            f"Matched agent capabilities: {', '.join(agent_capabilities[:3]) if agent_capabilities else 'General'}",
            f"Executed {steps_performed} analytical sub-routines against task description",
            "Compiled generalised output with available context",
        ]

        output_text = (
            f"# General Analysis Report — {task_title}\n\n"
            f"**Executor:** {agent_name} | **Engine:** {self.executor_name}\n\n"
            f"## Task Objective\n{task_description[:400]}{'...' if len(task_description) > 400 else ''}\n\n"
            f"## Execution Steps Performed\n"
            + "".join(f"{i+1}. {s}\n" for i, s in enumerate(steps)) +
            f"\n## Output Summary\nA general-purpose analysis was performed against the task specification "
            f"for '{task_title}' within the **{category}** domain. The required capability ({required_capability}) "
            f"was addressed using the agent's available capabilities: {', '.join(agent_capabilities[:3]) if agent_capabilities else 'General'}.\n\n"
            f"**Overall confidence:** {confidence:.0%}\n\n"
            f"> ⚠️ *This task was processed by the Fallback Executor as no specialised executor "
            f"matched the required capability '{required_capability}'. Output is generic and synthetic.*"
        )

        structured_output = {
            "executor": self.executor_name,
            "task_title": task_title,
            "capability_requested": required_capability,
            "category": category,
            "steps_performed": steps,
            "confidence": confidence,
            "routing_note": f"Fallback executor used — no specialised handler for '{required_capability}'",
            "demo_note": "Synthetic generalised output — no specialised executor matched.",
        }

        log_fn("info", "complete", f"Fallback execution complete — confidence {confidence:.0%}")
        return ExecutorResult(output_text=output_text, structured_output=structured_output,
                              metadata={"executor": self.executor_name, "confidence": confidence, "fallback": True})
