import math
from typing import Tuple

Lattice = Tuple[int, int, int]

def C_geo(q_min: int, Lx: int) -> float:
    return (q_min**2) / ((2 * math.pi)**2 * (Lx**2))

def K_geom(q_min: int, Lx: int) -> float:
    C = C_geo(q_min, Lx)
    return 4 * math.pi / C

def D_tau(Lx: int) -> float:
    # K = [2 Lx / (2pi)^2] * tau_wall
    return 2 * Lx / ((2 * math.pi)**2)

def D_kappa(L: Lattice) -> float:
    # geometry-only proportionality in the Gaussian sector
    # fill with 1.0 by default and let the user overwrite if a closed form is known
    return 1.0

def D_chib(L: Lattice) -> float:
    # geometry-only proportionality in the Gaussian sector
    return 1.0
