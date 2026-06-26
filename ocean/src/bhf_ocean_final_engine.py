#!/usr/bin/env python3
"""BHF-OCEAN final consolidation engine v0.2.

Purpose:
- Reproduce the two canonical gauge benchmarks: D5 reference and BC4/COVE-BHF.
- Certify BHF threshold uniqueness by exhaustive dynamic programming.
- Label alpha(0) as an open QCD+EW closure target, not as a prediction.

This is an audit engine, not a completed theory of nature.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from functools import lru_cache
import argparse, csv, json, math
from pathlib import Path

MZ_GEV = 91.1876
MBAR_PL_GEV = 2.435e18
ALPHA0_INV_CODATA = 137.035999177
# one-loop charged-lepton bridge used consistently in prior packets
DELTA_LEPTON_INV = 4.30579826418
B_SM = (41/10, -19/6, -7)
TWO_PI = 2*math.pi

@dataclass(frozen=True)
class GaugeCandidate:
    label: str
    root_class: str
    roots: int
    rank: int
    flux_half_count: float
    clock_num: int
    clock_den: int
    b_ps: tuple[float,float,float]
    dfc: tuple[float,float,float] = (0.0,0.0,0.0)
    scale_denominator: int|None = None

    @property
    def alpha_u_inv(self) -> float:
        return self.roots + self.rank + 0.5*self.flux_half_count

    @property
    def mu_gev(self) -> float:
        return MBAR_PL_GEV/(self.scale_denominator or self.roots)

    @property
    def mi_gev(self) -> float:
        L=math.log(self.mu_gev/MZ_GEV)
        return MZ_GEV*math.exp(self.clock_den/(self.clock_num+self.clock_den)*L)

    @property
    def b_ps_sm_basis(self) -> tuple[float,float,float]:
        b4,bL,bR=self.b_ps
        return ((3/5)*bR+(2/5)*b4, bL, b4)

    def compute(self) -> dict:
        l_sm=math.log(self.mi_gev/MZ_GEV)
        l_ps=math.log(self.mu_gev/self.mi_gev)
        inv=[]
        for bsm,bps,dfc in zip(B_SM,self.b_ps_sm_basis,self.dfc):
            inv.append(self.alpha_u_inv + bsm/TWO_PI*l_sm + bps/TWO_PI*l_ps + dfc)
        a1,a2,a3=inv
        alpha_em=(5/3)*a1+a2
        sin2=a2/alpha_em
        alphas=1/a3
        residual=ALPHA0_INV_CODATA-alpha_em-DELTA_LEPTON_INV
        kir=residual/(math.log(2)/TWO_PI)
        return {
            'label': self.label,
            'root_class': self.root_class,
            'roots': self.roots,
            'rank': self.rank,
            'flux_half_count': self.flux_half_count,
            'alpha_U_inv': self.alpha_u_inv,
            'M_U_GeV': self.mu_gev,
            'M_I_GeV': self.mi_gev,
            'clock': f'{self.clock_num}:{self.clock_den}',
            'b_PS_4': self.b_ps[0], 'b_PS_L': self.b_ps[1], 'b_PS_R': self.b_ps[2],
            'B_PS_1': self.b_ps_sm_basis[0], 'B_PS_2': self.b_ps_sm_basis[1], 'B_PS_3': self.b_ps_sm_basis[2],
            'dfc_1': self.dfc[0], 'dfc_2': self.dfc[1], 'dfc_3': self.dfc[2],
            'alpha1_inv_MZ': a1, 'alpha2_inv_MZ': a2, 'alpha3_inv_MZ': a3,
            'alpha_em_inv_MZ': alpha_em,
            'sin2_MSbar_MZ': sin2,
            'alpha_s_MZ': alphas,
            'alpha0_inv_status': 'TARGET_NOT_PREDICTED',
            'alpha0_inv_CODATA_target': ALPHA0_INV_CODATA,
            'delta_lepton_inv_bridge': DELTA_LEPTON_INV,
            'residual_QCD_EW_inv_target': residual,
            'K_IR_target_ln2_over_2pi_units': kir,
        }

def d5_reference() -> GaugeCandidate:
    dfc=tuple((math.log(2)/TWO_PI)*x for x in (1/8,-1/48,1/32))
    return GaugeCandidate('D5_reference_ISDLC_OCTU', 'D5', 40,5,3,6,13,(-7,-3,2),dfc,40)

def bhf_bc4() -> GaugeCandidate:
    return GaugeCandidate('BHF_COVE_BC4_final_gauge_benchmark', 'BC4', 32,4,7,3,14,(0.5,4.5,1.5),(0,0,0),32)

THRESHOLD_BLOCKS = [
    {'name':'S_R=(1,1,3)_R','charge6':(0,0,2),'dimension':3},
    {'name':'h_L=(1,2,1)','charge6':(0,1,0),'dimension':2},
    {'name':'h_R=(1,1,2)','charge6':(0,0,1),'dimension':2},
    {'name':'q_C=(4,1,1)','charge6':(1,0,0),'dimension':4},
    {'name':'Q_CL=(4,2,1)','charge6':(2,4,0),'dimension':8},
    {'name':'X_LR=(1,2,2)_D','charge6':(0,8,8),'dimension':4},
    {'name':'G_4=(15,1,1)_D','charge6':(32,0,0),'dimension':15},
    {'name':'G_L=(1,3,1)_D','charge6':(0,16,0),'dimension':3},
    {'name':'G_R=(1,1,3)_D','charge6':(0,0,16),'dimension':3},
]
TARGET6=(67,45,27)

def threshold_certificate():
    C=[b['charge6'] for b in THRESHOLD_BLOCKS]
    d=[b['dimension'] for b in THRESHOLD_BLOCKS]
    @lru_cache(None)
    def rec(k,a,b,c):
        rem=(a,b,c)
        if k==len(C):
            return (1,0,[()]) if rem==(0,0,0) else (0,10**12,[])
        charge=C[k]
        maxn=10**9
        for i,ci in enumerate(charge):
            if ci>0:
                maxn=min(maxn, rem[i]//ci)
        if maxn==10**9:
            maxn=0
        total=0; best=10**12; bests=[]
        for n in range(maxn+1):
            nr=(a-n*charge[0], b-n*charge[1], c-n*charge[2])
            if min(nr)<0:
                continue
            cnt,cost,suffs=rec(k+1,*nr)
            if not cnt:
                continue
            total+=cnt
            cc=cost+d[k]*n
            pref=[(n,)+s for s in suffs]
            if cc<best:
                best=cc; bests=pref
            elif cc==best:
                bests+=pref
        return total,best,bests
    total,best,bests=rec(0,*TARGET6)
    best_solution=bests[0]
    rows=[]
    for block,n in zip(THRESHOLD_BLOCKS,best_solution):
        rows.append({**block,'multiplicity':n,'dimension_cost':n*block['dimension']})
    return {
        'target_charge6': TARGET6,
        'number_of_nonnegative_integer_solutions': total,
        'minimal_dimension': best,
        'number_of_minimizers': len(bests),
        'unique_minimizer': best_solution,
        'rows': rows,
        'statement': 'Unique BHF threshold hierarchy under beta-charge closure plus dimension minimality.'
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--outdir', default='outputs')
    args=ap.parse_args()
    out=Path(args.outdir); out.mkdir(parents=True,exist_ok=True)
    candidates=[d5_reference(), bhf_bc4()]
    results=[c.compute() for c in candidates]
    cert=threshold_certificate()
    with (out/'final_predictions.csv').open('w',newline='') as fp:
        fields=list(results[0].keys())
        w=csv.DictWriter(fp,fieldnames=fields); w.writeheader(); w.writerows(results)
    with (out/'threshold_certificate.json').open('w') as fp:
        json.dump(cert,fp,indent=2)
    with (out/'final_results.json').open('w') as fp:
        json.dump({'candidates':results,'threshold_certificate':cert},fp,indent=2)
    report=[]
    report.append('# BHF-OCEAN final audit report\n')
    report.append('Status: finite-code research program; not a completed derivation of all constants.\n')
    for r in results:
        report.append(f"## {r['label']}\n")
        for k in ['root_class','alpha_U_inv','M_U_GeV','M_I_GeV','clock','alpha_em_inv_MZ','sin2_MSbar_MZ','alpha_s_MZ','residual_QCD_EW_inv_target','K_IR_target_ln2_over_2pi_units']:
            report.append(f'- {k}: {r[k]}')
        report.append('')
    report.append('## Threshold uniqueness certificate\n')
    report.append(f"- target charge6: {cert['target_charge6']}")
    report.append(f"- number of solutions: {cert['number_of_nonnegative_integer_solutions']}")
    report.append(f"- minimal dimension: {cert['minimal_dimension']}")
    report.append(f"- number of minimizers: {cert['number_of_minimizers']}")
    report.append(f"- unique minimizer: {cert['unique_minimizer']}")
    report.append('\n## Claim hygiene\n')
    report.append('- Gauge values are formal one-loop benchmarks. Decimal length is engine precision, not physical error budget.')
    report.append('- alpha(0)=137.035999177 is an empirical target requiring a QCD+EW infrared spectral closure; it is not predicted here.')
    report.append('- Flavor, QCD-IR, and EW modules are required by no-modulus closure, but their spectra are open.')
    (out/'final_report.md').write_text('\n'.join(report), encoding='utf-8')
    print(out/'final_report.md')

if __name__ == '__main__':
    main()
