import toml
import h5py

# def load_skeleton(config_path, frame):
#     with open(config_path, 'r') as f:
#         contents = toml.load(f)
#         h5_path = contents['h5']['filepath']
#     with h5py.File(h5_path, 'r') as h5:
#         nodes = [name.decode() for name in h5['node_names'][:]]
#         positions = h5["tracks"][:, :, :, frame]
#     tracks_n = positions.shape[0]
#     skeleton_data = {}
#     for i in range(tracks_n):
#         tracks = {}
#         for node_idx, node in enumerate(nodes):
#             coords = positions[i, :, node_idx]
#             tracks[f"{node}_x"] = coords[0]
#             tracks[f"{node}_y"] = coords[1]
#             if len(coords) > 2:
#                 tracks[f"{node}_z"] = coords[2]
#         skeleton_data[f"track_{i}"] = tracks
#     return skeleton_data, nodes

def load_skeleton(config_path, frame):
    with open(config_path, 'r') as f:
        contents = toml.load(f)
        h5_path = contents['h5']['filepath']
    
    with h5py.File(h5_path, 'r') as h5:
        nodes = [name.decode() for name in h5['node_names'][:]]
        positions = h5["tracks"][:]
        
        # print(positions.shape)
        # if frame >= positions.shape[3]:
        #     raise IndexError(f"Frame index {frame} out of range. Max frame index is {positions.shape[3] - 1}.") # works with sleap h5s 
        
        # Access the frame correctly
        positions = positions[:, :, :, frame]
    
    tracks_n = positions.shape[0]
    skeleton_data = {}
    for i in range(tracks_n):
        tracks = {}
        for node_idx, node in enumerate(nodes):
            tracks[node] = positions[i, :, node_idx].tolist()  # Adjusted the indexing
        skeleton_data[f"track_{i}"] = tracks
    return skeleton_data, nodes

config_path = 'src/config.toml'
frame = 24817 
skeleton_data, nodes = load_skeleton(config_path, frame)
print(skeleton_data)
