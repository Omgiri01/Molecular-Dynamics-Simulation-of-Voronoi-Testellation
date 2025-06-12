import numpy as np
import re

def extract_stress_strain_data(log_file, loading_direction='z'):
    """Extracts stress and strain data from a LAMMPS log file.
    Assumes engineering strain calculated from box dimensions.
    """
    stress_strain_data = []
    header_line_found = False
    header_indices = {}
    initial_Lx, initial_Ly, initial_Lz = None, None, None

    stress_component_key = {'x': 'Pxx', 'y': 'Pyy', 'z': 'Pzz'}[loading_direction] # Key for stress column
    # Need to map LAMMPS output name (e.g., Pxx) to a more standard name if desired, but let's use LAMMPS name for now.

    required_keys = ['Step', stress_component_key, 'Lx', 'Ly', 'Lz']

    try:
        with open(log_file, 'r') as f:
            for line in f:
                line = line.strip()

                # Try to find the header line using regex for more robustness
                if not header_line_found and re.match(r'^\s*Step', line):
                    header = line.split()
                    # Check if all required keys are in the header
                    if all(key in header for key in required_keys):
                        header_line_found = True
                        # Store indices
                        for key in required_keys:
                            header_indices[key] = header.index(key)
                        # Also store indices for all stress components for flexibility
                        stress_keys = ['Pxx', 'Pyy', 'Pzz', 'Pxy', 'Pxz', 'Pyz']
                        for key in stress_keys:
                             if key in header:
                                  header_indices[key] = header.index(key)
                        print("Log file header identified.")
                        continue # Move to next line after finding header

                # If header is found and the line looks like a data line
                # Check if number of values matches the number of headers found (more robust)
                elif header_line_found and len(line.split()) == len(header):
                    values = line.split()
                    try:
                        step = int(values[header_indices['Step']])
                        stress_value = float(values[header_indices[stress_component_key]])
                        Lx = float(values[header_indices['Lx']])
                        Ly = float(values[header_indices['Ly']])
                        Lz = float(values[header_indices['Lz']])

                        if step == 0:
                            initial_Lx, initial_Ly, initial_Lz = Lx, Ly, Lz
                            strain = 0.0
                        else:
                             if loading_direction == 'x':
                                 strain = (Lx - initial_Lx) / initial_Lx
                             elif loading_direction == 'y':
                                 strain = (Ly - initial_Ly) / initial_Ly
                             elif loading_direction == 'z':
                                 strain = (Lz - initial_Lz) / initial_Lz
                             else:
                                 strain = 0.0 # Should not happen with valid loading_direction

                        # Append data: (timestep, strain, stress_in_loading_direction)
                        # Note: LAMMPS pressure/stress is negative of solid mechanics stress
                        stress_strain_data.append((step, strain, -stress_value))

                    except (ValueError, IndexError) as e:
                        # Skip lines that don't contain expected numerical data after header is found
                        # print(f"Warning: Skipping data line due to parsing error: {line} - {e}")
                        pass # Silently skip lines that don't parse correctly

    except FileNotFoundError:
        print(f"Error: Log file not found at {log_file}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while reading the log file: {e}")
        return None

    if not header_line_found:
         print("Error: Could not find the thermo output header line in the log file.")
         print("Please ensure 'thermo_style custom' is configured correctly in your LAMMPS input.") # More specific error message
         return None

    return stress_strain_data

def write_stress_strain_data(data, output_file, loading_direction='z'):
    """Writes extracted stress-strain data to a file."""
    if data is None or not data:
        print("No data to write.")
        return

    try:
        # Determine the appropriate stress label for the header
        stress_label = {'x': 'Pxx', 'y': 'Pyy', 'z': 'Pzz'}[loading_direction]
        # Consider other stress components if needed for shear, etc.
        # For a simple tensile curve, the stress component in the loading direction is key.

        with open(output_file, 'w') as f:
            f.write(f"# Timestep, Strain, Stress ({stress_label})\n") # Header
            for step, strain, stress in data:
                f.write(f"{step}, {strain:.6e}, {stress:.6e}\n")
        print(f"Stress-strain data written to {output_file}")
    except Exception as e:
        print(f"Error writing data to file: {e}")

if __name__ == "__main__":
    log_file = "lammps.log"
    output_file = "stress_strain_data.txt"
    # Assuming uniaxial tension was along the z-axis in lammps_input.in
    loading_direction = 'z' 

    stress_strain_data = extract_stress_strain_data(log_file, loading_direction)

    if stress_strain_data:
        write_stress_strain_data(stress_strain_data, output_file, loading_direction)
    else:
        print("Failed to extract stress-strain data.") 