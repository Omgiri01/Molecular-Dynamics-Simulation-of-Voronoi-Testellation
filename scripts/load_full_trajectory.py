from ovito.io import import_file
from ovito.modifiers import *
import sys

def load_full_trajectory(filename):
    """Loads the full trajectory in OVITO with all timesteps."""
    try:
        # Load the simulation file with all frames
        pipeline = import_file(filename, multiple_frames=True)
        
        # Get the number of frames
        num_frames = pipeline.source.num_frames
        print(f"Total number of frames loaded: {num_frames}")
        
        # Apply any necessary modifiers
        # For example, you might want to add DXA for dislocation analysis
        pipeline.modifiers.append(DislocationAnalysisModifier())
        
        # Compute the first frame to ensure everything is loaded
        pipeline.compute(0)
        
        print("Successfully loaded all frames!")
        print("You can now use OVITO's interface to analyze the full trajectory.")
        print("Use the timeline slider to navigate through all timesteps.")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please ensure OVITO Python API is installed (`pip install ovito`) and the file path is correct.")

if __name__ == "__main__":
    # Specify the input file
    input_file = "../outputs/dump.voro"
    load_full_trajectory(input_file) 