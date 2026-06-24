"""Human-readable report generation."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .engine import DerivationEngine, EvaluationResult


def _fmt(x: float | None, digits: int = 6) -> str:
    if x is None:
        return "n/a"
    if x == 0:
        return "0"
    ax = abs(x)
    if ax >= 1e5 or ax < 1e-3:
        return f"{x:.{digits}e}"
    return f"{x:.{digits}g}"


def render_markdown_report(engine: DerivationEngine, results: list[EvaluationResult]) -> str:
    lines: list[str] = []
    lines.append("# First-Principles Constants Engine Report")
    lines.append("")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append("")
    lines.append("## Executive conclusion")
    lines.append("")
    lines.append(
        "The implemented, auditable tests do **not** establish a complete zero-parameter derivation of "
        "the fine-structure constant, the cosmological constant, or all Standard-Model couplings. "
        "They do establish which parts are calculable from specified axioms and which numbers remain "
        "boundary conditions in the tested frameworks."
    )
    lines.append("")
    lines.append("## Benchmark targets")
    lines.append("")
    lines.append("| target | value | 1 sigma | unit |")
    lines.append("|---|---:|---:|---|")
    for t in engine.targets.values():
        lines.append(f"| `{t.name}` | {_fmt(t.value, 8)} | {_fmt(t.sigma, 4)} | {t.unit} |")
    lines.append("")
    lines.append("## Model evaluations")
    lines.append("")
    for res in results:
        lines.append(f"### {res.model_name}")
        lines.append("")
        lines.append(f"Free parameters exposed by model: `{', '.join(res.free_parameters) if res.free_parameters else 'none'}`")
        lines.append("")
        lines.append(f"Verdict: **{res.verdict}**")
        lines.append("")
        lines.append("| quantity | predicted | target | residual | z | role |")
        lines.append("|---|---:|---:|---:|---:|---|")
        for score in res.scores.values():
            role = "derived prediction" if score.counted_as_prediction else "fitted/control"
            lines.append(
                f"| `{score.prediction.name}` | {_fmt(score.prediction.value, 8)} | {_fmt(score.target.value, 8)} | "
                f"{_fmt(score.residual, 4)} | {_fmt(score.z, 4)} | {role} |"
            )
        if res.dof_predictive:
            lines.append("")
            lines.append(f"Predictive chi^2/dof: {_fmt(res.chi2_predictive, 6)} / {res.dof_predictive}")
        lines.append("")
        if "ratio_predicted_to_observed" in res.diagnostics:
            lines.append(
                f"Diagnostic ratio predicted/observed: {_fmt(res.diagnostics['ratio_predicted_to_observed'], 4)}"
            )
            lines.append("")
    lines.append("## SM+GR audit")
    lines.append("")
    audit = engine.audit_status()
    count = audit["minimal_sm_parameter_count_without_neutrinos_plus_gravity"]
    lines.append(
        "Minimal SM without neutrino masses plus Newton scale and Lambda has this explicit count: "
        + ", ".join(f"{k}={v}" for k, v in count.items())
        + "."
    )
    lines.append("")
    lines.append("### Parameter-status classification")
    lines.append("")
    lines.append("| symbol | status | reason |")
    lines.append("|---|---|---|")
    for status in audit["sm_parameter_statuses"]:
        lines.append(f"| `{status['symbol']}` | `{status['status']}` | {status['reason']} |")
    lines.append("")
    return "\n".join(lines)


def write_report(path: str | Path) -> Path:
    engine = DerivationEngine()
    results = engine.evaluate_default_models()
    text = render_markdown_report(engine, results)
    out = Path(path)
    out.write_text(text, encoding="utf-8")
    return out
