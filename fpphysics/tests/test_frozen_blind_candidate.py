from fpphysics.frozen_blind_candidate import (
    FrozenRationalClockParameters,
    packet_isdlc_tcps_rational_clock_texture,
    score_frozen_candidate,
)


def test_frozen_rational_clock_candidate_scores_blind_pass_on_bundled_registry():
    report = score_frozen_candidate()
    assert report.verdict == "blind_pass_needs_independent_replication"
    blind = report.split_scores["blind"]
    assert blind.predicted_required >= 8
    assert blind.coverage >= 0.35
    assert blind.max_abs_z is not None and blind.max_abs_z <= 5.0


def test_frozen_candidate_declares_no_holdout_leakage():
    packet = packet_isdlc_tcps_rational_clock_texture()
    assert packet.uses_holdout_values is False
    assert not any(k in packet.trained_on for k in packet.predictions if k.startswith("V"))
    assert packet.free_parameter_count == 0


def test_threshold_and_proton_lifetime_are_far_above_working_bounds():
    p = FrozenRationalClockParameters()
    assert p.threshold_scale_gev() > 1.0e15
    assert p.proton_lifetime_years() > 1.0e35
