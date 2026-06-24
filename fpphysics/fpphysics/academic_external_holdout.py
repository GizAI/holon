"""Academic freeze-before-reveal external holdout audit.

This module deliberately scores a single frozen candidate packet without changing
its formulas or choosing a candidate after reveal.  It is designed to make abuse
visible rather than to force a positive result.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib, json, math
from typing import Any, Dict, List

@dataclass(frozen=True)
class Observation:
    name: str
    domain: str
    kind: str
    central: float | None = None
    sigma_minus: float | None = None
    sigma_plus: float | None = None
    limit: float | None = None
    cl: str = ""
    source: str = ""
    reason: str = ""

@dataclass
class ScoreRow:
    quantity: str
    domain: str
    prediction: float | str | None
    status: str
    central: float | None = None
    sigma_minus: float | None = None
    sigma_plus: float | None = None
    z: float | None = None
    abs_z: float | None = None
    limit: float | None = None
    ratio_to_limit: float | None = None
    cl: str = ""
    source: str = ""
    note: str = ""

EXTERNAL_TRANCHE: List[Observation] = [
    Observation('CKM_abs_Vtd','CKM_external','gaussian',0.00858,0.00017,0.00019,source='PDG CKM matrix global fit 2025 Eq. 12.27'),
    Observation('CKM_abs_Vts','CKM_external','gaussian',0.04111,0.00068,0.00077,source='PDG CKM matrix global fit 2025 Eq. 12.27'),
    Observation('CKM_abs_Vtb','CKM_external','gaussian',0.999118,0.000034,0.000029,source='PDG CKM matrix global fit 2025 Eq. 12.27'),
    Observation('CKM_gamma_deg','CKM_external','gaussian',65.7,3.0,3.0,source='PDG CKM gamma average'),
    Observation('CKM_sin2beta','CKM_external','gaussian',0.709,0.011,0.011,source='PDG CKM sin2beta world average'),
    Observation('neutrino_sum_masses_eV','cosmology_bound','upper_bound',limit=0.12,cl='95%',source='Planck 2018 + BAO'),
    Observation('beta_decay_mbeta_eV','direct_neutrino_mass_bound','upper_bound',limit=0.45,cl='90%',source='KATRIN 259-day 2025'),
    Observation('proton_p_to_e_pi0_lifetime_years','proton_decay_bound','lower_bound',limit=2.4e34,cl='90%',source='Super-K p->e+pi0'),
    Observation('lightest_new_charged_threshold_GeV','threshold_spectrum','not_scoreable',reason='No model-independent collider bound for unspecified representation/couplings/decays.'),
    Observation('lightest_new_colored_threshold_GeV','threshold_spectrum','not_scoreable',reason='No model-independent collider bound for unspecified representation/couplings/decays.'),
    Observation('quark_ms_over_mb_external','quark_mass_ratio','not_scoreable',reason='No common MSbar scale/RGE matching specified; direct PDG mass ratio is scheme/scale inconsistent.'),
    Observation('quark_mc_over_mt_external','quark_mass_ratio','not_scoreable',reason='No common MSbar/top mass definition specified; direct ratio is scheme-dependent.'),
]

DIAGNOSTIC_OBS: List[Observation] = [
    Observation('PMNS_sin2_theta12_diagnostic','diagnostic_PMNS','gaussian',0.308,0.011,0.012,source='NuFIT 6.0 IC24+SK NO'),
    Observation('PMNS_sin2_theta23_diagnostic','diagnostic_PMNS','gaussian',0.470,0.013,0.017,source='NuFIT 6.0 IC24+SK NO'),
    Observation('PMNS_sin2_theta13_diagnostic','diagnostic_PMNS','gaussian',0.02215,0.00058,0.00056,source='NuFIT 6.0 IC24+SK NO'),
]

def canonical_sha256_without_embedded_sha(packet: Dict[str, Any]) -> str:
    obj = {k: v for k, v in packet.items() if k != 'sha256'}
    data = json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    return hashlib.sha256(data).hexdigest()

def score_one(predictions: Dict[str, Any], obs: Observation, diagnostic: bool=False) -> ScoreRow:
    value = predictions.get(obs.name)
    if value is None:
        return ScoreRow(obs.name, obs.domain, None, 'missing_prediction', source=obs.source, note='declared target but no prediction')
    if obs.kind == 'gaussian':
        assert obs.central is not None and obs.sigma_minus is not None and obs.sigma_plus is not None
        sigma = obs.sigma_plus if value >= obs.central else obs.sigma_minus
        z = (value - obs.central) / sigma
        prefix = 'diagnostic_' if diagnostic else ''
        status = prefix + ('pass_3sigma' if abs(z) <= 3 else 'fail_gt_3sigma')
        return ScoreRow(obs.name, obs.domain, value, status, obs.central, obs.sigma_minus, obs.sigma_plus, z, abs(z), source=obs.source)
    if obs.kind == 'upper_bound':
        assert obs.limit is not None
        ratio = value / obs.limit
        return ScoreRow(obs.name, obs.domain, value, 'pass_upper_bound' if value < obs.limit else 'fail_upper_bound', limit=obs.limit, ratio_to_limit=ratio, cl=obs.cl, source=obs.source, note='bound only; not a precision hit')
    if obs.kind == 'lower_bound':
        assert obs.limit is not None
        ratio = value / obs.limit
        return ScoreRow(obs.name, obs.domain, value, 'pass_lower_bound' if value > obs.limit else 'fail_lower_bound', limit=obs.limit, ratio_to_limit=ratio, cl=obs.cl, source=obs.source, note='bound only; not a precision hit')
    return ScoreRow(obs.name, obs.domain, value, 'not_scoreable_academic', source=obs.source, note=obs.reason)

def audit_packet(packet_path: str | Path) -> Dict[str, Any]:
    path = Path(packet_path)
    packet = json.loads(path.read_text())
    preds = packet.get('predictions', {})
    rows = [score_one(preds, obs) for obs in EXTERNAL_TRANCHE]
    diagnostics = [score_one(preds, obs, diagnostic=True) for obs in DIAGNOSTIC_OBS]
    omega = (6/13)/4
    zomega = (omega - 0.120) / 0.001
    diagnostics.append(ScoreRow('Omega_c_h2_formula_diagnostic','diagnostic_LCDM',omega,'diagnostic_fail_gt_3sigma' if abs(zomega)>3 else 'diagnostic_pass_3sigma',0.120,0.001,0.001,zomega,abs(zomega),source='Planck 2018 base LCDM; formula from earlier Cabibbo-clock candidate'))
    numeric_rows = [r for r in rows if r.z is not None]
    chi2 = sum(float(r.z)**2 for r in numeric_rows)
    precision_failures = [r for r in rows if r.status == 'fail_gt_3sigma']
    not_score = [r for r in rows if r.status == 'not_scoreable_academic']
    summary = {
        'packet_embedded_sha256': packet.get('sha256'),
        'packet_canonical_without_embedded_sha256': canonical_sha256_without_embedded_sha(packet),
        'packet_raw_file_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'external_precision_numeric_count': len(numeric_rows),
        'external_precision_chi2': chi2,
        'external_precision_reduced_chi2': chi2 / max(len(numeric_rows), 1),
        'external_precision_max_abs_z': max((float(r.abs_z) for r in numeric_rows), default=None),
        'precision_failure_count': len(precision_failures),
        'not_scoreable_count': len(not_score),
        'strict_academic_external_tranche_verdict': 'FAIL' if precision_failures or not_score else 'PASS',
        'complete_SM_LCDM_first_principles_derivation_success': False,
    }
    return {
        'packet': packet,
        'summary': summary,
        'external_tranche_rows': [asdict(r) for r in rows],
        'diagnostic_rows_not_part_of_strict_external_tranche': [asdict(r) for r in diagnostics],
        'external_tranche_definitions': [asdict(o) for o in EXTERNAL_TRANCHE],
    }
