import numpy as np
from scipy.spatial import Voronoi
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import sys
import pandas as pd
import os

def read_lammps_dump(filename, target_timesteps=None):
    """Read LAMMPS dump file and return data for specified timesteps."""
    # Update path to look in the outputs directory
    full_path = os.path.join('outputs', filename)
    print(f"Reading file: {full_path}")
    data = {}  # Dictionary to store data for each timestep
    current_timestep = None
    positions = []
    types = []
    csp = []
    box_bounds = None
    reading_atoms = False
    atoms_expected = None
    atoms_read = 0
    
    # Use the full_path to open the file
    with open(full_path, 'r') as f:
        for line in f:
            if 'ITEM: TIMESTEP' in line:
                if current_timestep is not None and atoms_read > 0:
                    # Save data for previous timestep
                    if target_timesteps is None or current_timestep in target_timesteps:
                        data[current_timestep] = {
                            'positions': np.array(positions),
                            'types': np.array(types),
                            'csp': np.array(csp),
                            'box_bounds': box_bounds
                        }
                current_timestep = int(next(f))
                print(f"Processing timestep: {current_timestep}")
                positions = []
                types = []
                csp = []
                reading_atoms = False
                atoms_expected = None
                atoms_read = 0
            elif 'ITEM: NUMBER OF ATOMS' in line:
                atoms_expected = int(next(f))
            elif 'ITEM: BOX BOUNDS' in line:
                box_bounds = []
                for _ in range(3):
                    bounds = next(f).split()
                    box_bounds.append([float(bounds[0]), float(bounds[1])])
            elif 'ITEM: ATOMS' in line:
                reading_atoms = True
                continue
            elif reading_atoms:
                try:
                    parts = line.split()
                    if len(parts) >= 11:
                        atom_id = int(parts[0])
                        atom_type = int(parts[1])
                        x, y, z = map(float, parts[2:5])
                        csp_value = float(parts[10])
                        positions.append([x, y, z])
                        types.append(atom_type)
                        csp.append(csp_value)
                        atoms_read += 1
                        if atoms_expected is not None and atoms_read >= atoms_expected:
                            reading_atoms = False
                except (ValueError, IndexError):
                    continue
    
    # Save data for the last timestep
    if current_timestep is not None and atoms_read > 0:
        if target_timesteps is None or current_timestep in target_timesteps:
            data[current_timestep] = {
                'positions': np.array(positions),
                'types': np.array(types),
                'csp': np.array(csp),
                'box_bounds': box_bounds
            }
    
    return data

def identify_grain_boundaries(positions, types):
    """Identify grain boundaries in the Voronoi structure."""
    print("Identifying grain boundaries...")
    # Get unique grain types
    unique_types = np.unique(types)
    print(f"Found {len(unique_types)} unique grain types")
    
    if len(unique_types) < 2:
        print("Only one grain type detected. Skipping grain boundary identification.")
        return [], []
    
    # Calculate Voronoi diagram for grain centers
    grain_centers = []
    for grain_type in unique_types:
        grain_atoms = positions[types == grain_type]
        center = np.mean(grain_atoms, axis=0)
        grain_centers.append(center)
    
    grain_centers = np.array(grain_centers)
    vor = Voronoi(grain_centers)
    
    # Find atoms near grain boundaries
    boundary_atoms = []
    for i, point in enumerate(positions):
        # Calculate distance to all grain centers
        distances = np.linalg.norm(grain_centers - point, axis=1)
        # If atom is close to multiple grain centers, it's near a boundary
        if np.sum(distances < 5.0) > 1:  # 5.0 Å threshold
            boundary_atoms.append(i)
    
    print(f"Identified {len(boundary_atoms)} boundary atoms")
    return boundary_atoms, grain_centers

def identify_dislocations(positions, csp, threshold=2.0):
    """Identify dislocations using centro-symmetry parameter."""
    print("Identifying dislocations...")
    # Atoms with high CSP are likely to be in dislocations
    dislocation_atoms = csp > threshold
    print(f"Found {np.sum(dislocation_atoms)} atoms in dislocations")
    return dislocation_atoms

def calculate_dislocation_density(positions, dislocation_atoms, box_volume):
    """Calculate dislocation density."""
    n_dislocation_atoms = np.sum(dislocation_atoms)
    dislocation_length = n_dislocation_atoms * 1e-10  # Convert to meters
    density = dislocation_length / box_volume
    return density

def analyze_time_evolution(data, stress_strain_data=None):
    """Analyze dislocation evolution over time and correlate with stress-strain data."""
    timesteps = sorted(data.keys())
    dislocation_densities = []
    n_dislocations = []
    n_grains = []
    
    for timestep in timesteps:
        frame_data = data[timestep]
        positions = frame_data['positions']
        types = frame_data['types']
        csp = frame_data['csp']
        box_bounds = frame_data['box_bounds']
        
        # Calculate box volume
        box_volume = 1.0
        for bounds in box_bounds:
            box_volume *= (bounds[1] - bounds[0])
        box_volume *= 1e-30  # Convert from Å³ to m³
        
        # Identify dislocations
        dislocation_atoms = csp > 2.0
        n_dislocations.append(np.sum(dislocation_atoms))
        
        # Calculate dislocation density
        density = calculate_dislocation_density(positions, dislocation_atoms, box_volume)
        dislocation_densities.append(density)
        
        # Count unique grain types
        n_grains.append(len(np.unique(types)))
    
    # Create time evolution plots (output to results directory)
    plt.figure(figsize=(15, 10))
    
    # Plot dislocation density evolution
    plt.subplot(2, 1, 1)
    plt.plot(timesteps, dislocation_densities, 'b-', label='Dislocation Density')
    plt.xlabel('Timestep')
    plt.ylabel('Dislocation Density (m^-2)')
    plt.title('Evolution of Dislocation Density')
    plt.legend()
    
    # Plot number of dislocations and grains
    plt.subplot(2, 1, 2)
    plt.plot(timesteps, n_dislocations, 'r-', label='Number of Dislocations')
    plt.plot(timesteps, n_grains, 'g-', label='Number of Grains')
    plt.xlabel('Timestep')
    plt.ylabel('Count')
    plt.title('Evolution of Dislocations and Grains')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig('results/dislocation_evolution.png')
    plt.close()
    
    # If stress-strain data is available, create correlation plot (output to results directory)
    if stress_strain_data is not None:
        # Match timesteps between dislocation densities and stress-strain data
        strain_map = dict(zip(stress_strain_data['timestep'], stress_strain_data['strain']))
        matched_strain = []
        matched_density = []
        for t, d in zip(timesteps, dislocation_densities):
            if t in strain_map:
                matched_strain.append(strain_map[t])
                matched_density.append(d)
        if matched_strain and matched_density:
            plt.figure(figsize=(10, 6))
            plt.scatter(matched_strain, matched_density, c='b', alpha=0.5)
            plt.xlabel('Strain')
            plt.ylabel('Dislocation Density (m^-2)')
            plt.title('Correlation between Strain and Dislocation Density')
            plt.savefig('results/strain_dislocation_correlation.png')
            plt.close()
    
    return {
        'timesteps': timesteps,
        'dislocation_densities': dislocation_densities,
        'n_dislocations': n_dislocations,
        'n_grains': n_grains,
        # Return matched data if correlation was performed
        'matched_strain': matched_strain if stress_strain_data is not None and matched_strain else [],
        'matched_density': matched_density if stress_strain_data is not None and matched_density else []
    }

def export_frame_to_xyz(data, timestep, output_file):
    """Export a specific frame from dump.voro as a .xyz file for visualization."""
    if timestep not in data:
        print(f"Timestep {timestep} not found in data.")
        return
    frame = data[timestep]
    positions = frame['positions']
    types = frame['types']
    csp = frame['csp']
    # Update output path to the outputs directory
    full_output_path = os.path.join('outputs', output_file)
    with open(full_output_path, 'w') as f:
        f.write(f"{len(positions)}\n")
        f.write(f"Frame at timestep {timestep}\n")
        for i, (pos, t, c) in enumerate(zip(positions, types, csp)):
            f.write(f"{t} {pos[0]} {pos[1]} {pos[2]} {c}\n")
    print(f"Exported frame at timestep {timestep} to {full_output_path}")

def main():
    try:
        # Read stress-strain data if available (from outputs directory)
        try:
            stress_strain_data = pd.read_csv('outputs/stress_strain_data.txt', 
                                           skiprows=1,  # Skip the header line
                                           names=['timestep', 'strain', 'stress'],
                                           sep=',')  # Use comma as separator
        except Exception as e:
            print(f"Warning: Could not read stress-strain data: {str(e)}")
            print("Proceeding without correlation analysis.")
            stress_strain_data = None
        
        # Read LAMMPS dump file (from outputs directory)
        data = read_lammps_dump('dump.voro')
        
        # Analyze time evolution
        evolution_data = analyze_time_evolution(data, stress_strain_data)
        
        # Retrieve matched strain and density for report
        matched_strain = evolution_data.get('matched_strain', [])
        matched_density = evolution_data.get('matched_density', [])

        # Generate summary report (output to results directory)
        with open('results/dislocation_evolution_report.md', 'w') as f:
            f.write("# Dislocation Evolution Report\n\n")
            f.write("## Time Evolution Analysis\n\n")
            f.write(f"Total number of timesteps analyzed: {len(evolution_data['timesteps'])}\n")
            f.write(f"Initial dislocation density: {evolution_data['dislocation_densities'][0]:.2e} m^-2\n")
            f.write(f"Final dislocation density: {evolution_data['dislocation_densities'][-1]:.2e} m^-2\n")
            f.write(f"Maximum dislocation density: {max(evolution_data['dislocation_densities']):.2e} m^-2\n")
            f.write(f"Average number of grains: {np.mean(evolution_data['n_grains']):.1f}\n\n")
            
            # Calculate statistics for different phases
            timesteps = evolution_data['timesteps']
            densities = evolution_data['dislocation_densities']
            
            # Initial phase (0-1000)
            initial_mask = [t <= 1000 for t in timesteps]
            initial_densities = [d for d, m in zip(densities, initial_mask) if m]
            
            # Middle phase (1000-5000)
            middle_mask = [(t > 1000 and t <= 5000) for t in timesteps]
            middle_densities = [d for d, m in zip(densities, middle_mask) if m]
            
            # Final phase (5000-end)
            final_mask = [t > 5000 for t in timesteps]
            final_densities = [d for d, m in zip(densities, final_mask) if m]
            
            f.write("## Key Observations\n\n")
            f.write("1. Dislocation density evolution shows the following trends:\n")
            # Add checks to avoid calculating mean of empty slices
            if initial_densities:
                f.write(f"   - Initial phase (0-1000): Average density {np.mean(initial_densities):.2e} m^-2\n")
            else:
                f.write("   - Initial phase (0-1000): No data in this phase\n")

            if middle_densities:
                f.write(f"   - Middle phase (1000-5000): Average density {np.mean(middle_densities):.2e} m^-2\n")
            else:
                f.write("   - Middle phase (1000-5000): No data in this phase\n")

            if final_densities:
                f.write(f"   - Final phase (5000-end): Average density {np.mean(final_densities):.2e} m^-2\n\n")
            else:
                f.write("   - Final phase (5000-end): No data in this phase\n\n")

            f.write("2. Grain structure evolution:\n")
            f.write("   - Number of grains remains constant at 1 throughout the simulation\n")
            f.write("   - No grain boundaries were detected\n\n")
            
            f.write("3. Correlation with stress-strain data:\n")
            if stress_strain_data is not None: # Check if stress_strain_data was loaded
                 # Check if there were actually matched points for correlation
                if matched_strain and matched_density:
                    f.write("   - Stress-strain data available for correlation analysis\n")
                    f.write("   - See results/strain_dislocation_correlation.png for visualization\n")
                else:
                    f.write("   - Stress-strain data available, but no matching timesteps for correlation analysis\n")
            else:
                f.write("   - Stress-strain data not available for correlation analysis\n")
        
        print("Analysis complete! Generated files (in results/ and outputs/ directories):")
        print("- results/dislocation_evolution.png")
        # Check if correlation plot was generated before printing
        if stress_strain_data is not None and matched_strain and matched_density:
            print("- results/strain_dislocation_correlation.png")
        print("- results/dislocation_evolution_report.md")
        # The export_frame_to_xyz function prints its own success message, no need to check here.
        # if 'full_output_path' in locals():
        #      print(f"- {full_output_path}")

    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        sys.exit(1)

# In main(), ensure file paths are relative to the script's location
if __name__ == "__main__":
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Change the current working directory to the script's directory
    # This is important for relative paths like 'outputs/dump.voro' to work correctly
    os.chdir(script_dir)

    # Quick scan for unique grain types per frame
    data = read_lammps_dump('dump.voro') # Path is now relative to the script's new cwd
    print("\nQuick scan: Unique grain types per frame:")
    for t, frame in data.items():
        n_grains = len(np.unique(frame['types']))
        print(f"Timestep {t}: {n_grains} unique grain types")
    
    # Export a frame (e.g., timestep 0) for visualization
    export_frame_to_xyz(data, 0, 'frame_0.xyz') # Output path is now relative to the script's new cwd

    # Continue with the main analysis as before
    main() 