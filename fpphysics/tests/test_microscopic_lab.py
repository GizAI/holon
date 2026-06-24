from fractions import Fraction

from fpphysics.microscopic_lab import (
    ALPHA_U_INV,
    DFC_INDEX,
    LCI_INDEX,
    MicroscopicLabConfig,
    audit_dfc_chain_complex,
    audit_finite_holonomy_hamiltonian,
    audit_lci_supertrace,
    run_lab,
)


def test_finite_holonomy_stiffness_is_exact_for_constructed_operator():
    result = audit_finite_holonomy_hamiltonian()
    assert result.passed
    assert result.observed["num"] == ALPHA_U_INV.numerator
    assert result.observed["den"] == ALPHA_U_INV.denominator
    assert result.status == "conditional_theorem"


def test_lci_and_dfc_exact_indices_are_reproduced():
    lci = audit_lci_supertrace()
    dfc = audit_dfc_chain_complex()
    assert lci.passed
    assert dfc.passed
    assert [Fraction(x["num"], x["den"]) for x in lci.observed] == list(LCI_INDEX)
    assert [Fraction(x["num"], x["den"]) for x in dfc.observed] == list(DFC_INDEX)


def test_microscopic_lab_tiny_cpu_run():
    run = run_lab(MicroscopicLabConfig(null_candidates=128, chunk_size=64, seed=1, device="cpu", progress_every=0))
    assert run["lab_name"] == "Microscopic ISDLC Laboratory"
    assert run["classification"]["grade"] == "B_plus"
    assert run["null_scan"]["candidate_count"] == 128
    assert run["frozen_flavor_extension"]["packet_sha256"].startswith("63d9ed215a92")
    assert run["dependency_graph"]["findings"]
    assert run["finite_hamiltonian_stiffness_table"]["rows"][-1]["abs_error"] < 1e-4
    assert run["dfc_cohomology_table"]["cohomology_dimensions"] == {"H0": 1, "H1": 0, "H2": 0}
    assert run["nonrenormalization_audit"]["ordinary_scalar_control"]["verdict"].startswith("fail_")
