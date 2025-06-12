import numpy as np
import subprocess
import os

# Parameters
box_size = 100.0  # Angstrom
num_grains = 10
# Construct the absolute path to atomsk.exe
# Assuming atomsk.exe is in the bin directory at the project root
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
atomsk_path = os.path.join(project_root, 'bin', 'atomsk.exe')
# Output prefix for generated files
output_prefix = 'voronoi10'
# Seed file - assuming it's in the inputs directory
seed_file = os.path.join(project_root, 'inputs', 'fcc_Al_unitcell.lmp')

# --- Create a placeholder seed file in LAMMPS data format ---
# A simple FCC Al unit cell (create in inputs directory if it doesn't exist)
seed_file_path_inputs = os.path.join(project_root, 'inputs', 'fcc_Al_unitcell.lmp')
if not os.path.exists(seed_file_path_inputs):
    print(f"Creating a placeholder seed file: {seed_file_path_inputs}")
    # Ensure the inputs directory exists before creating the file
    os.makedirs(os.path.join(project_root, 'inputs'), exist_ok=True)
    with open(seed_file_path_inputs, 'w') as f:
        f.write("LAMMPS data file via Atomsk\n\n")
        f.write("1 atoms\n")
        f.write("1 atom types\n\n")
        f.write("0.0 4.05 xlo xhi\n")
        f.write("0.0 4.05 ylo yhi\n")
        f.write("0.0 4.05 zlo zhi\n")
        f.write("0.0 4.05 ylo yhi\n") # Corrected ylo/yhi line
        f.write("0.0 4.05 zlo zhi\n") # Corrected zlo/zhi line
        f.write("\nMasses\n\n") # Added Masses section
        f.write("1 26.981540\n") # Added Al mass
        f.write("\nAtoms # atomic\n\n")
        f.write("1 1 0.0 0.0 0.0\n") # Atom ID, atom type, x, y, z
# ---------------------------------------------------------

# Generate random grain centers
np.random.seed(42)
# Generate centers within the box size
grain_centers = np.random.uniform(0, box_size, size=(num_grains, 3))

# Generate unique orientations for each grain (as Euler angles in degrees)
orientations = []
for i in range(num_grains):
    # Random Euler angles (phi1, Phi, phi2)
    phi1, Phi, phi2 = np.random.uniform(0, 360, 3)
    orientations.append((phi1, Phi, phi2))

# Write Atomsk parameter file (output to inputs directory)
param_file_name = f'{output_prefix}.txt'
param_file_path = os.path.join(project_root, 'inputs', param_file_name)
with open(param_file_path, 'w') as f:
    f.write(f"box {box_size:.2f} {box_size:.2f} {box_size:.2f}\n")
    for i in range(num_grains):
        center = grain_centers[i]
        orientation = orientations[i]
        f.write(f"node {center[0]:.3f} {center[1]:.3f} {center[2]:.3f} {orientation[0]:.2f} {orientation[1]:.2f} {orientation[2]:.2f}\n")

# Output LAMMPS file path (output to inputs directory)
output_lmp_file = os.path.join(project_root, 'inputs', f'{output_prefix}.lmp')

# Build the Atomsk command as a list of strings
atomsk_command = [
    atomsk_path,
    '--polycrystal',
    seed_file_path_inputs, # Seed file from inputs directory
    param_file_path, # Parameter file from inputs directory
    output_lmp_file, # Output LAMMPS file to inputs directory
    '-wrap',        # Wrap atoms back into the box
    # '-duplicate', '1', '1', '1' # No need to duplicate here, box size is defined
]

print(f"Running Atomsk command: {' '.join(atomsk_command)}")
# Use shell=True for easier path handling on Windows, and check=True to raise an error if the command fails
result = subprocess.run(atomsk_command, shell=True, check=True, capture_output=True, text=True)

print("Atomsk stdout:")
print(result.stdout)
print("Atomsk stderr:")
print(result.stderr)

print(f"Voronoi structure with {num_grains} grains generated as {output_lmp_file}")

# Clean up the generated parameter file (optional)
# os.remove(param_file_path)

# Clean up the generated shell script if it exists from previous attempts
if os.path.exists('generate_voronoi.sh'): # Assuming this might be generated in the script directory
    os.remove('generate_voronoi.sh') 