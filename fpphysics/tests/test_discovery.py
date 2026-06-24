from fpphysics.autodiscovery import (
    DiscoveryConfig,
    GaugeSearchConfig,
    SymbolicSearchConfig,
    TheoryDiscoveryEngine,
    VacuumSearchConfig,
    detect_hardware,
)


def test_discovery_hardware_detection():
    info = detect_hardware()
    assert info.cpu_count is None or info.cpu_count > 0
    assert isinstance(info.numpy_version, str)


def test_tiny_discovery_run_produces_candidates_and_summary():
    cfg = DiscoveryConfig(
        gauge=GaugeSearchConfig(max_clock=3, max_scale_denominator=45, top_k=3, beta_denominator=3, min_alpha_u_inv=44, max_alpha_u_inv=49),
        vacuum=VacuumSearchConfig(top_k=3, min_action_n=92, max_action_n=94, max_prefactor_power=5, action_denominator=2),
        symbolic=SymbolicSearchConfig(top_k=2, beam_width=60, max_depth=1),
        mode="test",
    )
    result = TheoryDiscoveryEngine(config=cfg).run()
    assert result["gauge_candidates"]
    assert result["vacuum_candidates"]
    assert result["symbolic_candidates"]
    assert result["combined_verdict"]["claim_status"] == "candidate_generation_only_not_a_completed_first_principles_derivation"


def test_discovery_quarantines_auto_candidates_from_strict_derivation_count():
    cfg = DiscoveryConfig(
        gauge=GaugeSearchConfig(max_clock=3, max_scale_denominator=45, top_k=3, beta_denominator=3, min_alpha_u_inv=44, max_alpha_u_inv=49),
        vacuum=VacuumSearchConfig(top_k=3, min_action_n=92, max_action_n=94, max_prefactor_power=5, action_denominator=2),
        symbolic=SymbolicSearchConfig(top_k=2, beam_width=60, max_depth=1),
        mode="test",
    )
    result = TheoryDiscoveryEngine(config=cfg).run()
    assert result["strict_quarantine_scores"]
    assert all(r["verdict"] == "control_or_no_genuine_predictions" for r in result["strict_quarantine_scores"])
