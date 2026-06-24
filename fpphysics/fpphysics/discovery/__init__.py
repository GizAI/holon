"""Public wrapper for the automatic theory-discovery layer.

The implementation lives in :mod:`fpphysics.autodiscovery`.  This wrapper keeps
``import fpphysics.discovery`` stable without shipping multiple competing
implementations.
"""

from ..autodiscovery import (  # noqa: F401
    AutoCandidateModel,
    DiscoveryCandidate,
    DiscoveryConfig,
    DiscoveryScore,
    GaugeClockSearcher,
    GaugeSearchConfig,
    SymbolicSearchConfig,
    TheoryDiscoveryEngine,
    VacuumInstantonSearcher,
    VacuumSearchConfig,
    detect_hardware,
    flatten_candidates_for_csv,
    generate_markdown_report,
    write_csv,
    write_json,
    write_report,
)
