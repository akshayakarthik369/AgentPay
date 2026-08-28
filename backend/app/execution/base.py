"""
Base classes and data contracts for the AgentPay execution engine.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ExecutorResult:
    """Standardised output produced by any executor."""
    output_text: str                          # Human-readable result
    structured_output: Dict[str, Any]         # Machine-readable JSON-serialisable dict
    metadata: Dict[str, Any] = field(default_factory=dict)  # Routing info, executor name, etc.
    success: bool = True
    error_message: Optional[str] = None


# Type alias for the log-callback injected by the provider
LogFn = Callable[[str, str, str], None]  # (level, step, message)


class BaseExecutor(ABC):
    """Abstract base class for all task executors."""

    @property
    @abstractmethod
    def executor_name(self) -> str:
        """Human-readable name of this executor."""

    @property
    @abstractmethod
    def supported_capabilities(self) -> List[str]:
        """List of capability strings this executor handles (lower-cased)."""

    @abstractmethod
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
        """
        Perform the actual task execution.

        Parameters
        ----------
        task_title, task_description, category, required_capability:
            Frozen task context from the input snapshot.
        agent_name, agent_capabilities:
            The executing agent's profile.
        bid_proposal:
            The agent's original proposal for context.
        log_fn:
            Callable ``(level, step, message)`` used to emit execution log entries.
        """
