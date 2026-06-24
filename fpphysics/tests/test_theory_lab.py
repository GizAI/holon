from fpphysics.theory_lab import LabConfig, TheoryLab


def test_theory_lab_quick_without_global_fits_runs():
    cfg = LabConfig.quick()
    cfg = LabConfig(**{**cfg.as_dict(), "max_clock": 3, "symbolic_trials": 20, "run_global_fits": False, "top_k": 8})
    run = TheoryLab(config=cfg).run()
    assert run.candidates
    assert run.summary["complete_first_principles_derivation_found"] is False
    assert any(c.family == "seeded_candidate" for c in run.candidates)
    assert any(c.family == "target_guided_rg_clock" for c in run.candidates)
