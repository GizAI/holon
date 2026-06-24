from fpphysics.blind_protocol import (
    BlindPredictionProtocol,
    default_observation_registry,
    packet_from_isdlc_tcps,
    packet_frozen_clock_texture_minimal_thermal,
    packet_oracle_leakage_control,
    packet_toy_texture_control,
    run_default_blind_challenge,
)


def test_blind_protocol_rejects_gauge_only_seed_for_no_holdout_predictions():
    proto = BlindPredictionProtocol(default_observation_registry())
    report = proto.score_packet(packet_from_isdlc_tcps())
    assert report.verdict == "no_or_too_few_blind_predictions"
    assert report.split_scores["blind"].predicted_required == 0


def test_blind_protocol_rejects_leaky_oracle_even_if_numerically_perfect():
    obs = default_observation_registry()
    proto = BlindPredictionProtocol(obs)
    report = proto.score_packet(packet_oracle_leakage_control(obs))
    assert report.verdict == "invalid_due_to_holdout_leakage"
    assert report.leakage_flags


def test_blind_protocol_scores_toy_texture_but_does_not_certify():
    proto = BlindPredictionProtocol(default_observation_registry())
    report = proto.score_packet(packet_toy_texture_control())
    assert report.split_scores["blind"].predicted_required >= 8
    assert report.verdict in {"blind_failed_or_overfit_tension", "insufficient_blind_coverage", "blind_pass_needs_independent_replication"}
    assert report.verdict != "invalid_due_to_holdout_leakage"


def test_default_blind_challenge_runs_without_lab():
    run = run_default_blind_challenge(include_lab=False)
    assert run.summary["candidate_count"] == 4
    assert run.summary["blind_pass_count"] == 1



def test_frozen_clock_texture_candidate_passes_current_bundled_holdout():
    proto = BlindPredictionProtocol(default_observation_registry())
    report = proto.score_packet(packet_frozen_clock_texture_minimal_thermal())
    assert report.verdict == "blind_pass_needs_independent_replication"
    assert report.split_scores["blind"].predicted_required >= 8
    assert report.leakage_flags == ()

