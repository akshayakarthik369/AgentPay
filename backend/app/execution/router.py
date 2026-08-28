"""
Executor router — selects the right executor based on required_capability and category.
"""
from typing import List
from app.execution.base import BaseExecutor
from app.execution.executors.nlp_executor import NLPExecutor
from app.execution.executors.research_executor import ResearchExecutor
from app.execution.executors.data_executor import DataExecutor
from app.execution.executors.code_executor import CodeExecutor
from app.execution.executors.content_executor import ContentExecutor
from app.execution.executors.fallback_executor import FallbackExecutor

# All specialised executors in priority order
_EXECUTORS: List[BaseExecutor] = [
    NLPExecutor(),
    ResearchExecutor(),
    DataExecutor(),
    CodeExecutor(),
    ContentExecutor(),
]

_FALLBACK = FallbackExecutor()


def route_executor(
    required_capability: str,
    category: str,
    agent_capabilities: List[str],
) -> BaseExecutor:
    """
    Select the most appropriate executor for a task.

    Matching strategy (in order):
    1. Match required_capability (case-insensitive) against executor.supported_capabilities
    2. Match category (case-insensitive)
    3. Match any agent capability against executor.supported_capabilities
    4. Return FallbackExecutor
    """
    req_cap_lower = (required_capability or "").lower().strip()
    cat_lower = (category or "").lower().strip()
    agent_caps_lower = [c.lower().strip() for c in (agent_capabilities or [])]

    for executor in _EXECUTORS:
        supported = [s.lower() for s in executor.supported_capabilities]
        # Primary: required_capability exact or partial match
        if any(req_cap_lower == s or req_cap_lower in s or s in req_cap_lower for s in supported):
            return executor
        # Secondary: category match
        if any(cat_lower == s or cat_lower in s or s in cat_lower for s in supported):
            return executor

    # Tertiary: any agent capability
    for executor in _EXECUTORS:
        supported = [s.lower() for s in executor.supported_capabilities]
        if any(cap in supported or any(cap in s or s in cap for s in supported) for cap in agent_caps_lower):
            return executor

    return _FALLBACK
