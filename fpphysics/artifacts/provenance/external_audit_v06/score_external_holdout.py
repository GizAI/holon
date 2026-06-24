#!/usr/bin/env python3
"""Score a pre-frozen prediction packet against a revealed external holdout tranche.

This script is intentionally simple: it does not search, optimize, refit, mutate,
or select among candidates. It scores exactly the predictions present in the packet.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, pathlib, datetime

def side_sigma(pred, central, sigma_minus, sigma_plus):
    return sigma_plus if pred >= central else sigma_minus

def score(packet, tranche):
    rows=[]; numeric_count=0; chi2=0.0; pass_count=fail_count=missing_count=incomplete_count=0
    for key, obs in tranche["observations"].items():
        pred=packet.get("predictions",{}).get(key)
        row={"quantity":key,"domain":obs.get("domain",""),"source":obs.get("source",""),"prediction":pred,
             "central":obs.get("central", obs.get("lower_bound")),"sigma_minus":obs.get("sigma_minus"),
             "sigma_plus":obs.get("sigma_plus"),"z":None,"abs_z":None,"status":"","note":obs.get("note","")}
        if "central" in obs and "sigma_minus" in obs:
            if pred is None or isinstance(pred, str):
                row["status"]="missing_prediction"; missing_count+=1
            else:
                sig=side_sigma(float(pred), float(obs["central"]), float(obs["sigma_minus"]), float(obs["sigma_plus"]))
                z=(float(pred)-float(obs["central"]))/sig
                row["z"]=z; row["abs_z"]=abs(z); numeric_count+=1; chi2+=z*z
                if abs(z)<=3: row["status"]="pass_3sigma"; pass_count+=1
                else: row["status"]="fail_gt_3sigma"; fail_count+=1
        elif "categorical" in obs:
            if pred is None:
                row["status"]="missing_prediction"; missing_count+=1
            elif str(pred).lower()==str(obs["categorical"]).lower():
                row["status"]="categorical_pass"; pass_count+=1
            else:
                row["status"]="categorical_fail"; fail_count+=1
        elif "lower_bound" in obs:
            if pred is None or isinstance(pred,str):
                row["status"]="missing_prediction"; missing_count+=1
            elif float(pred)>=float(obs["lower_bound"]):
                row["status"]="one_sided_bound_pass"; pass_count+=1
            else:
                row["status"]="one_sided_bound_fail"; fail_count+=1
        else:
            row["status"]="incomplete_target_definition_or_missing_prediction"
            if pred is None: missing_count+=1
            else: incomplete_count+=1
        rows.append(row)
    return {
      "summary":{
        "numeric_count":numeric_count,
        "chi2":chi2,
        "reduced_chi2_independent_diag_approx":chi2/numeric_count if numeric_count else None,
        "pass_count_including_bounds_and_categorical":pass_count,
        "fail_count":fail_count,
        "missing_count":missing_count,
        "incomplete_count":incomplete_count,
        "external_tranche_pass":fail_count==0 and missing_count==0 and incomplete_count==0 and numeric_count>=10 and (chi2/numeric_count if numeric_count else 1e9)<4,
      },
      "rows":rows
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--packet", required=True)
    ap.add_argument("--tranche", required=True)
    ap.add_argument("--json-out", required=True)
    ap.add_argument("--csv-out", required=True)
    args=ap.parse_args()
    packet_path=pathlib.Path(args.packet); tranche_path=pathlib.Path(args.tranche)
    packet=json.loads(packet_path.read_text())
    tranche=json.loads(tranche_path.read_text())
    out=score(packet,tranche)
    out["audit_generated_utc"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
    out["packet_file_sha256"]=hashlib.sha256(packet_path.read_bytes()).hexdigest()
    out["embedded_canonical_sha256"]=packet.get("sha256")
    pathlib.Path(args.json_out).write_text(json.dumps(out, indent=2, ensure_ascii=False))
    with open(args.csv_out,"w",newline="") as f:
        fields=["quantity","domain","source","prediction","central","sigma_minus","sigma_plus","z","abs_z","status","note"]
        w=csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in out["rows"]: w.writerow({k:r.get(k) for k in fields})
if __name__ == "__main__": main()
