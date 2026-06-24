"""Standard-Model bookkeeping relevant to 'deriving constants'.

This module makes explicit which numbers are fixed by symmetry/field content
and which are free Wilson coefficients or boundary conditions in the minimal
renormalizable Standard Model plus GR.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Status(str, Enum):
    FIXED_BY_DEFINITION = "fixed_by_definition"
    CONDITIONAL_DERIVATION = "conditional_derivation"
    FIT_BOUNDARY_CONDITION = "fit_or_boundary_condition"
    NOT_DERIVED_IN_MODEL = "not_derived_in_model"


@dataclass(frozen=True)
class ParameterStatus:
    symbol: str
    description: str
    status: Status
    reason: str


def standard_model_parameter_statuses() -> list[ParameterStatus]:
    """Classify constants in the accepted SM+GR EFT viewpoint."""

    return [
        ParameterStatus(
            "alpha(0)",
            "low-energy fine-structure constant",
            Status.FIT_BOUNDARY_CONDITION,
            "Gauge symmetry permits a U(1)_Y kinetic coefficient; RG running plus thresholds relate alpha(0) to electroweak-scale boundary data but do not fix its numerical value.",
        ),
        ParameterStatus(
            "g1, g2, g3 at M_Z",
            "Standard-Model gauge couplings",
            Status.FIT_BOUNDARY_CONDITION,
            "The group SU(3)xSU(2)xU(1) and matter representations fix beta-function coefficients; the integration constants are measured inputs unless a UV theory supplies boundary conditions.",
        ),
        ParameterStatus(
            "Yukawa matrices",
            "fermion masses and mixings",
            Status.FIT_BOUNDARY_CONDITION,
            "Renormalizability allows independent Yukawa operators consistent with the gauge symmetries.",
        ),
        ParameterStatus(
            "lambda_H, mu_H^2",
            "Higgs potential parameters",
            Status.FIT_BOUNDARY_CONDITION,
            "The Higgs mass and vacuum expectation value are not fixed by the SM gauge principle.",
        ),
        ParameterStatus(
            "Lambda",
            "cosmological constant",
            Status.FIT_BOUNDARY_CONDITION,
            "In GR plus local QFT the vacuum-energy counterterm is an allowed relevant operator; its renormalized value is fixed observationally unless a UV principle cancels/selects it.",
        ),
        ParameterStatus(
            "b_i",
            "one-loop gauge beta-function coefficients",
            Status.CONDITIONAL_DERIVATION,
            "Given gauge group and particle content, b_i are calculable from representation theory.",
        ),
        ParameterStatus(
            "c, h, e in SI",
            "selected dimensional conversion constants",
            Status.FIXED_BY_DEFINITION,
            "After the SI redefinition these are unit definitions, not dynamical predictions of a theory.",
        ),
    ]


def minimal_sm_free_parameter_count(include_neutrino_masses: bool = False, include_gravity: bool = True) -> dict[str, int]:
    """Return a transparent count of independent empirical parameters.

    Counts depend on conventions.  The common minimal SM count is 19 without
    neutrino masses.  Adding neutrino masses/mixings and GR/cosmology increases
    the number.  This function is deliberately explicit rather than pretending
    there is a unique universal count.
    """

    counts = {
        "gauge_couplings": 3,
        "higgs_potential": 2,
        "quark_masses": 6,
        "charged_lepton_masses": 3,
        "ckm_mixing_angles": 3,
        "ckm_cp_phase": 1,
        "qcd_theta": 1,
    }
    if include_neutrino_masses:
        counts.update(
            {
                "neutrino_masses_or_splittings": 3,
                "pmns_mixing_angles": 3,
                "pmns_cp_phases_dirac_plus_majorana": 3,
            }
        )
    if include_gravity:
        counts.update(
            {
                "newton_constant_or_planck_scale": 1,
                "cosmological_constant": 1,
            }
        )
    counts["total"] = sum(counts.values())
    return counts
