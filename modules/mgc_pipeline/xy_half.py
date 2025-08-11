import torch
import math

def _real_dtype_of(cdtype):
    return torch.float32 if cdtype == torch.complex64 else torch.float64

class XYHalfFilling:
    def __init__(self, Lx, Ly, t=1.0, delta=0.0, device="cuda", dtype=None,
                 phi=0.0, periodic=True, twist_mode="twist", wall_x=0):
        self.Lx, self.Ly = Lx, Ly
        self.N = Lx * Ly
        self.t = float(t)
        self.delta = float(delta)
        self.device = device
        self.dtype = dtype
        self.phi = float(phi)
        self.periodic = periodic
        self.twist_mode = twist_mode  # "twist" or "wall"
        self.wall_x = int(wall_x) % max(1, Lx)
        # build lattice bonds
        self.bonds = self._build_bonds()
        self.D = 1 << self.N
        self.states = torch.arange(self.D, device=device, dtype=torch.long)
        self.diagE = self._precompute_diag()
        # sz sum per basis vector for Davidson preconditioner
        with torch.no_grad():
            bits = self.states.clone()
            pop = bits.clone()
            for shift in [1,2,4,8,16]:
                pop = pop - ((pop >> shift) & ((1 << shift) - 1))
            n1 = pop
            n0 = self.N - n1
            self.sz_sum = (n0 - n1).to(_real_dtype_of(dtype))

    def _build_bonds(self):
        def idx(x,y): return x + y*self.Lx
        bonds = []
        for y in range(self.Ly):
            for x in range(self.Lx):
                i = idx(x,y)
                # x bonds with left column x
                if x + 1 < self.Lx:
                    x2, wrapx = (x+1, False)
                    j = idx(x2,y)
                    bonds.append((i, j, 'x', x, wrapx))
                elif self.periodic:
                    x2, wrapx = (0, True)
                    j = idx(x2,y)
                    bonds.append((i, j, 'x', x, wrapx))
                # y bonds
                if y + 1 < self.Ly:
                    y2, wrapy = (y+1, False)
                    j = idx(x, y2)
                    bonds.append((i, j, 'y', None, wrapy))
                elif self.periodic:
                    y2, wrapy = (0, True)
                    j = idx(x, y2)
                    bonds.append((i, j, 'y', None, wrapy))
        return bonds

    def _phase_for_xbond(self, x_left, wrapx):
        if self.twist_mode == "twist":
            # uniform Peierls twist along x
            return complex(torch.cos(torch.tensor(self.phi/self.Lx)), torch.sin(torch.tensor(self.phi/self.Lx)))
        else:
            # localize the full phase on the cut between (wall_x-1) and wall_x
            cut_left = (self.wall_x - 1) % self.Lx
            if x_left == cut_left:
                return complex(torch.cos(torch.tensor(self.phi)), torch.sin(torch.tensor(self.phi)))
            return 1.0 + 0.0j

    @torch.no_grad()
    def _precompute_diag(self):
        diagE = torch.zeros(self.D, device=self.device, dtype=torch.float32)

        # Interaction term: delta * n_i * n_j for all bonds
        for (i, j, axis, x_left, wrapflag) in self.bonds:
            ni = ((self.states >> i) & 1).to(torch.float32)
            nj = ((self.states >> j) & 1).to(torch.float32)
            diagE += self.delta * ni * nj

        return diagE

    def apply_H(self, v):
        """Apply XY Hamiltonian with twist."""
        out = self.diagE.to(v.dtype) * v

        for (i, j, axis, x_left, wrapflag) in self.bonds:
            if axis == 'x':
                ph = self._phase_for_xbond(x_left, wrapflag)
                out = out + self._hop_term(v, i, j, -self.t, ph)
            else:
                out = out + self._hop_term(v, i, j, -self.t, 1.0 + 0.0j)
        return out

    def _hop_term(self, v, i, j, amp, phase):
        """Implement XY hopping with phase."""
        # Get states where exactly one of i,j is occupied
        mask_i = 1 << i
        mask_j = 1 << j

        # i occupied, j empty -> j occupied, i empty
        states_flip_ij = self.states ^ mask_i ^ mask_j
        valid_ij = ((self.states & mask_i) != 0) & ((self.states & mask_j) == 0)

        # j occupied, i empty -> i occupied, j empty
        states_flip_ji = self.states ^ mask_i ^ mask_j
        valid_ji = ((self.states & mask_j) != 0) & ((self.states & mask_i) == 0)

        # Apply hopping with phase
        phase_tensor = torch.tensor(phase, device=v.device, dtype=v.dtype)
        hop_ij = amp * phase_tensor * valid_ij.to(v.dtype)
        hop_ji = amp * torch.conj(phase_tensor) * valid_ji.to(v.dtype)

        out = hop_ij * v.index_select(0, states_flip_ij)
        out = out + hop_ji * v.index_select(0, states_flip_ji)

        return out
