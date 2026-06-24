# First-Principles Physics Engine Final

A consolidated, non-fragmented research engine for testing claimed first-principles derivations of Standard-Model and cosmological constants.

## Final scientific verdict

**No complete first-principles derivation of all SM + ΛCDM parameters has been certified.**

The engine does provide:

- strict scoring of candidate derivations;
- ISDLC–TCPS gauge/vacuum validation;
- automatic candidate discovery with post-selection quarantine;
- blind prediction packet freeze and leakage checks;
- external holdout audit of the strongest frozen packet;
- a clean MECE documentation and artifact layout.

## Quick start

```bash
python -m pip install -e '.[test]'
python -m pytest -q
python -m fpphysics.final_cli status
python -m fpphysics.final_cli run-all --outdir run/final
```

## Read first

Start with `docs/INDEX_ko.md` and `docs/00_EXECUTIVE_SUMMARY_ko.md`.

## Canonical results

The single source of truth is `artifacts/results/consolidated_summary.json`.

## Proper use

This repository is a falsification and discovery-assistance framework. It must not be cited as proof that the fine-structure constant, cosmological constant, or all Standard-Model parameters have been derived from accepted first principles.

## Top candidate classes

The three preserved high-value candidate classes are summarized in `docs/10_TOP_CANDIDATE_CLASSES_ko.md`:

1. Cabibbo-clock flavor core;
2. one-loop gauge-clock RGE candidates;
3. cosmological-constant exponential/instanton candidates.

## Most surprising candidates

A narrative explanation of the most surprising preserved candidate theories is available in `docs/11_SURPRISING_CANDIDATES_EXPLAINED_ko.md`. It separates structured signals from certified success claims.
