import toml
import h5py 

"""
This script can be used to analyze your markers for a given frame. It is used to load marker data in src/rois.py
A future change might be to use a user defined 'anchor' marker defined in config.toml instead of assuming that a nose marker will suffice. 
"""

def load_skelton(config_path, frame):
    with open(config_path, 'r') as f: 
        contents = toml.load(f)
        h5_path = contents['h5']['filepath']
    with h5py.File(h5_path, 'r') as h5:
        nodes = [name.decode() for name in h5['node_names'][:]]
        positions = h5["tracks"][:, frame, :, :]
    tracks_n = positions.shape[0]
    skeleton_data = {}
    for i in range(tracks_n):
        tracks = {}
        for node_idx, node in enumerate(nodes):
            tracks[node] = positions[i, node_idx, :].tolist()
        skeleton_data[f"track_{i}"] = tracks
    return skeleton_data, nodes

call = load_skelton('src/config.toml', 1)
print(call)
    