"""
Code Analysis Executor — handles Code Review, Code Analysis, Security Audit tasks.
Produces code quality assessment, issue summary, and recommendations.
"""
import hashlib
from typing import List
from app.execution.base import BaseExecutor, ExecutorResult, LogFn

_ISSUE_CATEGORIES = [
    "Potential null-reference patterns in exception handling paths",
    "Missing input validation on boundary conditions",
    "Hardcoded configuration values detected in module logic",
    "Redundant computation identified in inner loop structures",
    "Insufficient test coverage for edge-case branches",
    "Documentation gaps in public API surface",
    "Inconsistent error propagation strategy across modules",
]

_RECOMMENDATIONS = [
    "Introduce structured logging at key decision points for auditability",
    "Refactor repeated logic into reusable utility functions",
    "Add explicit type annotations to improve IDE tooling and review quality",
    "Expand unit test coverage to cover boundary and failure paths",
    "Adopt consistent error-handling patterns across the codebase",
]


def _seed_int(seed_str: str, lo: int, hi: int) -> int:
    digest = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
    return lo + (digest % (hi - lo + 1))


class CodeExecutor(BaseExecutor):

    @property
    def executor_name(self) -> str:
        return "Code Analysis & Review Executor"

    @property
    def supported_capabilities(self) -> List[str]:
        return ["code analysis", "code review", "security audit", "static analysis", "code"]

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

        log_fn("info", "init", f"Code Analysis Executor initialised for: '{task_title}'")
        log_fn("info", "parsing", "Parsing task context and inferring codebase scope")

        seed = task_title + category
        num_issues = _seed_int(seed + "issues", 2, 5)
        severity_score = _seed_int(seed + "sev", 3, 7)  # out of 10
        quality_score = 10 - severity_score + _seed_int(seed + "qual", 0, 2)
        quality_score = min(quality_score, 10)
        confidence = round(0.80 + (_seed_int(seed + "conf", 0, 16) / 100), 2)
        lines_reviewed = _seed_int(seed + "loc", 200, 1800)

        issue_indices = [_seed_int(seed + f"i{i}", 0, len(_ISSUE_CATEGORIES) - 1) for i in range(num_issues)]
        issues = list(dict.fromkeys([_ISSUE_CATEGORIES[i] for i in issue_indices]))[:num_issues]

        rec_idx = _seed_int(seed + "rec", 0, len(_RECOMMENDATIONS) - 2)
        recommendations = _RECOMMENDATIONS[rec_idx: rec_idx + 3]

        log_fn("info", "review", f"Reviewed {lines_reviewed:,} synthetic LOC — found {len(issues)} notable issues")
        log_fn("info", "scoring", f"Code quality score: {quality_score}/10 | Severity: {severity_score}/10")

        output_text = (
            f"# Code Analysis Report — {task_title}\n\n"
            f"**Executor:** {agent_name} | **Engine:** {self.executor_name}\n\n"
            f"## Assessment Summary\n"
            f"| Metric | Value |\n|---|---|\n"
            f"| Lines Reviewed | {lines_reviewed:,} (synthetic) |\n"
            f"| Issues Identified | {len(issues)} |\n"
            f"| Quality Score | {quality_score}/10 |\n"
            f"| Severity Score | {severity_score}/10 |\n"
            f"| Review Confidence | {confidence:.0%} |\n\n"
            f"## Issues Found\n"
            + "".join(f"- ⚠️  {issue}\n" for issue in issues) +
            f"\n## Recommendations\n"
            + "".join(f"{i+1}. {rec}\n" for i, rec in enumerate(recommendations)) +
            f"\n## Conclusion\nThe codebase demonstrates a **{'good' if quality_score >= 7 else 'fair'}** "
            f"overall quality profile. Priority should be placed on addressing the {len(issues)} "
            f"identified issues before production deployment.\n\n"
            f"> ⚠️ *Demonstration code review generated from task specification. "
            f"No real source code was supplied; findings are synthetic and illustrative only.*"
        )

        structured_output = {
            "executor": self.executor_name,
            "task_title": task_title,
            "lines_reviewed": lines_reviewed,
            "issues_found": issues,
            "issue_count": len(issues),
            "quality_score": quality_score,
            "severity_score": severity_score,
            "recommendations": recommendations,
            "confidence": confidence,
            "overall_grade": "good" if quality_score >= 7 else "fair",
            "demo_note": "Synthetic demonstration code review — no real code supplied.",
        }

        log_fn("info", "formatting", "Code review compiled and structured")
        log_fn("info", "complete", f"Code analysis complete — {len(issues)} issues, quality {quality_score}/10")

        return ExecutorResult(output_text=output_text, structured_output=structured_output,
                              metadata={"executor": self.executor_name, "confidence": confidence})
