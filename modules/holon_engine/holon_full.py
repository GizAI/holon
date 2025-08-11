#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Full first principles pipeline that goes from a micro Holon-like lattice model to:
  1) K (helicity modulus) with strict estimators and blocking errors
  2) alpha_star_inv at the high scale via the Sigma identity: alpha_star_inv = 4*pi*K + c_th
  3) A first principles scan of Pati Salam to SM two loop RG without fitting to external targets
     to produce a prediction band for alpha_em_inv(MZ).
No external experimental targets are used anywhere in the chain.

Performance notes
  - torch.compile with aot_eager backend for stable speedups without C++ codegen pitfalls
  - vectorized Metropolis and over relaxation
  - blocking error bars to account for autocorrelation
  - optional CUDA if available

Important limitation for absolute alpha_em at MZ
  - Without a physical unit map from the micro model to GeV, there is no unique absolute M_PS and M_GUT.
  - This code therefore performs a first principles scan across an internally reasonable window for M_PS and M_GUT
    that does not use experimental targets. The output is a band for alpha_em_inv(MZ) implied by the micro derived alpha_star.
  - If you pass explicit --MPS and --MGUT the code will give a single prediction using those inputs.

No em dash characters are used in this file by design.
"""

import os
import math
import time
import json
import argparse
import numpy as np
import torch
import yaml
from sympy import Matrix

import torch._dynamo as dynamo
dynamo.config.capture_scalar_outputs = True
os.environ.setdefault("TORCHDYNAMO_CAPTURE_SCALAR_OUTPUTS", "1")

def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

# =========================
# Smith Normal Form for q_min
# =========================

def compute_qmin_from_yaml(path_yaml):
    if not path_yaml or not os.path.isfile(path_yaml):
        log("No SNF yaml. Using q_min = 1")
        return 1.0, {"mode": "default", "q_min": 1.0}
    with open(path_yaml, "r") as f:
        data = yaml.safe_load(f)
    if "A" in data and "B" in data and "e" in data:
        A = Matrix(data["A"])
        B = Matrix(data["B"])
        e = Matrix(data["e"])
        U, S, V = A.smith_normal_form()
        ds = []
        r = min(S.shape[0], S.shape[1])
        for i in range(r):
            if S[i, i] != 0:
                ds.append(int(S[i, i]))
        if len(ds) == 0:
            ds = [1]
        denom = 0
        for i in range(len(ds)):
            v_i = V[:, i]
            m_i = int((e.T * B * v_i)[0, 0])
            val = math.gcd(ds[i], abs(m_i))
            denom = val if denom == 0 else math.gcd(denom, val)
        q_min = 1.0 if denom == 0 else 1.0 / float(denom)
        info = {"mode": "SNF", "torsion_diag": ds, "denom": int(denom), "q_min": q_min}
        log(f"SNF computed q_min = {q_min}")
        return q_min, info
    if "global_quotient" in data:
        gq = str(data["global_quotient"]).lower()
        if gq in ["z6", "z_6", "z-6"]:
            q_min = 1.0 / 3.0
        elif gq in ["z2", "z_2", "z-2"]:
            q_min = 1.0
        else:
            q_min = 1.0
        info = {"mode": "quotient", "global_quotient": gq, "q_min": q_min}
        log(f"Quotient based q_min = {q_min}")
        return q_min, info
    log("Unrecognized yaml. Using q_min = 1")
    return 1.0, {"mode": "fallback", "q_min": 1.0}

# =========================
# Blocking estimator
# =========================

def blocking_stats(x):
    x = np.asarray(x, dtype=np.float64)
    n = x.size
    if n < 8:
        m = float(x.mean())
        s = float(x.std(ddof=1) / math.sqrt(max(1, n - 1)))
        return m, s, 1, n
    levels = 0
    variances = []
    means = []
    ns = []
    y = x.copy()
    while y.size >= 8 and levels < 14:
        m = y.mean()
        v = y.var(ddof=1)
        means.append(m)
        variances.append(v / y.size)
        ns.append(y.size)
        # If y has odd length, drop the last element so pairs align
        y = 0.5 * (y[:-1:2] + y[1::2])
        levels += 1
    pick = max(0, len(variances) - 3)
    mean_final = float(means[pick])
    stderr_final = float(math.sqrt(variances[pick]))
    block_len = 2 ** pick
    num_blocks = ns[pick]
    return mean_final, stderr_final, block_len, num_blocks

# =========================
# Micro model
# =========================

class HolonStabRotor:
    def __init__(self, Lx, Ly, beta, J, Kp, device, seed=1234, use_compile=True, use_overrelax=True):
        self.Lx, self.Ly = int(Lx), int(Ly)
        self.beta = torch.tensor(beta, dtype=torch.float64, device=device)
        self.J = torch.tensor(J, dtype=torch.float64, device=device)
        self.Kp = torch.tensor(Kp, dtype=torch.float64, device=device)
        self.device = device
        self.use_overrelax = use_overrelax
        g = torch.Generator(device=device)
        g.manual_seed(seed)
        self.rng = g
        self.theta = (2 * math.pi) * torch.rand((Lx, Ly), dtype=torch.float64, device=device, generator=g) - math.pi
        self.sx = torch.ones((Lx, Ly), dtype=torch.int32, device=device)
        self.sy = torch.ones((Lx, Ly), dtype=torch.int32, device=device)
        self.phi = 0.0
        self.eps_aniso = 0.0
        self._ix = torch.arange(Lx, device=device)
        self._iy = torch.arange(Ly, device=device)
        self._ixp = (self._ix + 1) % Lx
        self._ixm = (self._ix - 1) % Lx
        self._iyp = (self._iy + 1) % Ly
        self._iym = (self._iy - 1) % Ly
        self.delta_max = 0.35
        self._compiled = False
        if use_compile and hasattr(torch, "compile"):
            self._try_compile()
        self._update_zshift_cache()

    def set_J(self, J): self.J = torch.tensor(J, dtype=torch.float64, device=self.device)
    def set_Kp(self, Kp): self.Kp = torch.tensor(Kp, dtype=torch.float64, device=self.device)
    def set_beta(self, beta): self.beta = torch.tensor(beta, dtype=torch.float64, device=self.device)
    def set_twist(self, phi): self.phi = float(phi)
    def set_anisotropy(self, eps): self.eps_aniso = float(eps)

    def reset_angles(self):
        self.theta = (2 * math.pi) * torch.rand(self.theta.shape, dtype=self.theta.dtype, device=self.theta.device, generator=self.rng) - math.pi

    def reset_links(self, p_minus=0.0):
        if p_minus <= 0:
            self.sx.fill_(1)
            self.sy.fill_(1)
        else:
            rx = torch.rand(self.theta.shape, dtype=self.theta.dtype, device=self.theta.device, generator=self.rng)
            ry = torch.rand(self.theta.shape, dtype=self.theta.dtype, device=self.theta.device, generator=self.rng)
            self.sx = torch.where(rx < p_minus, torch.tensor(-1, dtype=torch.int32, device=self.device), torch.tensor(1, dtype=torch.int32, device=self.device))
            self.sy = torch.where(ry < p_minus, torch.tensor(-1, dtype=torch.int32, device=self.device), torch.tensor(1, dtype=torch.int32, device=self.device))
        self._update_zshift_cache()

    def _Ax(self): return self.phi / self.Lx
    def _Ay(self): return 0.0
    def _Jx(self): return self.J * (1.0 + self.eps_aniso)
    def _Jy(self): return self.J * (1.0 - self.eps_aniso)

    def _update_zshift_cache(self):
        self._zsx = math.pi * (1.0 - self.sx.to(torch.float64)) * 0.5
        self._zsy = math.pi * (1.0 - self.sy.to(torch.float64)) * 0.5

    def _dx(self, theta):
        th_xp = theta[self._ixp][:, :]
        A = self._Ax()
        d = th_xp - theta - A - self._zsx
        return ((d + math.pi) % (2 * math.pi)) - math.pi

    def _dy(self, theta):
        th_yp = theta[:, self._iyp]
        d = th_yp - theta - self._zsy
        return ((d + math.pi) % (2 * math.pi)) - math.pi

    def energy_density_tensor(self):
        dx = self._dx(self.theta)
        dy = self._dy(self.theta)
        E_rot = - self._Jx() * torch.cos(dx) - self._Jy() * torch.cos(dy)
        sx = self.sx
        sy = self.sy
        plaq = sx * sy[self._ixp][:, :] * sx[:, self._iyp] * sy
        E_plaq = - self.Kp * plaq.to(torch.float64)
        return (E_rot.sum() + E_plaq.sum()) / (self.Lx * self.Ly)

    def measure_energy(self):
        return float(self.energy_density_tensor().detach().cpu().numpy())

    def K_current_tensor(self):
        dx = self._dx(self.theta)
        cosx = torch.cos(dx)
        sinx = torch.sin(dx)
        N = self.Lx * self.Ly
        sum_sinx = sinx.sum()
        K = self._Jx() * cosx.mean() - (self.beta * (self._Jx() ** 2) / N) * (sum_sinx ** 2) / N
        return K

    def measure_K_current(self):
        return float(self.K_current_tensor().detach().cpu().numpy())

    def O_kappa_tensor(self):
        dx = self._dx(self.theta)
        dy = self._dy(self.theta)
        return - self.J * torch.sum(torch.cos(dx)) + self.J * torch.sum(torch.cos(dy))

    def O_boundary_tensor(self):
        A = self._Ax()
        th0 = self.theta[0, :]
        th1 = self.theta[1 % self.Lx, :]
        d = ((th1 - th0 - A - self._zsx[0, :] + math.pi) % (2 * math.pi)) - math.pi
        return - self.J * torch.sum(torch.cos(d))

    def measure_O_kappa(self):
        return float(self.O_kappa_tensor().detach().cpu().numpy())

    def measure_O_boundary(self):
        return float(self.O_boundary_tensor().detach().cpu().numpy())

    def _local_theta_dE_tensor(self, theta, prop, mask):
        A = self._Ax()
        th = theta
        thn = torch.where(mask, prop, th)
        th_xp = th[self._ixp][:, :]
        th_xm = th[self._ixm][:, :]
        th_yp = th[:, self._iyp]
        th_ym = th[:, self._iym]
        thn_xp = thn[self._ixp][:, :]
        thn_xm = thn[self._ixm][:, :]
        thn_yp = thn[:, self._iyp]
        thn_ym = thn[:, self._iym]
        zsx = self._zsx
        zsx_xm = zsx[self._ixm][:, :]
        zsy = self._zsy
        zsy_ym = zsy[:, self._iym]
        dx_old_f = ((th_xp - th - A - zsx + math.pi) % (2 * math.pi)) - math.pi
        dx_old_b = ((th - th_xm - A - zsx_xm + math.pi) % (2 * math.pi)) - math.pi
        dy_old_f = ((th_yp - th - zsy + math.pi) % (2 * math.pi)) - math.pi
        dy_old_b = ((th - th_ym - zsy_ym + math.pi) % (2 * math.pi)) - math.pi
        dx_new_f = ((thn_xp - thn - A - zsx + math.pi) % (2 * math.pi)) - math.pi
        dx_new_b = ((thn - thn_xm - A - zsx_xm + math.pi) % (2 * math.pi)) - math.pi
        dy_new_f = ((thn_yp - thn - zsy + math.pi) % (2 * math.pi)) - math.pi
        dy_new_b = ((thn - thn_ym - zsy_ym + math.pi) % (2 * math.pi)) - math.pi
        dE_site = - self._Jx() * (torch.cos(dx_new_f) + torch.cos(dx_new_b) - torch.cos(dx_old_f) - torch.cos(dx_old_b)) \
                  - self._Jy() * (torch.cos(dy_new_f) + torch.cos(dy_new_b) - torch.cos(dy_old_f) - torch.cos(dy_old_b))
        return torch.where(mask, dE_site, torch.zeros_like(dE_site))

    def metropolis_theta_sweep(self):
        Lx, Ly = self.Lx, self.Ly
        xx = torch.arange(Lx, device=self.device).unsqueeze(1).expand(Lx, Ly)
        yy = torch.arange(Ly, device=self.device).unsqueeze(0).expand(Lx, Ly)
        even = ((xx + yy) % 2 == 0)
        odd = ~even
        acc_sum = 0.0
        total = 0.0
        for mask in [even, odd]:
            prop = self.theta + self.delta_max * (2.0 * torch.rand(self.theta.shape, dtype=self.theta.dtype, device=self.theta.device) - 1.0)
            dE = self._local_theta_dE_tensor(self.theta, prop, mask)
            acc = torch.exp(- self.beta * dE)
            rnd = torch.rand(self.theta.shape, dtype=self.theta.dtype, device=self.theta.device)
            take = (rnd < acc) & mask
            self.theta = torch.where(take, prop, self.theta)
            acc_sum += float(take.sum().detach().cpu().numpy())
            total += float(mask.sum().detach().cpu().numpy())
        return acc_sum / max(1.0, total)

    def _local_sigma_x_dE_tensor(self, mask_bool):
        A = self._Ax()
        dx = ((self.theta[self._ixp][:, :] - self.theta - A - self._zsx + math.pi) % (2 * math.pi)) - math.pi
        dE_rot = 2.0 * self._Jx() * torch.cos(dx)
        sx = self.sx
        sy = self.sy
        plaq_ij = sx * sy[self._ixp][:, :] * sx[:, self._iyp] * sy
        j_prev = self._iym
        sy_ip_jm = sy[self._ixp][:, :][:, j_prev]
        sx_i_jp = sx[:, self._iyp][:, j_prev]
        sy_i_jm = sy[:, j_prev]
        plaq_ijm = sx[:, j_prev] * sy_ip_jm * sx_i_jp * sy_i_jm
        dE_plaq = 2.0 * self.Kp * (plaq_ij.to(torch.float64) + plaq_ijm.to(torch.float64))
        dE = dE_rot + dE_plaq
        return torch.where(mask_bool, dE, torch.zeros_like(dE))

    def _local_sigma_y_dE_tensor(self, mask_bool):
        dy = ((self.theta[:, self._iyp] - self.theta - self._zsy + math.pi) % (2 * math.pi)) - math.pi
        dE_rot = 2.0 * self._Jy() * torch.cos(dy)
        sx = self.sx
        sy = self.sy
        plaq_ij = sx * sy[self._ixp][:, :] * sx[:, self._iyp] * sy
        i_prev = self._ixm
        sx_im_j = sx[i_prev][:, :]
        sy_im_j = sy[i_prev][:, :]
        sx_im_jp = sx[i_prev][:, self._iyp]
        plaq_imj = sx_im_j * sy * sx_im_jp * sy_im_j
        dE_plaq = 2.0 * self.Kp * (plaq_ij.to(torch.float64) + plaq_imj.to(torch.float64))
        dE = dE_rot + dE_plaq
        return torch.where(mask_bool, dE, torch.zeros_like(dE))

    def overrelax_theta_sweep(self):
        A = self._Ax()
        theta = self.theta
        th_xp = theta[self._ixp][:, :] - (A + self._zsx)
        th_xm = theta[self._ixm][:, :] + (A + self._zsx[self._ixm][:, :])
        th_yp = theta[:, self._iyp] - self._zsy
        th_ym = theta[:, self._iym] + self._zsy[:, self._iym]
        Jx = self._Jx()
        Jy = self._Jy()
        Hx = Jx * (torch.cos(th_xp) + torch.cos(th_xm))
        Hy = Jx * (torch.sin(th_xp) + torch.sin(th_xm))
        Hx += Jy * (torch.cos(th_yp) + torch.cos(th_ym))
        Hy += Jy * (torch.sin(th_yp) + torch.sin(th_ym))
        angH = torch.atan2(Hy, Hx)
        theta_new = 2.0 * angH - theta
        theta_new = ((theta_new + math.pi) % (2 * math.pi)) - math.pi
        self.theta = theta_new

    def sweep(self):
        acc_t = self.metropolis_theta_sweep()
        if self.use_overrelax:
            self.overrelax_theta_sweep()
        acc_s = self.metropolis_sigma_sweep()
        return acc_t, acc_s

    def metropolis_sigma_sweep(self):
        Lx, Ly = self.Lx, self.Ly
        xx = torch.arange(Lx, device=self.device).unsqueeze(1).expand(Lx, Ly)
        yy = torch.arange(Ly, device=self.device).unsqueeze(0).expand(Lx, Ly)
        even = ((xx + yy) % 2 == 0)
        odd = ~even
        acc_sum = 0.0
        total = 0.0
        for mask in [even, odd]:
            dE = self._local_sigma_x_dE_tensor(mask)
            acc = torch.exp(- self.beta * dE)
            rnd = torch.rand(acc.shape, dtype=acc.dtype, device=acc.device)
            take = rnd < acc
            self.sx = torch.where(take, (-self.sx), self.sx)
            total += float(dE.numel())
            acc_sum += float(take.sum().detach().cpu().numpy())
        self._update_zshift_cache()
        for mask in [even, odd]:
            dE = self._local_sigma_y_dE_tensor(mask)
            acc = torch.exp(- self.beta * dE)
            rnd = torch.rand(acc.shape, dtype=acc.dtype, device=acc.device)
            take = rnd < acc
            self.sy = torch.where(take, (-self.sy), self.sy)
            total += float(dE.numel())
            acc_sum += float(take.sum().detach().cpu().numpy())
        self._update_zshift_cache()
        return acc_sum / max(1.0, total)

    def _try_compile(self):
        try:
            backend = "aot_eager"
            self.energy_density_tensor = torch.compile(self.energy_density_tensor, backend=backend, fullgraph=True, dynamic=False)
            self._local_theta_dE_tensor = torch.compile(self._local_theta_dE_tensor, backend=backend, fullgraph=True, dynamic=False)
            self.metropolis_theta_sweep = torch.compile(self.metropolis_theta_sweep, backend=backend, fullgraph=True, dynamic=False)
            self.K_current_tensor = torch.compile(self.K_current_tensor, backend=backend, fullgraph=True, dynamic=False)
            self.O_kappa_tensor = torch.compile(self.O_kappa_tensor, backend=backend, fullgraph=True, dynamic=False)
            self.O_boundary_tensor = torch.compile(self.O_boundary_tensor, backend=backend, fullgraph=True, dynamic=False)
            self._compiled = True
            log("Compiled selected kernels with torch.compile backend aot_eager")
        except Exception as e:
            log(f"torch.compile failed: {e}. Using eager mode")
            self._compiled = False

# =========================
# Unit tests
# =========================

def unit_test_local_dE(model, num_trials=50):
    max_err = 0.0
    for _ in range(num_trials):
        i = np.random.randint(0, model.Lx)
        j = np.random.randint(0, model.Ly)
        E0 = model.measure_energy()
        model.sx[i, j] = -model.sx[i, j]
        model._update_zshift_cache()
        E1 = model.measure_energy()
        dE_exact = E1 - E0
        model.sx[i, j] = -model.sx[i, j]
        model._update_zshift_cache()
        mask = torch.zeros((model.Lx, model.Ly), dtype=torch.bool, device=model.device)
        mask[i, j] = True
        dE_loc = float(model._local_sigma_x_dE_tensor(mask).sum().detach().cpu().numpy())
        max_err = max(max_err, abs(dE_exact - dE_loc))
    for _ in range(num_trials):
        i = np.random.randint(0, model.Lx)
        j = np.random.randint(0, model.Ly)
        E0 = model.measure_energy()
        model.sy[i, j] = -model.sy[i, j]
        model._update_zshift_cache()
        E1 = model.measure_energy()
        dE_exact = E1 - E0
        model.sy[i, j] = -model.sy[i, j]
        model._update_zshift_cache()
        mask = torch.zeros((model.Lx, model.Ly), dtype=torch.bool, device=model.device)
        mask[i, j] = True
        dE_loc = float(model._local_sigma_y_dE_tensor(mask).sum().detach().cpu().numpy())
        max_err = max(max_err, abs(dE_exact - dE_loc))
    return max_err

# =========================
# Measurement helpers
# =========================

def run_block_measurements(model, sweeps_burn, sweeps_meas, thin, log_every):
    for s in range(sweeps_burn):
        acc_t, acc_s = model.sweep()
        if (s + 1) % log_every == 0:
            e = model.measure_energy()
            log(f"  burn-in {s+1}/{sweeps_burn} E={e:.6f} acc_th={acc_t:.3f} acc_sg={acc_s:.3f}")
    K_series = []
    Ok_series = []
    Ob_series = []
    E_series = []
    acc_t_series = []
    acc_s_series = []
    for s in range(sweeps_meas):
        for _ in range(thin):
            acc_t, acc_s = model.sweep()
        acc_t_series.append(acc_t)
        acc_s_series.append(acc_s)
        K_series.append(model.measure_K_current())
        Ok_series.append(model.measure_O_kappa())
        Ob_series.append(model.measure_O_boundary())
        E_series.append(model.measure_energy())
        if (s + 1) % log_every == 0:
            Km, _, _, _ = blocking_stats(K_series)
            log(f"  meas {s+1}/{sweeps_meas} K~{Km:.6f} E={E_series[-1]:.6f}")
    K_mean, K_err, K_bl, K_nb = blocking_stats(K_series)
    N = model.Lx * model.Ly
    A = model.Ly
    beta = float(model.beta.detach().cpu().numpy())
    kappa = beta * np.var(Ok_series, ddof=1) / N
    chi_b = beta * np.var(Ob_series, ddof=1) / A
    return {
        "K_mean": float(K_mean),
        "K_err": float(K_err),
        "K_block_len": int(K_bl),
        "K_num_blocks": int(K_nb),
        "kappa": float(kappa),
        "chi_b": float(chi_b),
        "E_mean": float(np.mean(E_series)),
        "acc_theta": float(np.mean(acc_t_series)),
        "acc_sigma": float(np.mean(acc_s_series)),
    }

def measure_K_fd_eq(Lx, Ly, beta, J, Kp, phi, sweeps_burn, sweeps_meas, thin, seed, device, use_compile, use_overrelax, tag):
    model = HolonStabRotor(Lx=Lx, Ly=Ly, beta=beta, J=J, Kp=Kp, device=device, seed=seed, use_compile=use_compile, use_overrelax=use_overrelax)
    model.set_twist(phi)
    model.reset_angles()
    model.reset_links(p_minus=0.0)
    log(f"[{tag}] burn-in {sweeps_burn} at phi={phi:.6f}")
    for s in range(sweeps_burn):
        acc_t, acc_s = model.sweep()
        if (s + 1) % max(1, sweeps_burn // 5) == 0:
            e = model.measure_energy()
            log(f"  [{tag}] burn {s+1}/{sweeps_burn} E={e:.6f} acc_th={acc_t:.3f} acc_sg={acc_s:.3f}")
    E_series = []
    for s in range(sweeps_meas):
        for _ in range(thin):
            model.sweep()
        E_series.append(model.measure_energy())
    E_mean, E_err, _, _ = blocking_stats(E_series)
    return E_mean, E_err

# =========================
# Two loop RGEs
# =========================

def beta_SM_1loop(a1, a2, a3):
    b1 = 41.0/10.0
    b2 = -19.0/6.0
    b3 = -7.0
    return np.array([b1, b2, b3], dtype=np.float64)

def beta_SM_2loop_matrix():
    b11 = 199.0/50.0
    b12 = 27.0/10.0
    b13 = 44.0/5.0
    b21 = 9.0/10.0
    b22 = 35.0/6.0
    b23 = 12.0
    b31 = 11.0/10.0
    b32 = 9.0/2.0
    b33 = -26.0
    return np.array([[b11, b12, b13],
                     [b21, b22, b23],
                     [b31, b32, b33]], dtype=np.float64)

def run_SM_two_loop(alpha_init, mu_hi, mu_lo, n_steps=2000):
    a = np.array(alpha_init, dtype=np.float64)
    t_hi = math.log(mu_hi)
    t_lo = math.log(mu_lo)
    dt = (t_lo - t_hi) / n_steps
    B2 = beta_SM_2loop_matrix()
    for _ in range(n_steps):
        b1 = beta_SM_1loop(a[0], a[1], a[2])
        b2term = B2 @ a
        da_dt = (a**2) * (b1/(2*math.pi)) + (a**3) * (b2term/((2*math.pi)**2))
        a = a + da_dt * dt
        a = np.clip(a, 1e-6, 2.0)
    return a

def run_one_loop(alpha_init, b_vec, mu_hi, mu_lo):
    a = np.array(alpha_init, dtype=np.float64)
    t_hi = math.log(mu_hi)
    t_lo = math.log(mu_lo)
    dt = t_lo - t_hi
    a_inv = 1.0/a + (b_vec/(2*math.pi))*dt
    return 1.0/np.clip(a_inv, 1e-9, 1e9)

def PS_b_one_loop(content="minimalpp"):
    if content == "minimalpp":
        # Toy example for illustration. Three families. Simplified Higgs set.
        # You can change via CLI if needed.
        b4 = -5.0
        b2L = -2.0
        b2R = -2.0
    else:
        b4 = -4.0
        b2L = -1.5
        b2R = -1.5
    return np.array([b4, b2L, b2R], dtype=np.float64)

def PS_to_SM_match(alpha4, alpha2L, alpha2R, alphaBL):
    alpha3 = alpha4
    alpha2 = alpha2L
    alpha1 = (3.0/5.0) * alpha2R + (2.0/5.0) * alphaBL
    return alpha1, alpha2, alpha3

def run_PS_to_SM(alpha_star, MGUT, MPS, content="minimalpp"):
    a4 = alpha_star
    a2L = alpha_star
    a2R = alpha_star
    # B-L is inside SU(4). For a sketch, use same a4 at MGUT.
    aBL = alpha_star
    bPS = PS_b_one_loop(content)
    aPS = np.array([a4, a2L, a2R], dtype=np.float64)
    aPS_low = run_one_loop(aPS, bPS, MGUT, MPS)
    a4_low, a2L_low, a2R_low = aPS_low
    aBL_low = run_one_loop(np.array([aBL], dtype=np.float64), np.array([-5.0], dtype=np.float64), MGUT, MPS)[0]
    a1_MPS, a2_MPS, a3_MPS = PS_to_SM_match(a4_low, a2L_low, a2R_low, aBL_low)
    a_SM_MZ = run_SM_two_loop([a1_MPS, a2_MPS, a3_MPS], MPS, 91.1876)
    alpha1_MZ, alpha2_MZ, alpha3_MZ = a_SM_MZ
    alpha_em_inv = (5.0/3.0)/alpha1_MZ + 1.0/alpha2_MZ
    s2W = ((3.0/5.0)*alpha1_MZ)/(((3.0/5.0)*alpha1_MZ) + alpha2_MZ)
    return {
        "alpha1_MZ": alpha1_MZ,
        "alpha2_MZ": alpha2_MZ,
        "alpha3_MZ": alpha3_MZ,
        "alpha_em_inv_MZ": alpha_em_inv,
        "sin2thetaW": s2W
    }

# =========================
# Main pipeline
# =========================

def run_pipeline(args):
    device = torch.device("cuda" if torch.cuda.is_available() and not args.cpu else "cpu")
    log(f"Device: {device.type}")
    if device.type == "cuda":
        log(f"CUDA: {torch.cuda.get_device_name(0)}")
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True

    q_min, q_info = compute_qmin_from_yaml(args.snf_yaml)
    C_geo = (q_min ** 2) / ((2 * math.pi) ** 2 * (args.Lx ** 2))
    K_geom = (4.0 * math.pi) / C_geo
    log(f"Geometry Lx={args.Lx} Ly={args.Ly} q_min={q_min} C_geo={C_geo:.6e} K_geom={K_geom:.6e}")

    D_tau = 2.0 * args.Lx / ((2 * math.pi) ** 2)
    D_kappa = 1.0
    D_b = 1.0
    log(f"D_tau={D_tau:.6e} D_kappa={D_kappa:.2f} D_b={D_b:.2f}")

    test_model = HolonStabRotor(Lx=min(16, args.Lx), Ly=min(16, args.Ly), beta=args.beta, J=args.t0, Kp=args.Kp,
                                device=device, seed=args.seed + 99, use_compile=not args.no_compile, use_overrelax=args.use_overrelax)
    err = unit_test_local_dE(test_model, num_trials=40)
    log(f"Local dE unit test max abs error ~ {err:.3e}")

    r_values = np.linspace(args.r_min, args.r_max, args.r_steps).tolist()
    scan = []
    best_idx = None
    best_F = -1e300
    for pass_id in [0, 1]:
        for ir, r in enumerate(r_values):
            J = args.t0 * r
            model = HolonStabRotor(Lx=args.Lx, Ly=args.Ly, beta=args.beta, J=J, Kp=args.Kp,
                                   device=device, seed=args.seed + ir + pass_id*1000, use_compile=not args.no_compile, use_overrelax=args.use_overrelax)
            model.set_twist(0.0)
            model.reset_angles()
            model.reset_links(0.0)
            log(f"[scan {pass_id}] r={r:.6f} J={J:.6f} burn {args.burn_in}")
            for s in range(args.burn_in):
                acc_t, acc_s = model.sweep()
                if (s + 1) % args.log_sweeps == 0:
                    e = model.measure_energy()
                    log(f"  burn {s+1}/{args.burn_in} E={e:.6f} acc_th={acc_t:.3f} acc_sg={acc_s:.3f}")
            log(f"[scan] r={r:.6f} measure {args.meas_sweeps}")
            meas = run_block_measurements(model, 0, args.meas_sweeps, args.thin, args.log_sweeps)
            K_mean = meas["K_mean"]
            kappa = meas["kappa"]
            chi_b = meas["chi_b"]
            F = D_tau * K_mean - D_kappa * kappa - D_b * chi_b
            scan.append({
                "r": r, "J": J, "K": K_mean, "K_err": meas["K_err"],
                "kappa": kappa, "chi_b": chi_b, "F": F,
                "acc_theta": meas["acc_theta"], "acc_sigma": meas["acc_sigma"], "E_mean": meas["E_mean"]
            })
            log(f"  r={r:.6f} K={K_mean:.6f} kappa={kappa:.6e} chi_b={chi_b:.6e} F={F:.6e}")
            if F > best_F:
                best_F = F
                best_idx = len(scan) - 1
        if best_idx is not None:
            best_r = scan[best_idx]["r"]
            if (best_r <= r_values[0] + 1e-12 or best_r >= r_values[-1] - 1e-12) and pass_id == 0:
                span = r_values[-1] - r_values[0]
                r_min2 = max(0.05, r_values[0] - 0.5*span)
                r_max2 = r_values[-1] + 0.5*span
                r_values = np.linspace(r_min2, r_max2, args.r_steps + 2).tolist()
                log(f"Edge maximum at r={best_r:.6f}. Extend r grid to [{r_min2:.3f}, {r_max2:.3f}] with {len(r_values)} points")
                continue
        break

    r_star = scan[best_idx]["r"]
    J_star = scan[best_idx]["J"]
    log(f"HG Canon picked r_star={r_star:.6f} J_star={J_star:.6f} F={scan[best_idx]['F']:.6e}")

    model = HolonStabRotor(Lx=args.Lx, Ly=args.Ly, beta=args.beta, J=J_star, Kp=args.Kp,
                           device=device, seed=args.seed + 7777, use_compile=not args.no_compile, use_overrelax=args.use_overrelax)
    model.set_twist(0.0)
    model.reset_angles()
    model.reset_links(0.0)
    log(f"[refine] burn-in {args.refine_burn_in} at r*")
    for s in range(args.refine_burn_in):
        acc_t, acc_s = model.sweep()
        if (s + 1) % args.log_sweeps == 0:
            e = model.measure_energy()
            log(f"  refine burn {s+1}/{args.refine_burn_in} E={e:.6f} acc_th={acc_t:.3f} acc_sg={acc_s:.3f}")
    log(f"[refine] measure {args.refine_meas} at r*")
    meas_star = run_block_measurements(model, 0, args.refine_meas, args.thin, args.log_sweeps)
    K_macro = meas_star["K_mean"]
    K_macro_err = meas_star["K_err"]
    Z_diag = K_macro / J_star if J_star != 0 else float("nan")

    phi = args.phi_fd
    E_p, E_p_err = measure_K_fd_eq(args.Lx, args.Ly, args.beta, J_star, args.Kp, +phi, args.fd_burn, args.fd_meas, args.thin, args.seed + 1101, device, not args.no_compile, args.use_overrelax, "phi+")
    E_m, E_m_err = measure_K_fd_eq(args.Lx, args.Ly, args.beta, J_star, args.Kp, -phi, args.fd_burn, args.fd_meas, args.thin, args.seed + 1102, device, not args.no_compile, args.use_overrelax, "phi-")
    E0 = meas_star["E_mean"]
    d2E = (E_p - 2.0*E0 + E_m) / (phi**2)
    K_fd_eq = (args.Lx**2) * d2E
    rel_diff = abs(K_macro - K_fd_eq) / max(1e-12, 0.5*(abs(K_macro) + abs(K_fd_eq)))

    sigma = C_geo * K_macro
    alpha_star_inv = 4.0 * math.pi * K_macro + args.c_th
    alpha_star = 1.0 / alpha_star_inv

    # RG section
    band = None
    point_pred = None
    if args.MGUT is not None and args.MPS is not None:
        MGUT = float(args.MGUT)
        MPS = float(args.MPS)
        rg = run_PS_to_SM(alpha_star, MGUT, MPS, content=args.ps_content)
        point_pred = {
            "MGUT": MGUT,
            "MPS": MPS,
            "alpha_em_inv_MZ": float(rg["alpha_em_inv_MZ"]),
            "sin2thetaW_MZ": float(rg["sin2thetaW"]),
            "alpha1_MZ": float(rg["alpha1_MZ"]),
            "alpha2_MZ": float(rg["alpha2_MZ"]),
            "alpha3_MZ": float(rg["alpha3_MZ"])
        }
    else:
        MGUT_grid = np.logspace(args.scan_log10_MGUT_min, args.scan_log10_MGUT_max, args.scan_MGUT_steps)
        MPS_grid = np.logspace(args.scan_log10_MPS_min, args.scan_log10_MPS_max, args.scan_MPS_steps)
        vals = []
        count = 0
        for MGUT in MGUT_grid:
            for MPS in MPS_grid:
                if MPS >= MGUT:
                    continue
                rg = run_PS_to_SM(alpha_star, MGUT, MPS, content=args.ps_content)
                vals.append([MGUT, MPS, rg["alpha_em_inv_MZ"], rg["sin2thetaW"]])
                count += 1
                if count % max(1, (len(MGUT_grid)*len(MPS_grid))//10) == 0:
                    log(f"  RG scan progress {count} items")
        vals = np.array(vals, dtype=np.float64)
        if vals.size > 0:
            ae = vals[:, 2]
            s2 = vals[:, 3]
            band = {
                "alpha_em_inv_MZ_min": float(ae.min()),
                "alpha_em_inv_MZ_max": float(ae.max()),
                "sin2thetaW_min": float(s2.min()),
                "sin2thetaW_max": float(s2.max()),
                "samples": int(vals.shape[0])
            }

    summary = {
        "geometry": {"Lx": args.Lx, "Ly": args.Ly, "q_min": q_min, "C_geo": C_geo, "K_geom": K_geom},
        "canon_constants": {"D_tau": D_tau, "D_kappa": D_kappa, "D_b": D_b},
        "inputs": {"beta": args.beta, "t0": args.t0, "Kp": args.Kp, "r_grid": r_values},
        "scan": scan,
        "r_star": r_star,
        "J_star": J_star,
        "meas_star": {
            "K_macro": K_macro, "K_macro_err": K_macro_err,
            "kappa_star": meas_star["kappa"], "chi_b_star": meas_star["chi_b"],
            "K_block_len": meas_star["K_block_len"], "K_num_blocks": meas_star["K_num_blocks"],
            "acc_theta": meas_star["acc_theta"], "acc_sigma": meas_star["acc_sigma"],
            "E_mean": meas_star["E_mean"]
        },
        "cross_checks": {"K_fd_eq": K_fd_eq, "rel_diff_K_vs_KfdEq": rel_diff},
        "sigma": sigma,
        "alpha_star_inv": alpha_star_inv,
        "alpha_star": alpha_star,
        "snf_info": q_info,
        "rge_point_prediction": point_pred,
        "rge_scan_band": band,
        "ps_content": args.ps_content
    }

    log("========= FINAL REPORT =========")
    log(f"r_star = {r_star:.6f}, J_star = {J_star:.6f}")
    log(f"K_macro = {K_macro:.6f} +- {K_macro_err:.6f}  Z_diag=K/J={Z_diag:.6f}")
    log(f"K_fd_eq = {K_fd_eq:.6f}  rel diff = {rel_diff:.3e}")
    log(f"sigma = {sigma:.6e}")
    log(f"alpha_star_inv = {alpha_star_inv:.6f}")
    if point_pred is not None:
        log(f"alpha_em_inv(MZ) at MGUT={point_pred['MGUT']:.3e}, MPS={point_pred['MPS']:.3e} is {point_pred['alpha_em_inv_MZ']:.6f}")
        log(f"sin^2 theta_W(MZ) = {point_pred['sin2thetaW_MZ']:.6f}")
    elif band is not None:
        log(f"RG scan band for alpha_em_inv(MZ): [{band['alpha_em_inv_MZ_min']:.3f}, {band['alpha_em_inv_MZ_max']:.3f}]")
        log(f"RG scan band for sin^2 theta_W(MZ): [{band['sin2thetaW_min']:.3f}, {band['sin2thetaW_max']:.3f}] over {band['samples']} samples")
    log("================================")

    if args.out:
        with open(args.out, "w") as f:
            json.dump(summary, f, indent=2)
        log(f"Wrote JSON summary to {args.out}")
    return summary

# =========================
# CLI
# =========================

def build_parser():
    p = argparse.ArgumentParser(description="First principles Holon micro to alpha_star and alpha_em pipeline")
    p.add_argument("--Lx", type=int, default=96)
    p.add_argument("--Ly", type=int, default=96)
    p.add_argument("--beta", type=float, default=2.0)
    p.add_argument("--t0", type=float, default=1.0)
    p.add_argument("--Kp", type=float, default=1.0)
    p.add_argument("--use_overrelax", action="store_true")
    p.add_argument("--r_min", type=float, default=0.6)
    p.add_argument("--r_max", type=float, default=2.6)
    p.add_argument("--r_steps", type=int, default=11)
    p.add_argument("--burn_in", type=int, default=800)
    p.add_argument("--meas_sweeps", type=int, default=1200)
    p.add_argument("--refine_burn_in", type=int, default=1500)
    p.add_argument("--refine_meas", type=int, default=2500)
    p.add_argument("--thin", type=int, default=2)
    p.add_argument("--log_sweeps", type=int, default=100)
    p.add_argument("--phi_fd", type=float, default=0.04)
    p.add_argument("--fd_burn", type=int, default=600)
    p.add_argument("--fd_meas", type=int, default=1000)
    p.add_argument("--seed", type=int, default=20250812)
    p.add_argument("--snf_yaml", type=str, default=None)
    p.add_argument("--c_th", type=float, default=0.0)
    p.add_argument("--out", type=str, default="hg_alpha_full_summary.json")
    p.add_argument("--cpu", action="store_true")
    p.add_argument("--no_compile", action="store_true")
    # RG options
    p.add_argument("--MPS", type=float, default=None, help="Set Pati Salam scale in GeV. If not set, scan mode")
    p.add_argument("--MGUT", type=float, default=None, help="Set unification scale in GeV. If not set, scan mode")
    p.add_argument("--ps_content", type=str, default="minimalpp", help="Pati Salam content key")
    p.add_argument("--scan_log10_MPS_min", type=float, default=12.0)
    p.add_argument("--scan_log10_MPS_max", type=float, default=15.5)
    p.add_argument("--scan_MPS_steps", type=int, default=14)
    p.add_argument("--scan_log10_MGUT_min", type=float, default=15.6)
    p.add_argument("--scan_log10_MGUT_max", type=float, default=17.6)
    p.add_argument("--scan_MGUT_steps", type=int, default=12)
    return p

if __name__ == "__main__":
    args = build_parser().parse_args()
    t0 = time.time()
    log("Starting full pipeline")
    try:
        run_pipeline(args)
    except KeyboardInterrupt:
        log("Interrupted")
    except Exception as e:
        log(f"Fatal error: {e}")
        raise
    finally:
        log(f"Total wall time: {(time.time() - t0)/60.0:.2f} min")
