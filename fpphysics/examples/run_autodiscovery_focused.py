import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


from fpphysics.autodiscovery import (
    DiscoveryConfig,
    GaugeSearchConfig,
    SymbolicSearchConfig,
    TheoryDiscoveryEngine,
    VacuumSearchConfig,
    write_csv,
    write_json,
    write_report,
)


if __name__ == "__main__":
    cfg = DiscoveryConfig(
        gauge=GaugeSearchConfig(
            max_clock=13,
            max_scale_denominator=45,
            top_k=30,
            beta_denominator=5,
            min_alpha_u_inv=44,
            max_alpha_u_inv=49,
        ),
        vacuum=VacuumSearchConfig(
            top_k=30,
            min_action_n=70,
            max_action_n=120,
            max_prefactor_power=8,
            action_denominator=4,
        ),
        symbolic=SymbolicSearchConfig(top_k=10, beam_width=80, max_depth=1),
        mode="focused_isdlc_tcps_plus_posthoc_controls",
    )
    out = Path("autodiscovery_run")
    out.mkdir(exist_ok=True)
    result = TheoryDiscoveryEngine(config=cfg).run()
    write_json(str(out / "autodiscovery_results.json"), result)
    write_csv(str(out / "autodiscovery_top_candidates.csv"), result)
    write_report(str(out / "AUTODISCOVERY_REPORT_ko.md"), result)
    print(f"wrote outputs to {out}")
