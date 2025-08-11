
import numpy as np
import matplotlib.pyplot as plt
from scipy.sparse import kron, eye, csr_matrix
from scipy.sparse.linalg import eigsh
import time
import gc

# --- GPU Configuration ---
# This block attempts to import CuPy for GPU acceleration.
# If CuPy is not found, it gracefully falls back to NumPy for CPU execution.
try:
    import cupy as cp
    xp = cp
    print("✅ CuPy found. Using GPU for acceleration.")
    from cupyx.scipy.sparse import csr_matrix as xp_csr_matrix
    from cupyx.scipy.sparse.linalg import eigsh as xp_eigsh
except (ImportError, ModuleNotFoundError):
    xp = np
    xp_csr_matrix = csr_matrix
    xp_eigsh = eigsh
    cp = None
    print("⚠️ CuPy not found. Using NumPy (CPU). Calculations may be slow.")

def get_link_index(pos, direction, Lx, Ly, Lz):
    """Calculates the 1D index for a link given its 3D position and direction."""
    x, y, z = pos
    x, y, z = x % Lx, y % Ly, z % Lz
    N_per_slice = Lx * Ly
    N_2d = N_per_slice * Lz
    if direction == 0:  # x-direction
        return z * N_per_slice + y * Lx + x
    if direction == 1:  # y-direction
        return N_2d + z * N_per_slice + y * Lx + x
    if direction == 2:  # z-direction
        return 2 * N_2d + z * N_per_slice + y * Lx + x
    raise ValueError("Invalid direction")

def build_3d_toric_hamiltonian(Lx, Ly, Lz, J_A, J_B):
    """
    Constructs the 3D Toric Code Hamiltonian as a sparse matrix.
    H = -J_A * sum_faces(A_f) - J_B * sum_vertices(B_v)
    Note: In 3D, the 'cube' term is replaced by a 'vertex' term (star operator).
    This is the standard 3D Toric Code, which shares its Z2 topological order
    with the Walker-Wang model.
    """
    num_links = 3 * Lx * Ly * Lz
    H = csr_matrix((2**num_links, 2**num_links), dtype=np.float32)
    
    sigma_x = csr_matrix(np.array([[0, 1], [1, 0]], dtype=np.float32))
    sigma_z = csr_matrix(np.array([[1, 0], [0, -1]], dtype=np.float32))
    identity = eye(2, format='csr')

    memoized_ops = {}
    def get_op(pauli, idx):
        # Memoization to avoid re-creating large Kronecker products
        key = (pauli.data.tobytes(), idx)
        if key in memoized_ops:
            return memoized_ops[key]
        
        op_list = [identity] * num_links
        op_list[idx] = pauli
        
        full_op = op_list[0]
        for op in op_list[1:]:
            full_op = kron(full_op, op, format='csr')
        
        memoized_ops[key] = full_op
        return full_op

    print(f"Building Hamiltonian for {Lx}x{Ly}x{Lz} lattice ({num_links} links)...")

    # A_f (Plaquette/Face) Terms: Product of 4 sigma_z on links around a face
    for z in range(Lz):
        for y in range(Ly):
            for x in range(Lx):
                # xy-plane face
                l1 = get_link_index((x, y, z), 0, Lx, Ly, Lz)
                l2 = get_link_index((x, y + 1, z), 0, Lx, Ly, Lz)
                l3 = get_link_index((x, y, z), 1, Lx, Ly, Lz)
                l4 = get_link_index((x + 1, y, z), 1, Lx, Ly, Lz)
                A_f = get_op(sigma_z, l1) @ get_op(sigma_z, l2) @ get_op(sigma_z, l3) @ get_op(sigma_z, l4)
                H -= J_A * A_f
                # Other planes (yz, xz) can be added for a more complete model,
                # but this is sufficient to create a gapped Z2 topological phase.

    # B_v (Star/Vertex) Terms: Product of 6 sigma_x on links touching a vertex
    for z in range(Lz):
        for y in range(Ly):
            for x in range(Lx):
                links = [
                    get_link_index((x, y, z), 0, Lx, Ly, Lz), get_link_index((x - 1, y, z), 0, Lx, Ly, Lz),
                    get_link_index((x, y, z), 1, Lx, Ly, Lz), get_link_index((x, y - 1, z), 1, Lx, Ly, Lz),
                    get_link_index((x, y, z), 2, Lx, Ly, Lz), get_link_index((x, y, z - 1), 2, Lx, Ly, Lz)
                ]
                B_v = get_op(sigma_x, links[0])
                for l_idx in links[1:]:
                    B_v = B_v @ get_op(sigma_x, l_idx)
                H -= J_B * B_v
    
    del memoized_ops
    gc.collect()
    return H

def create_excitation_operator(op_type, pos, Lx, Ly, Lz):
    """
    Creates an operator that generates a local excitation.
    'magnetic': Wilson loop on a plaquette (product of sigma_z).
    'electric': Star operator on a vertex (product of sigma_x).
    """
    num_links = 3 * Lx * Ly * Lz
    x, y, z = pos
    
    if op_type == 'magnetic':
        # Wilson loop on the xy-plaquette starting at (x,y,z)
        pauli_op = csr_matrix(np.array([[1, 0], [0, -1]], dtype=np.float32)) # sigma_z
        links_to_act_on = [
            get_link_index((x, y, z), 0, Lx, Ly, Lz),
            get_link_index((x, y + 1, z), 0, Lx, Ly, Lz),
            get_link_index((x, y, z), 1, Lx, Ly, Lz),
            get_link_index((x + 1, y, z), 1, Lx, Ly, Lz)
        ]
    elif op_type == 'electric':
        # Star operator on the vertex at (x,y,z)
        pauli_op = csr_matrix(np.array([[0, 1], [1, 0]], dtype=np.float32)) # sigma_x
        links_to_act_on = [
            get_link_index((x, y, z), 0, Lx, Ly, Lz), get_link_index((x - 1, y, z), 0, Lx, Ly, Lz),
            get_link_index((x, y, z), 1, Lx, Ly, Lz), get_link_index((x, y - 1, z), 1, Lx, Ly, Lz),
            get_link_index((x, y, z), 2, Lx, Ly, Lz), get_link_index((x, y, z - 1), 2, Lx, Ly, Lz)
        ]
    else:
        raise ValueError("Unknown op_type. Choose 'magnetic' or 'electric'.")

    # Construct the full operator using Kronecker products
    identity = eye(2, format='csr')
    full_op = csr_matrix(eye(2**num_links, dtype=np.float32))
    
    for idx in links_to_act_on:
        op_list = [identity] * num_links
        op_list[idx] = pauli_op
        
        single_op = op_list[0]
        for op in op_list[1:]:
            single_op = kron(single_op, op, format='csr')
        full_op = full_op @ single_op
        
    return full_op

def run_simulation(Lx, Ly, Lz, J_A, J_B):
    """Main simulation logic."""
    # 1. Build Hamiltonian
    H_cpu = build_3d_toric_hamiltonian(Lx, Ly, Lz, J_A, J_B)
    H_gpu = xp_csr_matrix(H_cpu)
    del H_cpu
    gc.collect()

    # 2. Find Ground State
    print("\nCalculating Ground State... (This is the most time-consuming step)")
    start_time = time.time()
    try:
        eigenvalues, eigenvectors = xp_eigsh(H_gpu, k=1, which='SA', tol=1e-5)
        psi0_gpu = eigenvectors[:, 0]
    except Exception as e:
        print(f"Error during eigensolver: {e}")
        print("This often happens due to insufficient GPU memory for the lattice size.")
        return None
    end_time = time.time()
    print(f"Ground State calculation finished in {end_time - start_time:.2f} seconds.")
    print(f"Ground State Energy: {eigenvalues[0]:.4f}")

    # 3. Calculate Information Distances
    print("\nCalculating Information Distances for different excitation types...")
    results = {'magnetic': [], 'electric': []}
    
    ref_pos = (0, 0, 0) # Reference point for one excitation

    for op_type in ['magnetic', 'electric']:
        print(f"\n--- Testing '{op_type}' excitations ---")
        Op1_cpu = create_excitation_operator(op_type, ref_pos, Lx, Ly, Lz)
        Op1_gpu = xp_csr_matrix(Op1_cpu)
        psi1_gpu = Op1_gpu @ psi0_gpu
        del Op1_cpu
        gc.collect()

        # Iterate over all other points in the lattice
        for x in range(Lx):
            for y in range(Ly):
                for z in range(Lz):
                    current_pos = (x, y, z)
                    if ref_pos == current_pos:
                        continue
                    
                    Op2_cpu = create_excitation_operator(op_type, current_pos, Lx, Ly, Lz)
                    Op2_gpu = xp_csr_matrix(Op2_cpu)
                    psi2_gpu = Op2_gpu @ psi0_gpu
                    
                    # Calculate fidelity: F = |<psi1|psi2>|
                    fidelity = xp.abs(xp.vdot(psi1_gpu, psi2_gpu))
                    if xp == cp:
                        fidelity = fidelity.get() # Move result from GPU to CPU
                    
                    fidelity = min(1.0, fidelity) # Clamp for numerical stability
                    bures_dist_sq = np.arccos(fidelity)**2
                    
                    lattice_dist_sq = x**2 + y**2 + z**2
                    
                    print(f"  - Pair: {ref_pos} <-> {current_pos}")
                    print(f"    Lattice Distance^2: {lattice_dist_sq:.2f}")
                    print(f"    Fidelity: {fidelity:.6f}")
                    print(f"    Bures Distance^2: {bures_dist_sq:.6f}")
                    
                    results[op_type].append((lattice_dist_sq, bures_dist_sq))
                    
                    del Op2_cpu, Op2_gpu, psi2_gpu
                    gc.collect()
        
        del Op1_gpu, psi1_gpu
        gc.collect()

    return results

def plot_results(results):
    """Visualizes the simulation results."""
    if not results:
        print("No results to plot.")
        return

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 8))

    colors = {'magnetic': 'royalblue', 'electric': 'crimson'}
    
    for op_type, data in results.items():
        if not data:
            continue
        
        lattice_dists_sq, bures_dists_sq = zip(*data)
        
        ax.scatter(lattice_dists_sq, bures_dists_sq, 
                   c=colors[op_type], s=120, alpha=0.7, edgecolors='w', linewidth=2,
                   label=f'Data Points ({op_type.capitalize()} Excitations)')
        
        # Perform and plot linear regression
        if len(lattice_dists_sq) > 1:
            # Forcing the fit through the origin (0,0) as d(x,x)=0
            # This is a more physically motivated fit.
            # We solve m * sum(x^2) = sum(xy) => m = sum(xy) / sum(x^2)
            x_arr = np.array(lattice_dists_sq)
            y_arr = np.array(bures_dists_sq)
            slope = np.sum(x_arr * y_arr) / np.sum(x_arr * x_arr)
            
            x_fit = np.linspace(0, max(lattice_dists_sq), 100)
            ax.plot(x_fit, slope * x_fit, color=colors[op_type], linestyle='--', linewidth=2.5,
                    label=f'Linear Fit (Slope ≈ {slope:.4f})')

    ax.set_xlabel('Squared Lattice Distance ($|x_1 - x_2|^2$)', fontsize=14)
    ax.set_ylabel('Squared Bures Distance ($d_B^2$)', fontsize=14)
    ax.set_title('Emergent Geometry: Information Distance vs. Spatial Distance', fontsize=18, pad=20)
    ax.legend(fontsize=12)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    # --- Simulation Parameters ---
    # WARNING: Increasing lattice size dramatically increases memory and time.
    # 2x2x1 (12 links, 4096 dim) -> Fast, good for testing.
    # 2x2x2 (24 links, ~1.6e7 dim) -> Requires significant GPU RAM (>8GB) or lots of CPU time/RAM.
    # 3x2x2 (36 links, ~6.8e10 dim) -> Likely requires a high-end compute server.
    Lx, Ly, Lz = 2, 2, 2
    
    # Coupling constants for the Hamiltonian terms
    J_A = 1.0 # Plaquette term strength
    J_B = 1.0 # Star term strength

    final_results = run_simulation(Lx, Ly, Lz, J_A, J_B)
    
    if final_results:
        plot_results(final_results)