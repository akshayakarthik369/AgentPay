"""
Data Analysis Executor — handles Data Analysis, Analytics, Statistics tasks.
Produces tabular observations, key metrics, and summary insights.
"""
import hashlib
from typing import List
from app.execution.base import BaseExecutor, ExecutorResult, LogFn


def _seed_int(seed_str: str, lo: int, hi: int) -> int:
    digest = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
    return lo + (digest % (hi - lo + 1))


class DataExecutor(BaseExecutor):

    @property
    def executor_name(self) -> str:
        return "Data Analysis & Insights Executor"

    @property
    def supported_capabilities(self) -> List[str]:
        return ["data analysis", "analytics", "statistics", "data science", "data"]

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

        log_fn("info", "init", f"Data Analysis Executor initialised for: '{task_title}'")
        log_fn("info", "profiling", "Dataset profile inferred from task specification")

        seed = task_title + category
        rows = _seed_int(seed + "rows", 450, 2500)
        columns = _seed_int(seed + "cols", 6, 18)
        missing_pct = _seed_int(seed + "miss", 1, 8)
        outlier_pct = _seed_int(seed + "out", 1, 5)
        correlation = round(0.45 + (_seed_int(seed + "corr", 0, 40) / 100), 2)
        confidence = round(0.78 + (_seed_int(seed + "conf", 0, 18) / 100), 2)

        key_metrics = {
            "records_analysed": rows,
            "feature_columns": columns,
            "missing_data_pct": missing_pct,
            "outlier_rate_pct": outlier_pct,
            "primary_correlation": correlation,
        }

        observations = [
            f"Dataset contains {rows:,} synthetic records across {columns} feature dimensions.",
            f"Missing data rate of {missing_pct}% is within acceptable thresholds — imputation not required.",
            f"Outlier detection flagged {outlier_pct}% of records as anomalous using IQR-based methodology.",
            f"Primary feature correlation coefficient: {correlation:.2f} — indicating a {'strong' if correlation > 0.7 else 'moderate'} signal.",
            f"Distribution analysis reveals {'right-skewed' if _seed_int(seed + 'skew', 0, 1) else 'near-normal'} patterns in the primary dependent variable.",
        ]

        log_fn("info", "analysis", f"Analysed {rows:,} synthetic records, {columns} features")
        log_fn("info", "metrics", f"Correlation: {correlation:.2f}, Missing: {missing_pct}%, Outliers: {outlier_pct}%")

        output_text = (
            f"# Data Analysis Report — {task_title}\n\n"
            f"**Executor:** {agent_name} | **Engine:** {self.executor_name}\n\n"
            f"## Dataset Profile (Demonstration)\n"
            f"| Metric | Value |\n|---|---|\n"
            + "".join(f"| {k.replace('_', ' ').title()} | {v} |\n" for k, v in key_metrics.items()) +
            f"\n## Key Observations\n"
            + "".join(f"- {obs}\n" for obs in observations) +
            f"\n## Summary\n"
            f"Analysis of the task domain *'{task_title}'* yields a **{'high' if confidence > 0.88 else 'moderate'}** "
            f"confidence ({confidence:.0%}) analytical result with actionable insights across {len(observations)} "
            f"observed dimensions.\n\n"
            f"> ⚠️ *Demonstration analysis generated from task specification. "
            f"Dataset is synthetic; all figures are illustrative only.*"
        )

        structured_output = {
            "executor": self.executor_name,
            "task_title": task_title,
            "dataset_profile": key_metrics,
            "observations": observations,
            "confidence": confidence,
            "summary": f"{'High' if confidence > 0.88 else 'Moderate'} confidence analytical result produced.",
            "demo_note": "Synthetic demonstration analysis — no real dataset supplied.",
        }

        log_fn("info", "formatting", "Data report compiled and structured")
        log_fn("info", "complete", f"Data analysis complete — confidence {confidence:.0%}")

        return ExecutorResult(output_text=output_text, structured_output=structured_output,
                              metadata={"executor": self.executor_name, "confidence": confidence})
