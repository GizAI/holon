from __future__ import annotations
import csv, json, math, hashlib, shutil, zipfile
from pathlib import Path
from datetime import datetime, timezone

PACKET_PATH = Path('/mnt/data/strict_freeze_external_holdout/external_holdout_frozen_packet.json')
OUT = Path('/mnt/data/academic_external_holdout_audit_v0_7')
OUT.mkdir(exist_ok=True)

packet = json.loads(PACKET_PATH.read_text())
pred = packet['predictions']
raw_sha = hashlib.sha256(PACKET_PATH.read_bytes()).hexdigest()
canon_obj = {k:v for k,v in packet.items() if k!='sha256'}
canon_sha = hashlib.sha256(json.dumps(canon_obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()

# External tranche values. These are loaded after the frozen packet in this script.
# Gaussian sigma asymmetry: use sigma_plus when prediction > central, sigma_minus when prediction < central.
tranche = [
    dict(name='CKM_abs_Vtd', domain='CKM_external', kind='gaussian', central=0.00858, sigma_minus=0.00017, sigma_plus=0.00019, source='PDG CKM matrix global fit 2025 Eq. 12.27'),
    dict(name='CKM_abs_Vts', domain='CKM_external', kind='gaussian', central=0.04111, sigma_minus=0.00068, sigma_plus=0.00077, source='PDG CKM matrix global fit 2025 Eq. 12.27'),
    dict(name='CKM_abs_Vtb', domain='CKM_external', kind='gaussian', central=0.999118, sigma_minus=0.000034, sigma_plus=0.000029, source='PDG CKM matrix global fit 2025 Eq. 12.27'),
    dict(name='CKM_gamma_deg', domain='CKM_external', kind='gaussian', central=65.7, sigma_minus=3.0, sigma_plus=3.0, source='PDG CKM review 2025 gamma average'),
    dict(name='CKM_sin2beta', domain='CKM_external', kind='gaussian', central=0.709, sigma_minus=0.011, sigma_plus=0.011, source='PDG CKM review 2025 sin2beta world average'),
    dict(name='neutrino_sum_masses_eV', domain='cosmology_bound', kind='upper_bound', limit=0.12, cl='95%', source='Planck 2018 + BAO bound'),
    dict(name='beta_decay_mbeta_eV', domain='direct_neutrino_mass_bound', kind='upper_bound', limit=0.45, cl='90%', source='KATRIN 259-day 2025 bound'),
    dict(name='proton_p_to_e_pi0_lifetime_years', domain='proton_decay_bound', kind='lower_bound', limit=2.4e34, cl='90%', source='Super-K p->e+pi0 450 kton-year bound'),
    dict(name='lightest_new_charged_threshold_GeV', domain='threshold_spectrum', kind='not_scoreable', reason='No model-independent collider bound exists for an unspecified charged threshold representation/couplings/decays. Prediction is only decoupled-at-GUT-scale, not an externally resolved spectrum.'),
    dict(name='lightest_new_colored_threshold_GeV', domain='threshold_spectrum', kind='not_scoreable', reason='No model-independent collider bound exists for an unspecified colored threshold representation/couplings/decays. Prediction is only decoupled-at-GUT-scale, not an externally resolved spectrum.'),
    dict(name='quark_ms_over_mb_external', domain='quark_mass_ratio', kind='not_scoreable', reason='Frozen prediction does not specify common MSbar scale/RGE matching. PDG quotes m_s at 2 GeV and m_b at μ=m_b; direct ratio is scheme/scale inconsistent.'),
    dict(name='quark_mc_over_mt_external', domain='quark_mass_ratio', kind='not_scoreable', reason='Frozen prediction does not specify common MSbar scale/RGE/top mass definition. PDG top mass has direct/pole/MS ambiguities.'),
]

rows=[]
chi2=0.0
numeric=0
failures=[]
passes=[]
not_score=[]
for obs in tranche:
    name=obs['name']
    p = pred.get(name)
    if p is None:
        row = dict(quantity=name, domain=obs['domain'], prediction='', status='missing_prediction', note='declared target but no prediction present')
        failures.append(row)
    elif obs['kind']=='gaussian':
        sigma = obs['sigma_plus'] if p >= obs['central'] else obs['sigma_minus']
        z = (p-obs['central'])/sigma
        status = 'pass_3sigma' if abs(z)<=3 else 'fail_gt_3sigma'
        row = dict(quantity=name, domain=obs['domain'], prediction=p, central=obs['central'], sigma_minus=obs['sigma_minus'], sigma_plus=obs['sigma_plus'], z=z, abs_z=abs(z), status=status, source=obs['source'], note='')
        numeric += 1; chi2 += z*z
        (passes if status.startswith('pass') else failures).append(row)
    elif obs['kind']=='upper_bound':
        ratio = p/obs['limit']
        status = 'pass_upper_bound' if p < obs['limit'] else 'fail_upper_bound'
        row = dict(quantity=name, domain=obs['domain'], prediction=p, limit=obs['limit'], cl=obs.get('cl',''), ratio_to_limit=ratio, status=status, source=obs['source'], note='bound only; not a precision hit')
        (passes if status.startswith('pass') else failures).append(row)
    elif obs['kind']=='lower_bound':
        ratio = p/obs['limit']
        status = 'pass_lower_bound' if p > obs['limit'] else 'fail_lower_bound'
        row = dict(quantity=name, domain=obs['domain'], prediction=p, limit=obs['limit'], cl=obs.get('cl',''), ratio_to_limit=ratio, status=status, source=obs['source'], note='bound only; not a precision hit')
        (passes if status.startswith('pass') else failures).append(row)
    else:
        row = dict(quantity=name, domain=obs['domain'], prediction=p, status='not_scoreable_academic', note=obs['reason'])
        not_score.append(row)
    rows.append(row)

# Diagnostic PMNS and LCDM values from the same frozen packet, not in strict external target list; include to expose known tensions.
diagnostics = [
    dict(name='PMNS_sin2_theta12_diagnostic', domain='diagnostic_PMNS', kind='gaussian', central=0.308, sigma_minus=0.011, sigma_plus=0.012, source='NuFIT 6.0 IC24+SK NO'),
    dict(name='PMNS_sin2_theta23_diagnostic', domain='diagnostic_PMNS', kind='gaussian', central=0.470, sigma_minus=0.013, sigma_plus=0.017, source='NuFIT 6.0 IC24+SK NO'),
    dict(name='PMNS_sin2_theta13_diagnostic', domain='diagnostic_PMNS', kind='gaussian', central=0.02215, sigma_minus=0.00058, sigma_plus=0.00056, source='NuFIT 6.0 IC24+SK NO'),
]
# Omega_c not in strict packet, but source formula book predicted it; included as prior candidate diagnostic if available from older packet not here.
# Compute omega from r=6/13 if allowed by formula book; mark diagnostic not external target.
omega_c_pred = (6/13)/4
for d in diagnostics:
    p=pred.get(d['name'])
    sigma=d['sigma_plus'] if p>=d['central'] else d['sigma_minus']
    z=(p-d['central'])/sigma
    d.update(prediction=p,z=z,abs_z=abs(z),status='diagnostic_pass_3sigma' if abs(z)<=3 else 'diagnostic_fail_gt_3sigma')
# add Ωc diagnostic
z_omega=(omega_c_pred-0.120)/0.001
diagnostics.append(dict(name='Omega_c_h2_formula_diagnostic',domain='diagnostic_LCDM',prediction=omega_c_pred,central=0.120,sigma_minus=0.001,sigma_plus=0.001,z=z_omega,abs_z=abs(z_omega),status='diagnostic_fail_gt_3sigma' if abs(z_omega)>3 else 'diagnostic_pass_3sigma',source='Planck 2018 base LCDM; formula from earlier Cabibbo clock candidate'))

summary = {
    'audit_name': 'academic_external_holdout_audit_v0_7',
    'generated_utc': datetime.now(timezone.utc).isoformat(),
    'packet_path': str(PACKET_PATH),
    'packet_embedded_sha256': packet.get('sha256'),
    'packet_raw_file_sha256': raw_sha,
    'packet_canonical_without_embedded_sha256': canon_sha,
    'source_packet_sha256': packet.get('source_packet_sha256'),
    'external_precision_numeric_count': numeric,
    'external_precision_chi2': chi2,
    'external_precision_reduced_chi2': chi2/max(numeric,1),
    'external_precision_max_abs_z': max((r.get('abs_z',0) for r in rows if 'abs_z' in r), default=None),
    'external_precision_failures': [r for r in rows if r.get('status') == 'fail_gt_3sigma'],
    'bound_pass_count': sum(1 for r in rows if r.get('status','').startswith('pass_') and 'bound' in r.get('status','')),
    'not_scoreable_count': len(not_score),
    'strict_academic_external_tranche_verdict': 'FAIL' if any(r.get('status')=='fail_gt_3sigma' for r in rows) or len(not_score)>0 else 'PASS',
    'partial_positive_result': 'CKM Vtd/Vts/Vtb/gamma pass; neutrino-sum, beta-decay, proton bound pass; sin2beta fails >3σ; thresholds and quark ratios are not publication-grade scoreable as frozen.',
    'complete_SM_LCDM_first_principles_derivation_success': False,
    'why_not_complete': [
        'alpha(0), charged-lepton Yukawa ratios, full quark/lepton Yukawa matrices, Higgs-sector parameters, neutrino CP phase/absolute scale likelihood, and all six ΛCDM parameters are not derived from a microscopic action.',
        'The packet has a >3σ failure in sin2β in the new CKM external tranche.',
        'Threshold spectrum is not resolved into representations/couplings/decays, so collider comparison is not well-defined.',
        'Quark mass ratios lack a common renormalization scheme and matching scale.'
    ]
}

result={'packet':packet,'summary':summary,'external_tranche_rows':rows,'diagnostic_rows_not_part_of_strict_external_tranche':diagnostics,'external_tranche_definitions':tranche}
(OUT/'academic_external_holdout_results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
shutil.copy(PACKET_PATH, OUT/'frozen_packet_pre_reveal_copy.json')
shutil.copy('/mnt/data/strict_freeze_external_holdout/PRE_REVEAL_FREEZE_MANIFEST.md', OUT/'PRE_REVEAL_FREEZE_MANIFEST.md')

# CSV rows
all_fields=[]
for r in rows+diagnostics:
    for k in r:
        if k not in all_fields: all_fields.append(k)
with open(OUT/'academic_external_holdout_scores.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=all_fields)
    w.writeheader(); w.writerows(rows+diagnostics)

# MD report
fmt=lambda x: f'{x:.6g}' if isinstance(x,(int,float)) and x!=0 and (abs(x)>=1e-4 and abs(x)<1e6) else (f'{x:.6e}' if isinstance(x,float) else str(x))
md=[]
md.append('# Academic external freeze-before-reveal audit v0.7')
md.append('')
md.append('## Bottom line')
md.append('이 감사는 frozen packet을 수정하지 않고 새 외부 holdout tranche에 대입했다. 학계 방어 기준으로는 **부분 양성 신호는 있지만 엄격 성공은 아니다**.')
md.append('')
md.append(f'- strict academic external verdict: `{summary["strict_academic_external_tranche_verdict"]}`')
md.append(f'- complete SM+ΛCDM first-principles derivation: `{summary["complete_SM_LCDM_first_principles_derivation_success"]}`')
md.append(f'- precision numeric count: `{numeric}`')
md.append(f'- reduced chi2 over precision external tranche: `{summary["external_precision_reduced_chi2"]:.4f}`')
md.append(f'- max |z|: `{summary["external_precision_max_abs_z"]:.4f}`')
md.append('')
md.append('## Frozen packet integrity')
md.append(f'- embedded packet hash: `{packet.get("sha256")}`')
md.append(f'- canonical-without-embedded-sha hash: `{canon_sha}`')
md.append(f'- raw file SHA256: `{raw_sha}`')
md.append(f'- source packet SHA256: `{packet.get("source_packet_sha256")}`')
md.append('')
md.append('## Strict external tranche results')
md.append('| target | prediction | target / bound | z or ratio | status |')
md.append('|---|---:|---:|---:|---|')
for r in rows:
    target=''
    metric=''
    if 'central' in r:
        target=f"{fmt(r['central'])}"
        metric=f"z={fmt(r['z'])}"
    elif 'limit' in r:
        sign='<' if 'upper' in r['status'] else '>'
        target=f"{sign} {fmt(r['limit'])}"
        metric=f"ratio={fmt(r['ratio_to_limit'])}"
    else:
        target='not well-defined'
        metric='not scored'
    md.append(f"| `{r['quantity']}` | {fmt(r.get('prediction',''))} | {target} | {metric} | `{r['status']}` |")
md.append('')
md.append('## Diagnostic rows, not counted as strict external tranche')
md.append('| diagnostic | prediction | target | z | status |')
md.append('|---|---:|---:|---:|---|')
for r in diagnostics:
    md.append(f"| `{r['name']}` | {fmt(r['prediction'])} | {fmt(r['central'])} | {fmt(r['z'])} | `{r['status']}` |")
md.append('')
md.append('## Interpretation')
md.append('- CKM 외부 tranche에서 `Vtd`, `Vts`, `Vtb`, `gamma`는 3σ 안에 들어간다.')
md.append('- `sin2beta`는 3σ를 넘는 실패다. CKM 전체의 publication-grade blind success라고 쓰면 안 된다.')
md.append('- neutrino sum mass, beta-decay effective mass, proton lifetime은 lower/upper bound 통과지만 precision prediction 성공은 아니다.')
md.append('- threshold spectrum은 표현/결합/붕괴모드가 지정되지 않아 collider bound와 학술적으로 채점할 수 없다.')
md.append('- quark mass ratios는 common MSbar scale 및 threshold/RGE matching이 없어 채점에서 제외했다.')
md.append('- 따라서 현재 얻은 것은 “동결된 후보의 부분 외부 검증”이지, 모든 SM+ΛCDM 파라미터의 완전 제1원리 유도 성공이 아니다.')
(OUT/'ACADEMIC_EXTERNAL_HOLDOUT_AUDIT_ko.md').write_text('\n'.join(md))

# zip report bundle and a mini engine bundle
with zipfile.ZipFile('/mnt/data/academic_external_holdout_audit_v0_7.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in OUT.rglob('*'):
        z.write(p,p.relative_to(OUT.parent))

# Create a minimal reproducible scorer script in the output bundle
scorer = Path('/mnt/data/academic_external_holdout_audit_v0_7/score_academic_external_holdout.py')
scorer.write_text(Path(__file__).read_text())
# Rezip including scorer
with zipfile.ZipFile('/mnt/data/academic_external_holdout_audit_v0_7.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in OUT.rglob('*'):
        z.write(p,p.relative_to(OUT.parent))

print(json.dumps(summary,indent=2,ensure_ascii=False))
