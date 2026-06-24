"""First-principles physics engine.

This package does not assert that the measured constants are already derived
from accepted first principles.  It provides a rigorous, executable framework
for testing candidate derivations and for generating post-selected hypotheses
that must remain quarantined until independently derived.
"""

from .constants import BenchmarkData, Quantity, load_benchmarks
from .engine import DerivationEngine, EvaluationResult
from .autodiscovery import DiscoveryConfig, TheoryDiscoveryEngine
from .theory_lab import LabConfig, TheoryLab

from .blind_protocol import BlindPredictionProtocol, BlindProtocolConfig, PredictionPacket, default_observation_registry
from .frozen_blind_candidate import packet_isdlc_tcps_rational_clock_texture, score_frozen_candidate

# Backward-compatible alias for earlier drafts of the discovery API.
DiscoverySettings = DiscoveryConfig

__all__ = [
    "BenchmarkData",
    "Quantity",
    "load_benchmarks",
    "DerivationEngine",
    "EvaluationResult",
    "DiscoveryConfig",
    "DiscoverySettings",
    "TheoryDiscoveryEngine",
    "LabConfig",
    "TheoryLab",
    "BlindPredictionProtocol",
    "BlindProtocolConfig",
    "PredictionPacket",
    "default_observation_registry",
    "packet_isdlc_tcps_rational_clock_texture",
    "score_frozen_candidate",
]
