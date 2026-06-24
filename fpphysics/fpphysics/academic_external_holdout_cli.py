from __future__ import annotations
import argparse, csv, json
from pathlib import Path
from .academic_external_holdout import audit_packet

def main(argv=None):
    ap=argparse.ArgumentParser(description='Score one frozen packet on academic external holdout tranche.')
    ap.add_argument('--packet', required=True)
    ap.add_argument('--outdir', default='academic_external_holdout_run')
    ns=ap.parse_args(argv)
    out=Path(ns.outdir); out.mkdir(parents=True, exist_ok=True)
    result=audit_packet(ns.packet)
    (out/'academic_external_holdout_results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
    rows=result['external_tranche_rows']+result['diagnostic_rows_not_part_of_strict_external_tranche']
    fields=[]
    for r in rows:
        for k in r:
            if k not in fields: fields.append(k)
    with open(out/'academic_external_holdout_scores.csv','w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    print(json.dumps(result['summary'], indent=2, ensure_ascii=False))

if __name__=='__main__': main()
