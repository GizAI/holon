import json
from pathlib import Path
from fpphysics.academic_external_holdout import audit_packet

def test_academic_audit_packet_hash_and_failure(tmp_path):
    packet = {
        'sha256':'dummy',
        'predictions': {
            'CKM_abs_Vtd': 0.008710690688894424,
            'CKM_abs_Vts': 0.041532912940577975,
            'CKM_abs_Vtb': 0.9991155001220742,
            'CKM_gamma_deg': 66.71626827889489,
            'CKM_sin2beta': 0.7452966162888277,
            'neutrino_sum_masses_eV': 0.058574929257125444,
            'beta_decay_mbeta_eV': 0.009052130160788001,
            'proton_p_to_e_pi0_lifetime_years': 8.516862452184991e37,
            'lightest_new_charged_threshold_GeV': 6.0875e16,
            'lightest_new_colored_threshold_GeV': 6.0875e16,
            'quark_ms_over_mb_external': 0.02564102564102564,
            'quark_mc_over_mt_external': 0.007889546351084813,
        }
    }
    p = tmp_path/'packet.json'
    p.write_text(json.dumps(packet))
    res = audit_packet(p)
    assert res['summary']['strict_academic_external_tranche_verdict'] == 'FAIL'
    assert res['summary']['precision_failure_count'] >= 1
    assert res['summary']['not_scoreable_count'] == 4
    assert res['summary']['complete_SM_LCDM_first_principles_derivation_success'] is False
