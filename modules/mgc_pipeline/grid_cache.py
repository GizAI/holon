import torch

def _real_dtype_of(cdtype):
    return torch.float32 if cdtype == torch.complex64 else torch.float64

class GridCache:
    def __init__(self, Lx, Ly, periodic, J, device, dtype, wall=False, wall_x=0,
                 anis_eps=0.0, boundary_eta=0.0):
        self.Lx, self.Ly = Lx, Ly
        self.periodic = periodic
        self.J = J
        self.device = device
        self.dtype = dtype
        self.wall = wall
        self.wall_x = wall_x % max(1, Lx)
        self.anis_eps = float(anis_eps)
        self.boundary_eta = float(boundary_eta)
        self.N, self.bonds = self._build_grid(Lx, Ly, periodic)
        self.D = 1 << self.N
        self.diagE, self.states = self._precompute_diag(self.N, self.bonds, J, device)
        self.masks = [(1 << i) for i in range(self.N)]
        # warm start stores
        self.warm_minus = {}; self.warm_plus = {}
        # sz sum per basis vector for Davidson preconditioner
        with torch.no_grad():
            bits = self.states.clone()
            pop = bits.clone()
            for shift in [1,2,4,8,16]:
                pop = pop - ((pop >> shift) & ((1 << shift) - 1))
            n1 = pop
            n0 = self.N - n1
            self.sz_sum = (n0 - n1).to(_real_dtype_of(dtype))
        self._build_apply()

    def _build_grid(self, Lx, Ly, periodic):
        def idx(x, y): return x + y * Lx
        bonds = []
        for y in range(Ly):
            for x in range(Lx):
                i = idx(x, y)
                # x bonds, store left column x and axis tag
                if x + 1 < Lx:
                    bonds.append((i, idx(x+1, y), 'x', x, False))  # not wrap
                elif periodic:
                    bonds.append((i, idx(0, y), 'x', x, True))     # wrap along x
                # y bonds, axis tag only
                if y + 1 < Ly:
                    bonds.append((i, idx(x, y+1), 'y', None, False))  # not wrap
                elif periodic:
                    bonds.append((i, idx(x, 0), 'y', None, True))     # wrap along y
        return Lx*Ly, bonds

    @torch.no_grad()
    def _precompute_diag(self, N, bonds, J, device):
        D = 1 << N
        states = torch.arange(D, device=device, dtype=torch.long)
        diagE = torch.zeros(D, device=device, dtype=torch.float32)
        cut_left = (self.wall_x - 1) % max(1, self.Lx)

        for (i, j, axis, x_left, is_wrap) in bonds:
            # base coupling with anisotropy
            if axis == 'x':
                J_axis = J * (1.0 + self.anis_eps)
                # domain-wall flip only on the cut bond between (wall_x-1) and wall_x
                flip = (self.wall and (x_left is not None) and (x_left == cut_left))
                s_cut = -1.0 if flip else 1.0
                s_boundary = 1.0
            else:
                J_axis = J * (1.0 - self.anis_eps)
                s_cut = 1.0
                # optional boundary weakening on y-wrap bonds
                s_boundary = (1.0 - self.boundary_eta) if is_wrap else 1.0

            si = 1.0 - 2.0 * ((states >> i) & 1).to(torch.float32)
            sj = 1.0 - 2.0 * ((states >> j) & 1).to(torch.float32)
            diagE += -(J_axis * s_cut * s_boundary) * si * sj

        return diagE, states

    def _apply_H_param(self, v, h, eps):
        out = self.diagE.to(v.dtype) * v
        for i, m in enumerate(self.masks):
            si = 1.0 - 2.0 * ((self.states >> i) & 1).to(v.real.dtype)
            out = out + (-eps) * si * v
            out = out + (-h) * v.index_select(0, self.states ^ m)
        return out

    def _build_apply(self):
        if self.dtype in (torch.complex64, torch.complex128):
            self.apply = self._apply_H_param
            self.compiled = False
        else:
            try:
                self.apply = torch.compile(self._apply_H_param, mode="reduce-overhead")
                self.compiled = True
            except Exception:
                self.apply = self._apply_H_param
                self.compiled = False

    def apply_H(self, v, h, eps):
        return self.apply(v, h, eps)

    def nearest_warm(self, h, sign):
        store = self.warm_minus if sign < 0 else self.warm_plus
        if not store: return None, None
        keys = list(store.keys())
        idx = min(range(len(keys)), key=lambda i: abs(keys[i] - h))
        k = keys[idx]
        return k, store[k]

    def put_warm(self, h, sign, psi):
        store = self.warm_minus if sign < 0 else self.warm_plus
        k = float(round(h, 8))
        store[k] = psi.detach().clone()
        if len(store) > 6:
            ks = list(store.keys())
            far = max(ks, key=lambda kk: abs(kk - k))
            store.pop(far, None)
