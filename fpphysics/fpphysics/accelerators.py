"""Optional CPU/GPU/JIT backend discovery.

The discovery engine is designed to run with NumPy only, but this module records
which acceleration backends are available and exposes conservative helpers.  It
never requires GPU libraries; it uses them only when they are installed and the
hardware/runtime reports availability.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from importlib.util import find_spec
from typing import Any


@dataclass(frozen=True)
class BackendInfo:
    """Detected numerical backend capability."""

    numpy_available: bool
    scipy_available: bool
    numba_available: bool
    torch_available: bool
    torch_cuda_available: bool | None
    torch_mps_available: bool | None
    jax_available: bool
    jax_devices: tuple[str, ...]
    cupy_available: bool
    selected_device: str
    note: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def detect_backends(prefer: str = "auto") -> BackendInfo:
    """Inspect optional compute backends.

    Parameters
    ----------
    prefer:
        ``"auto"`` chooses CUDA if available, then Apple MPS, then JAX device,
        otherwise CPU.  Passing ``"cpu"`` forces CPU even if accelerators exist.
    """

    numpy_available = find_spec("numpy") is not None
    scipy_available = find_spec("scipy") is not None
    numba_available = find_spec("numba") is not None
    torch_available = find_spec("torch") is not None
    cupy_available = find_spec("cupy") is not None
    jax_available = find_spec("jax") is not None

    torch_cuda_available: bool | None = None
    torch_mps_available: bool | None = None
    if torch_available:
        try:
            import torch  # type: ignore

            torch_cuda_available = bool(torch.cuda.is_available())
            try:
                torch_mps_available = bool(getattr(torch.backends, "mps").is_available())
            except Exception:
                torch_mps_available = False
        except Exception:
            torch_cuda_available = False
            torch_mps_available = False

    jax_devices: tuple[str, ...] = tuple()
    if jax_available:
        try:
            import jax  # type: ignore

            jax_devices = tuple(str(d) for d in jax.devices())
        except Exception:
            jax_devices = tuple()

    prefer_norm = prefer.lower().strip()
    selected = "cpu"
    notes: list[str] = []
    if prefer_norm not in {"auto", "cpu", "cuda", "mps", "jax", "cupy"}:
        notes.append(f"unknown preference {prefer!r}; using auto policy")
        prefer_norm = "auto"

    if prefer_norm == "cpu":
        selected = "cpu"
        notes.append("CPU was forced by the caller.")
    elif prefer_norm == "cuda":
        selected = "cuda" if torch_cuda_available else "cpu"
        if not torch_cuda_available:
            notes.append("CUDA was requested but torch reported no CUDA device; using CPU.")
    elif prefer_norm == "mps":
        selected = "mps" if torch_mps_available else "cpu"
        if not torch_mps_available:
            notes.append("MPS was requested but unavailable; using CPU.")
    elif prefer_norm == "jax":
        selected = "jax" if jax_devices else "cpu"
        if not jax_devices:
            notes.append("JAX was requested but no JAX devices were listed; using CPU.")
    elif prefer_norm == "cupy":
        selected = "cupy" if cupy_available else "cpu"
        if not cupy_available:
            notes.append("CuPy was requested but not installed; using CPU.")
    else:
        if torch_cuda_available:
            selected = "cuda"
        elif torch_mps_available:
            selected = "mps"
        elif cupy_available:
            selected = "cupy"
        elif jax_devices and any("gpu" in d.lower() or "tpu" in d.lower() for d in jax_devices):
            selected = "jax"
        else:
            selected = "cpu"
            notes.append("No GPU accelerator reported available; vectorized NumPy/SciPy CPU path selected.")

    return BackendInfo(
        numpy_available=numpy_available,
        scipy_available=scipy_available,
        numba_available=numba_available,
        torch_available=torch_available,
        torch_cuda_available=torch_cuda_available,
        torch_mps_available=torch_mps_available,
        jax_available=jax_available,
        jax_devices=jax_devices,
        cupy_available=cupy_available,
        selected_device=selected,
        note=" ".join(notes) if notes else "accelerator selected successfully",
    )
