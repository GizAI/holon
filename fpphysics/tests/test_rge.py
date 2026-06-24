import math

import numpy as np

from fpphysics.constants import load_benchmarks
from fpphysics.rge import electroweak_to_gut_normalized, fit_one_loop_unification, SM_B


def test_gut_normalization_values_are_reasonable():
    b = load_benchmarks()
    c = electroweak_to_gut_normalized(
        b.alpha_hat_5_mz_inv.value,
        b.sin2theta_hat_mz.value,
        b.alpha_s_mz.value,
        b.mz_gev.value,
    )
    d = c.as_dict()
    assert 58.0 < d["alpha1_inv"] < 60.0
    assert 29.0 < d["alpha2_inv"] < 30.0
    assert 8.0 < d["alpha3_inv"] < 9.0
    assert d["g3"] > d["g2"] > d["g1"]


def test_non_susy_unification_predicts_low_alpha_s():
    b = load_benchmarks()
    c = electroweak_to_gut_normalized(
        b.alpha_hat_5_mz_inv.value,
        b.sin2theta_hat_mz.value,
        b.alpha_s_mz.value,
        b.mz_gev.value,
    )
    res = fit_one_loop_unification(c.alpha_inv, b.mz_gev.value, SM_B)
    pred_alpha_s = res.predicted_alphas_mz[2]
    assert 0.06 < pred_alpha_s < 0.08
    assert abs(pred_alpha_s - b.alpha_s_mz.value) > 0.03
