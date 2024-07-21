import pandas as pd
import numpy as np
import toml 
import cv2

# Load configuration
config_path = "src/config.toml"

with open(config_path, 'r') as f: 
    contents = toml.load(f)
    bout_marker = contents['markers']['bout_marker']
    video_path = contents['video']['filepath']
    threshold = contents['params']['bout_threshold']  # bout threshold defaults to 1 if it is not specified in toml file 

input_path = 'marker_roi_entries.csv'
data = pd.read_csv(input_path)
video = cv2.VideoCapture(video_path)
fps = video.get(cv2.CAP_PROP_FPS)

# filter for the bout_marker
filtered_data = data[data['Marker'] == bout_marker]


def find_bouts(group):
    bouts = []
    bout = None
    
    for _, i in group.iterrows():
        # checks for unique bouts 
        if bout is None or i['Frame'] != bout['End_Frame'] + 1 or i['ROI'] != bout['ROI']: 
            if bout is not None:
                # finds duration for completed bouts
                duration = (bout['End_Frame'] - bout['Start_Frame'] + 1) / fps
                if duration >= threshold:

                    bouts.append(bout)
            # begins new bout
            bout = {'Start_Frame': i['Frame'], 'End_Frame': i['Frame'], 'ROI': i['ROI']}
        else:
            # continue to current bouts
            bout['End_Frame'] = i['Frame']
    
    if bout is not None:
        duration = (bout['End_Frame'] - bout['Start_Frame'] + 1) / fps # get time

        if duration >= threshold: # apply threshold
            bouts.append(bout)
    
    return pd.DataFrame(bouts)

# Identify bouts for each track
bouts = []
for j, k in filtered_data.groupby('Track'): # there should only be one track (I think)
    all_bouts = find_bouts(k)
    all_bouts['Track'] = j # track_0
    bouts.append(all_bouts)

# compile the bouts
bouts_df = pd.concat(bouts, ignore_index=True)

# find length in s 
bouts_df['Duration'] = (bouts_df['End_Frame'] - bouts_df['Start_Frame'] + 1) / fps

# length (s) 
bouts_df = bouts_df.sort_values(['Track', 'Start_Frame'])


output_path = 'marker_roi_bouts.csv'
bouts_df.to_csv(output_path, index=False)
