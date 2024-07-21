# Multi-ROI Animal Tracking and Attention Analysis
### Usage 

Clone the repository
```zsh
git clone https://github.com/shankarchawla1776/multi-ROI-attention-tracking.git
```
To set up a virtual enviornment, run: 
```zsh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
Configure the toml file:
```toml
[video]
filepath = # str: path to your video
frames = # str: number of frames in your video

[h5]
filepath = # str: path to your sleap h5 file

[rois]
count = # int: number of rois you want to define

[rois.names]
# for each roi:
roi_numbers = roi_name # int = str

```

To run analysis, first run the ROI labeling GUI:

```zsh
python3 src/main.py
```
This will output basic ROI analysis consisting of marker-ROI overlap in the project's main directory as a .csv file. 


