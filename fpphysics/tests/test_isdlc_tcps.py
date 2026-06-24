from fpphysics.candidate_models import (
    ISDLCTCPSOneLoopGaugeModel,
    ISDLCTCPSCosmologicalAnsatzModel,
)
from fpphysics.engine import DerivationEngine


def test_isdlc_tcps_gauge_predictions_are_reproducible():
    res = DerivationEngine().evaluate(ISDLCTCPSOneLoopGaugeModel())
    assert res.verdict == "tension"
    assert abs(res.scores["alpha_em_inv_mz"].prediction.value - 127.9077332788044) < 1e-10
    assert abs(res.scores["sin2theta_hat_mz"].prediction.value - 0.2312790123121689) < 1e-15
    assert abs(res.scores["alpha3_mz"].prediction.value - 0.11804865399076522) < 1e-15
    assert res.max_abs_z_predictive is not None
    assert 2.7 < res.max_abs_z_predictive < 2.9


def test_isdlc_tcps_beta_audit_exact_values():
    diag = DerivationEngine().evaluate(ISDLCTCPSOneLoopGaugeModel()).diagnostics
    beta = diag["beta_audit_exact"]
    assert beta["b4"] == "-7"
    assert beta["b2L"] == "-3"
    assert beta["b2R"] == "2"
    assert beta["B1_PS_effective"] == "-8/5"


def test_isdlc_tcps_cosmological_ansatz_is_order_but_not_precision():
    res = DerivationEngine().evaluate(ISDLCTCPSCosmologicalAnsatzModel())
    assert res.verdict == "fails_current_scored_tests"
    ratio = res.diagnostics["ratio_predicted_to_observed_rho"]
    assert 2.8 < ratio < 2.9
