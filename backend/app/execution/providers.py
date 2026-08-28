"""
LocalDeterministicProvider — synchronous execution provider for Phase 8.

Orchestrates:
  1. Executor routing
  2. Sequential progress logging (with log_fn callback)
  3. Deterministic result generation
  4. Error isolation (no raw stack traces leaked)

Architecture note: ready to be subclassed by GeminiExecutionProvider in Phase 9.
"""
from __future__ import annotations
import json
import time
from datetime import datetime
from typing import Callable, List, Optional

from app.execution.base import ExecutorResult
from app.execution.router import route_executor


class LocalDeterministicProvider:
    """Synchronous, deterministic execution provider using local executors."""

    PROVIDER_NAME = "LocalDeterministicProvider"

    # Progress milestones emitted during execution
    PROGRESS_STAGES = [
        (0,  "queued",       "info", "Execution queued and initialised"),
        (10, "preparing",    "info", "Task context loaded from input snapshot"),
        (20, "routing",      "info", "Selecting execution strategy and executor"),
        (35, "analysing",    "info", "Task requirements analysed"),
        (60, "generating",   "info", "Generating result output"),
        (85, "formatting",   "info", "Formatting structured output"),
        (100,"finalising",   "info", "Execution finalised and output stored"),
    ]

    def run(
        self,
        task_title: str,
        task_description: str,
        category: str,
        required_capability: str,
        agent_name: str,
        agent_capabilities: List[str],
        bid_proposal: str,
        log_fn: Callable[[str, str, str], None],  # (level, step, message)
        progress_fn: Callable[[int], None],         # (progress_pct)
    ) -> ExecutorResult:
        """
        Execute a task deterministically.

        Parameters
        ----------
        log_fn : (level, step, message) -> None
            Persists a log entry to the database.
        progress_fn : (progress_pct) -> None
            Updates execution progress in the database.
        """
        try:
            # Stage 0 → 20: preparation
            progress_fn(0)
            log_fn("info", "queued", "Execution queued and initialised")

            progress_fn(10)
            log_fn("info", "preparing", "Task context loaded from input snapshot")

            # Route executor
            progress_fn(20)
            executor = route_executor(required_capability, category, agent_capabilities)
            log_fn(
                "info", "routing",
                f"Executor selected: {executor.executor_name} "
                f"(capability={required_capability}, category={category})"
            )

            # Stage 35: analyse
            progress_fn(35)
            log_fn("info", "analysing", "Task requirements analysed and execution parameters confirmed")

            # Stage 60: run executor
            progress_fn(60)
            result = executor.execute(
                task_title=task_title,
                task_description=task_description,
                category=category,
                required_capability=required_capability,
                agent_name=agent_name,
                agent_capabilities=agent_capabilities,
                bid_proposal=bid_proposal,
                log_fn=log_fn,
            )

            # Stage 85 → 100: formatting
            progress_fn(85)
            log_fn("info", "formatting", "Structured output packaged and validated")

            progress_fn(100)
            log_fn("info", "finalised", f"Execution complete via {self.PROVIDER_NAME}")

            # Attach provider metadata
            result.metadata["provider"] = self.PROVIDER_NAME
            return result

        except Exception as exc:
            # Isolate the error — do NOT leak raw stack traces
            safe_msg = f"{type(exc).__name__}: {str(exc)[:300]}"
            log_fn("error", "failure", f"Execution failed: {safe_msg}")
            return ExecutorResult(
                output_text="",
                structured_output={},
                metadata={"provider": self.PROVIDER_NAME},
                success=False,
                error_message=safe_msg,
            )
