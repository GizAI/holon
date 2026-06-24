import math

from fpphysics.blind_cabibbo import (
    CLOCK_RATIO,
    CabibboClockFormulaBook,
    conservative_dim6_proton_lifetime_years,
    packet_isdlc_tcps_cabibbo_clock_extension,
    run_cabibbo_clock_blind_challenge,
)


def test_cabibbo_clock_formula_book_is_fixed():
    fb = CabibboClockFormulaBook()
    assert CLOCK_RATIO == 6 / 13
    assert math.isclose(fb.lambda_c, math.sqrt(6 / 13) / 3)
    assert math.isclose(fb.pmns_sin2_theta13, (6 / 13) ** 2 / 9)


def test_cabibbo_packet_has_no_declared_holdout_leakage():
    packet = packet_isdlc_tcps_cabibbo_clock_extension()
    assert packet.uses_holdout_values is False
    assert packet.free_parameter_count == 0
    assert "Vus" in packet.predictions
    assert "Omega_c_h2" in packet.predictions


def test_proton_lifetime_lower_envelope_is_above_bound():
    assert conservative_dim6_proton_lifetime_years() > 2e34


def test_cabibbo_clock_passes_current_publication_tier_but_not_complete_derivation():
    run = run_cabibbo_clock_blind_challenge()
    assert run["summary"]["publication_tier_pass"] is True
    assert run["summary"]["default_strict_pass"] is True
    assert run["summary"]["blind_predicted_required"] >= 14
    assert run["summary"]["blind_max_abs_z"] <= 3.0
    assert run["summary"]["complete_first_principles_derivation"] is False
    assert "me_over_mmu" in run["summary"]["missing_required"]
