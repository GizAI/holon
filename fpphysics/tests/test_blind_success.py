from fpphysics.blind_success import (
    ISDLC_TCPS_MU_GEV,
    conservative_dim6_proton_lifetime_years,
    run_blind_success_challenge,
)


def test_proton_lifetime_bound_is_robustly_above_registry_bound():
    assert ISDLC_TCPS_MU_GEV > 1e16
    assert conservative_dim6_proton_lifetime_years() > 2e34


def test_tier1_blind_success_but_not_strict_certification():
    run = run_blind_success_challenge()
    assert run["summary"]["tier1_pass"] is True
    assert run["summary"]["strict_pass"] is False
    keys = {row["key"] for row in run["tier1_holdout_details"]}
    assert "tau_p_to_e_pi0_years" in keys
    assert "N_eff" in keys
