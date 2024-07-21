import cv2
import numpy as np
import json
from rois import select_rois, load_config, compute_entries
import toml 
import h5py 
import pandas as pd

def load_frame(video, frame_number):
    video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = video.read()
    if ret:
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return None

def save_rois(rois, config, output_path):
    roi_data = {
        'names': config['rois']['names'],
        'data': [[(int(p.x()), int(p.y())) for p in roi] for roi in rois]
    }
    with open(output_path, 'w') as f:
        json.dump(roi_data, f)
    print(f"ROIs saved to {output_path}")

def load_skeleton(config_path):
    with open(config_path, 'r') as f: 
        contents = toml.load(f)
        h5_path = contents['h5']['filepath']
    
    with h5py.File(h5_path, 'r') as h5:
        nodes = [name.decode() for name in h5['node_names'][:]]
        positions = h5["tracks"][:]
     
    return positions, nodes

def main():
    config = load_config('src/config.toml')
    video_path = config['video']['filepath']
    roi_names = list(config['rois']['names'].values())

    video = cv2.VideoCapture(video_path)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

    frame = load_frame(video, 0)
    if frame is None:
        print("failed to load the first frame")
        return

    rois = select_rois(frame, 0, roi_names)
    
    save_rois(rois, config, 'rois.json')

    skeleton_data, nodes = load_skeleton('src/config.toml')

    df = compute_entries(skeleton_data, rois, roi_names, nodes, total_frames)

    df.to_csv('marker_roi_entries.csv', index=False)
    print("Marker ROI entries saved to marker_roi_entries.csv") # consider also defining an output path in config.toml

    video.release()

if __name__ == "__main__":
    main()
    
