import os
import math

def split_voro_file(input_file, chunk_size_mb=90):
    # Convert MB to bytes
    chunk_size = chunk_size_mb * 1024 * 1024
    
    # Get file size
    file_size = os.path.getsize(input_file)
    num_chunks = math.ceil(file_size / chunk_size)
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(input_file)
    base_name = os.path.basename(input_file)
    name_without_ext = os.path.splitext(base_name)[0]
    
    # Read and split the file
    with open(input_file, 'rb') as f:
        for i in range(num_chunks):
            output_file = os.path.join(output_dir, f"{name_without_ext}_part{i+1}.voro")
            with open(output_file, 'wb') as out:
                # Read chunk_size bytes
                chunk = f.read(chunk_size)
                out.write(chunk)
            print(f"Created chunk {i+1}/{num_chunks}: {output_file}")

if __name__ == "__main__":
    input_file = "outputs/dump.voro"
    split_voro_file(input_file) 