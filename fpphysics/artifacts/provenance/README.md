# Provenance Artifacts

This folder keeps selected evidence from the full `/mnt/data` export that is
not part of the executable final engine path.

## Included

- `academic_external_holdout_v07/`
  - pre-reveal freeze manifest for the strict academic external packet;
  - full Korean audit report;
  - original standalone scoring script used to produce the audit bundle.
- `external_audit_v06/`
  - v0.6 external audit report;
  - all-frozen-packet sweep showing that no pre-existing frozen packet passed
    the external tranche;
  - revealed external tranche values and original standalone scorer.
- `external_blind_validation_E1/`
  - earlier E1 freeze-before-reveal validation bundle with frozen packet,
    revealed observations, scores, and standalone validator.

## Excluded

The bulk `mnt_full_export_20260624.zip` contains many intermediate work
directories, nested release zips, stdout captures, cache files, and duplicate
run outputs. Those are intentionally not copied into the final repository.
