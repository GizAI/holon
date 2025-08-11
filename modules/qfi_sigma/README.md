# Fast approximate sigma via QFI overlap (GPU)

What this does
- Uses a 2D transverse field Ising model as a surrogate to quickly estimate the QFI-based stiffness along the h direction.
- Approximates sigma by normalizing the pure-state QFI per bond. This is a proxy for the "정보 강성" in your framework and is meant to give a quick signal within minutes on a single RTX 4090.

Why this design
- Exact QCN Hamiltonian would take far longer to implement and run. This surrogate still captures the core pipeline: ground state by Lanczos then Bures or QFI metric via ground-state overlaps.

How to run
1) Ensure CUDA drivers are installed and a Python 3.10+ environment is ready.
2) Install PyTorch with CUDA support. Example for CUDA 12.1:
   pip install --index-url https://download.pytorch.org/whl/cu121 torch torchvision torchaudio
3) Optionally install from requirements.txt:
   pip install -r requirements.txt

Quick start
   python3 qfi_sigma.py --Lx 4 --Ly 4 --h0 3.0 --dh 0.01 --iters 60 --dtype fp32 --device cuda --normalize per_bond

Typical runtime on RTX 4090
- A few seconds to under a minute for 4x4 lattice with 60 Lanczos iterations.

Tuning for 10-minute budget
- Increase iters to 120 for better ground-state convergence.
- Try 5x4 or 5x5 lattice, but keep an eye on D=2^(Lx*Ly) which grows fast.
- Reduce dh to 0.005 for more accurate QFI but expect a smaller overlap and more sensitivity to numerical error.

Notes
- The model uses open boundaries by default. Add --periodic to enable periodic boundaries.
- Use --dtype fp64 for more stable overlaps if you increase lattice size or reduce dh.

Outputs
- Prints ground energies, overlap, QFI g and sigma_hat with normalization details.
- sigma_hat near 0.2 is possible depending on parameters and normalization. Treat this as a quick plausibility check rather than a final number.
