"""
Research Executor — handles Research, Investigation, Report, Survey tasks.
Produces structured findings with methodology notes and conclusions.
"""
import hashlib
from typing import List
from app.execution.base import BaseExecutor, ExecutorResult, LogFn

_METHODS = ["literature synthesis", "structured data review", "comparative analysis",
            "pattern identification", "domain knowledge distillation"]

_FINDING_TEMPLATES = [
    "Primary domain actors exhibit strong adoption of {topic}-centric methodologies.",
    "Emerging patterns suggest {topic} is undergoing rapid evolution in Q3–Q4 2025.",
    "Cross-domain evidence indicates significant correlation between {topic} performance and outcome quality.",
    "Longitudinal signals point to growing maturity in {topic} tooling and infrastructure.",
    "Stakeholder surveys (synthetic) reflect moderate to high satisfaction with {topic} deliverables.",
]


def _seed_int(seed_str: str, lo: int, hi: int) -> int:
    digest = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
    return lo + (digest % (hi - lo + 1))


class ResearchExecutor(BaseExecutor):

    @property
    def executor_name(self) -> str:
        return "Research & Investigation Executor"

    @property
    def supported_capabilities(self) -> List[str]:
        return ["research", "investigation", "report", "survey", "literature review"]

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

        log_fn("info", "init", f"Research Executor initialised for: '{task_title}'")
        log_fn("info", "scope", f"Research scope: {category} / {required_capability}")
        log_fn("info", "method", "Applying structured synthesis methodology")

        seed = task_title + category
        topic = task_title.split()[0] if task_title else "domain"
        method_idx = _seed_int(seed + "meth", 0, len(_METHODS) - 1)
        method = _METHODS[method_idx]
        num_findings = _seed_int(seed + "nf", 3, 5)
        finding_indices = [_seed_int(seed + f"f{i}", 0, len(_FINDING_TEMPLATES) - 1) for i in range(num_findings)]
        findings = list(dict.fromkeys([
            _FINDING_TEMPLATES[i].format(topic=topic) for i in finding_indices
        ]))[:num_findings]

        confidence = round(0.72 + (_seed_int(seed + "conf", 0, 22) / 100), 2)
        sources_reviewed = _seed_int(seed + "src", 12, 35)

        log_fn("info", "synthesis", f"Synthesised {len(findings)} key findings across {sources_reviewed} reference sources")

        output_text = (
            f"# Research Report — {task_title}\n\n"
            f"**Executor:** {agent_name} | **Methodology:** {method.title()}\n\n"
            f"## Objective\n{task_description[:300]}{'...' if len(task_description) > 300 else ''}\n\n"
            f"## Key Findings\n"
            + "".join(f"{i+1}. {f}\n" for i, f in enumerate(findings)) +
            f"\n## Methodology Notes\nThis research employed **{method}** across {sources_reviewed} curated "
            f"reference sources within the {category} domain.\n\n"
            f"## Conclusion\nThe evidence base supports a **{'strong' if confidence > 0.85 else 'moderate'}** "
            f"level of confidence ({confidence:.0%}) in the findings presented above.\n\n"
            f"> ⚠️ *Demonstration report generated from task specification. "
            f"No real external sources were queried; findings are synthetic and illustrative only.*"
        )

        structured_output = {
            "executor": self.executor_name,
            "task_title": task_title,
            "methodology": method,
            "sources_reviewed": sources_reviewed,
            "findings": findings,
            "confidence": confidence,
            "conclusion": f"{'Strong' if confidence > 0.85 else 'Moderate'} evidence base identified.",
            "demo_note": "Synthetic demonstration report — no real sources queried.",
        }

        log_fn("info", "formatting", "Research report compiled and structured")
        log_fn("info", "complete", f"Research execution complete — {len(findings)} findings produced")

        return ExecutorResult(output_text=output_text, structured_output=structured_output,
                              metadata={"executor": self.executor_name, "confidence": confidence})
