import numpy as np
import pandas as pd
from tqdm import tqdm

def read_dump_voro(filename):
    """Read dump.voro file and extract trajectory data"""
    data = []
    current_timestep = None
    current_data = []
    box_bounds = None
    atom_ids = []
    
    with open(filename, 'r') as f:
        for line in tqdm(f):
            line = line.strip()
            
            # Check for timestep
            if line.startswith('ITEM: TIMESTEP'):
                if current_timestep is not None and current_data:
                    data.append((current_timestep, current_data, box_bounds, atom_ids))
                current_data = []
                atom_ids = []
                current_timestep = int(next(f))
                continue
            
            # Get box bounds
            if line.startswith('ITEM: BOX BOUNDS'):
                box_bounds = []
                for _ in range(3):
                    bounds = list(map(float, next(f).split()))
                    box_bounds.append(bounds)
                continue
                
            # Skip headers except for ATOMS
            if line.startswith('ITEM:'):
                if not line.startswith('ITEM: ATOMS'):
                    continue
                # Get column indices from ATOMS header
                headers = next(f).strip().split()
                id_idx = headers.index('id') if 'id' in headers else 0
                x_idx = headers.index('x') if 'x' in headers else 1
                y_idx = headers.index('y') if 'y' in headers else 2
                z_idx = headers.index('z') if 'z' in headers else 3
                continue
                
            # Parse data lines
            if current_timestep is not None:
                try:
                    values = list(map(float, line.split()))
                    if len(values) >= 4:  # Ensure we have id and x,y,z coordinates
                        atom_ids.append(int(values[id_idx]))
                        current_data.append([values[x_idx], values[y_idx], values[z_idx]])
                except ValueError:
                    continue
    
    # Add the last timestep
    if current_timestep is not None and current_data:
        data.append((current_timestep, current_data, box_bounds, atom_ids))
    
    return data

def write_trajectory(data, output_file):
    """Write trajectory data to output file"""
    with open(output_file, 'w') as f:
        for timestep, positions, box_bounds, atom_ids in data:
            f.write("ITEM: TIMESTEP\n")
            f.write(f"{timestep}\n")
            f.write("ITEM: NUMBER OF ATOMS\n")
            f.write(f"{len(positions)}\n")
            f.write("ITEM: BOX BOUNDS pp pp pp\n")
            
            # Write box bounds if available, otherwise use default
            if box_bounds:
                for bounds in box_bounds:
                    f.write(f"{bounds[0]:.6f} {bounds[1]:.6f}\n")
            else:
                f.write("0.0 100.0\n")
                f.write("0.0 100.0\n")
                f.write("0.0 100.0\n")
            
            f.write("ITEM: ATOMS id type x y z\n")
            for i, (atom_id, pos) in enumerate(zip(atom_ids, positions), 1):
                f.write(f"{atom_id} 1 {pos[0]:.6f} {pos[1]:.6f} {pos[2]:.6f}\n")

def verify_output(input_file, output_file):
    """Verify the output file matches the input format"""
    print("\nVerifying output file...")
    
    # Read first few lines of both files
    with open(input_file, 'r') as f_in, open(output_file, 'r') as f_out:
        input_lines = [next(f_in) for _ in range(10)]
        output_lines = [next(f_out) for _ in range(10)]
    
    # Compare headers
    if input_lines[0].strip() != output_lines[0].strip():
        print("Warning: Header format mismatch!")
        return False
    
    print("Output file format verification passed!")
    return True

def main():
    input_file = "dump.voro"
    output_file = "dump2.deform"
    
    print("Reading dump.voro file...")
    data = read_dump_voro(input_file)
    
    print("Writing trajectory file...")
    write_trajectory(data, output_file)
    
    print(f"Conversion complete! Trajectory saved to {output_file}")
    
    # Verify the output
    verify_output(input_file, output_file)

if __name__ == "__main__":
    main() 