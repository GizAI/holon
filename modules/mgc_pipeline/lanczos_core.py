import torch

@torch.no_grad()
def ritz_from_tridiag(alphas, betas):
    m = len(alphas)
    T = torch.zeros((m, m), dtype=torch.float64, device='cpu')
    for i in range(m):
        T[i, i] = float(alphas[i])
        if i + 1 < m:
            b = float(betas[i])
            T[i, i+1] = b
            T[i+1, i] = b
    evals, evecs = torch.linalg.eigh(T)
    return evals[0].item(), evecs[:, 0].to(torch.float32)

def _real_dtype_of(cdtype):
    return torch.float32 if cdtype == torch.complex64 else torch.float64

@torch.no_grad()
def davidson_polish(apply_H, diagE, sz_sum, psi, E, h, eps, steps=2, damping=1e-3, dtype=torch.complex64):
    diagH = diagE.to(_real_dtype_of(dtype)) - eps * sz_sum
    v = psi.clone()
    for _ in range(steps):
        Hv = apply_H(v, h, eps)
        r = Hv - E * v
        r_norm = torch.linalg.norm(r).item()
        if r_norm < 1e-6:
            break
        denom = (diagH - E).abs() + damping
        delta = (-r.real / denom).to(dtype) + 1j * (-r.imag / denom).to(dtype)
        v = v + delta
        v = v / v.norm()
    Hv = apply_H(v, h, eps)
    E_new = torch.vdot(v, Hv).real.item()
    rnorm = torch.linalg.norm(Hv - E_new * v).item()
    return v, E_new, rnorm

@torch.no_grad()
def thick_restart_lanczos_warm(apply_H, D, h, eps, max_matvec=120, m=16, reorth_window=6,
                               device="cuda", dtype=torch.complex64, seed=0, v0=None,
                               store_basis_fp16=True):
    gen = torch.Generator(device=device)
    if v0 is None:
        gen.manual_seed(seed)
        v = torch.randn(D, device=device, dtype=dtype)
        v = v / v.norm()
    else:
        v = v0.to(dtype)
        nrm = v.norm()
        if nrm.item() > 0:
            v = v / nrm

    best_E = float('inf'); best_vec = None; matvecs = 0

    def _restore(vstored):
        if vstored.dtype == torch.float16 and vstored.ndim == 2 and vstored.size(-1) == 2:
            return torch.view_as_complex(vstored.to(torch.float32))
        return vstored

    while matvecs < max_matvec:
        alphas = []; betas = []; V = []; v_prev = torch.zeros_like(v)
        for k in range(m):
            if store_basis_fp16:
                V.append(torch.view_as_real(v).contiguous().half())
            else:
                V.append(v.clone())
            w = apply_H(v, h, eps); matvecs += 1
            alpha = torch.vdot(v, w).real.to(torch.float32).item()
            w = w - alpha * v
            if k > 0:
                w = w - betas[-1].item() * v_prev
            start = max(0, k - reorth_window)
            for j in range(start, k):
                vv = _restore(V[j])
                coeff = torch.vdot(vv, w)
                w = w - coeff * vv
            beta = w.norm().to(torch.float32).item()
            alphas.append(alpha)
            if beta < 1e-10:
                break
            betas.append(torch.tensor(beta))
            v_prev = v
            v = (w / beta).contiguous()

        E_ritz, y = ritz_from_tridiag(alphas, betas)
        psi = torch.zeros(D, device=device, dtype=dtype)
        for i in range(len(y)):
            vv = _restore(V[i])
            psi += y[i].to(dtype) * vv
        nrm = psi.norm()
        if nrm.item() > 0: psi = psi / nrm
        phase = torch.angle(psi[0]); psi = psi * torch.exp(-1j * phase)
        if E_ritz < best_E:
            best_E = E_ritz; best_vec = psi.clone()
        v = psi
        Hv = apply_H(v, h, eps)
        rq = torch.vdot(v, Hv).real.item()
        if abs(rq - E_ritz) < 1e-6:
            break

    Hv = apply_H(best_vec, h, eps)
    rnorm = torch.linalg.norm(Hv - best_E * best_vec).item()
    return best_E, best_vec, matvecs, rnorm
