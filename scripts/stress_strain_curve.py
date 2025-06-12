import numpy as np
import matplotlib.pyplot as plt
import re

# Read the data from lammps.log
timesteps = []
stresses = []  # Pzz values
strains = []   # Calculated from Lz

with open('lammps.log', 'r') as f:
    lines = f.readlines()

# Use regex to find the header line and extract column indices dynamically
header_line = None
header_parts = []
for i, line in enumerate(lines):
    if 'Step' in line and 'Temp' in line and 'Press' in line:
        # Use regex to handle variable spacing
        match = re.search(r'(Step.*Temp.*PotEng.*KinEng.*TotEng.*Press.*Pxx.*Pyy.*Pzz.*Pxy.*Pxz.*Pyz.*Lx.*Ly.*Lz)', line)
        if match:
            header_line = line
            # Split based on whitespace and filter out empty strings
            header_parts = [part for part in header_line.split() if part]
            start_idx = i + 1
            break

if header_line is None:
    print("Error: Could not find the header line in lammps.log")
else:
    try:
        # Find column indices based on header parts
        step_col = header_parts.index('Step')
        pzz_col = header_parts.index('Pzz')
        lz_col = header_parts.index('Lz')

        # Assume initial Lz from the first data line after header
        initial_Lz = None

        # Read the data from all thermo blocks
        for line in lines[start_idx:]:
            if line.strip() and not line.startswith('Loop') and not line.startswith('elapsed') and not line.startswith('Total') and not line.startswith('cpu') and not line.startswith('MPI') and not line.startswith('Section') and not line.startswith('Neigh') and not line.startswith('Histogram') and not line.startswith('Nlocal') and not line.startswith('Nghost') and not line.startswith('Neighs') and not line.startswith('FullNghs'):
                 # Split based on whitespace and filter out empty strings
                parts = [part for part in line.split() if part]

                if len(parts) > max(step_col, pzz_col, lz_col):
                    current_timestep = int(parts[step_col])
                    current_pzz = float(parts[pzz_col])
                    current_Lz = float(parts[lz_col])

                    if initial_Lz is None and current_timestep == 0:
                        initial_Lz = current_Lz

                    if initial_Lz is not None:
                        strain = (current_Lz - initial_Lz) / initial_Lz

                        timesteps.append(current_timestep)
                        stresses.append(current_pzz)
                        strains.append(strain)


        if not timesteps:
            print("Error: No data points found after header.")
        else:
            # Convert to numpy arrays
            timesteps = np.array(timesteps)
            stresses = np.array(stresses)
            strains = np.array(strains)

            # Create the plot
            plt.figure(figsize=(10, 6))
            plt.plot(strains, stresses, 'b-', linewidth=2)

            # Add labels and title
            plt.xlabel('Engineering Strain', fontsize=12)
            plt.ylabel('Engineering Stress (eV/Å³)', fontsize=12)
            plt.title('Stress-Strain Curve from Uniaxial Tensile Test', fontsize=14)

            # Add grid
            plt.grid(True, linestyle='--', alpha=0.7)

            # Find and annotate yield point (approximate - usually the peak stress before significant drop)
            if len(stresses) > 1:
                # Find index of maximum stress as potential yield point
                yield_point_idx = np.argmax(stresses)
                # Check if maximum stress is not at the very beginning (timestep 0)
                if timesteps[yield_point_idx] > 0:
                     plt.plot(strains[yield_point_idx], stresses[yield_point_idx], 'ro', label='Approx. Yield Point')
                     plt.annotate(f'Approx. Yield: ({strains[yield_point_idx]:.4f}, {stresses[yield_point_idx]:.2f})',
                                 xy=(strains[yield_point_idx], stresses[yield_point_idx]),
                                 xytext=(strains[yield_point_idx]+0.005, stresses[yield_point_idx]+0.005),
                                 textcoords='offset points',
                                 arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=.5'))
                else:
                     print("Maximum stress found at timestep 0, skipping yield point annotation.")


            # Add legend
            plt.legend()

            # Save the plot
            plt.savefig('stress_strain_curve.png', dpi=300, bbox_inches='tight')
            plt.close()

            # Print some key values
            print(f"Maximum stress: {np.max(stresses):.2f} eV/Å³")
            print(f"Maximum strain: {np.max(strains):.4f}")
            if len(stresses) > 1 and timesteps[yield_point_idx] > 0:
                 print(f"Approx. Yield stress: {stresses[yield_point_idx]:.2f} eV/Å³")
                 print(f"Approx. Yield strain: {strains[yield_point_idx]:.4f}")

            # Print strain range
            print(f"\nStrain range: {np.min(strains):.4f} to {np.max(strains):.4f}")
            print(f"Number of data points: {len(strains)}")

    except ValueError as e:
        print(f"Error processing log file: {e}. Please ensure the column names (Step, Pzz, Lz) are present and correctly spelled in your log file.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}") 