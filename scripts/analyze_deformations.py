from ovito.io import import_file
import numpy as np

def analyze_deformation(filename):
    """Analyzes deformation (displacement) from a simulation file using OVITO."""
    try:
        # Load the simulation file
        pipeline = import_file(filename)

        # Get the number of frames
        num_frames = pipeline.source.num_frames
        if num_frames == 0:
            print("Error: No frames found in the simulation file.")
            return

        # Get initial positions from the first frame (index 0)
        print("Reading initial positions from timestep 0...")
        data_initial = pipeline.compute(0)
        initial_positions = data_initial.particles.positions

        print(f"Analyzing deformation (displacement) from {filename}...")
        print("------------------------------------------")
        print("Timestep | Average Displacement Magnitude")
        print("------------------------------------------")

        # Loop through all timesteps starting from the first frame (index 0)
        for frame_index in range(num_frames):
            # Compute the data for the current frame
            data_current = pipeline.compute(frame_index)

            # Get current positions
            current_positions = data_current.particles.positions

            # Ensure both position arrays have the same shape
            if initial_positions.shape != current_positions.shape:
                 print(f"Warning: Shape mismatch at frame {frame_index}. Skipping displacement calculation for this frame.")
                 current_timestep = data_current.attributes.get('Timestep', frame_index)
                 print(f"{current_timestep:<9} | N/A") # Indicate displacement not calculated
                 continue # Skip displacement calculation for this frame

            # Calculate displacement vectors
            displacements = current_positions - initial_positions

            # Calculate the magnitude of displacement for each particle
            displacement_magnitudes = np.linalg.norm(displacements, axis=1)

            # Calculate the average displacement magnitude across all particles
            average_displacement_magnitude = np.mean(displacement_magnitudes)

            # Get the current timestep value (using frame_index as a fallback)
            current_timestep = data_current.attributes.get('Timestep', frame_index)

            print(f"{current_timestep:<9} | {average_displacement_magnitude:<31.6f}")

        print("------------------------------------------")
        print("Deformation analysis complete.")

    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please ensure OVITO Python API is installed (`pip install ovito`) and the file path is correct.")

if __name__ == "__main__":
    # Specify the input file
    input_file = "dump.voro"
    analyze_deformation(input_file) 