# Multi-ROI Animal Pose Tracking and Attention Calcluation


### Usage 

Clone the repository
```zsh
git clone https://github.com/shankarchawla1776/multi-ROI-attention-tracking.git
```

Navigate to ```src/config.toml```. 

Under the ```[video]``` feild, define your video (.mp4) filepath and the number of frames in your video (as a string).

Under the ```[rois]``` field, define the number (integer) of rois you plan to analyze. 

Under the ```[rois.names]``` field, set the number of each roi to the name of this roi. 

Example: 

```toml
[video]
filepath = "test_data/videos/test.mp4"
frames = "54,605"

[rois]
count = 3

[rois.names]
1 = "ButtonL"
2 = "ButtonR"
3 = "Reward"
```

To run analysis:

First, run the ROI labeling GUI:

```zsh
python3 src/main.py
```
This will output some basic ROI analysis in the project's main directory. 

Next, run the attention analysis: 
```zsh
python3 src/tests/test_rois.py
```

### Methods 
##### Head orientation attention vectors
- Mice (lacking a fovea) do not use eye movements in the same fashion as humans. Mice use head movements for orientation towards objects of interest and eyes play a supportive role [Michaiel at al., 2020](https://elifesciences.org/articles/57458). 
- Sound are important for guiding exploratory mechanisms in mice [Snyder et al., 2012](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3273855/).
This evidence supports our to utilize vectors representing mouse attention. The origin of attention vectors will be placed on the nose marker of the animal and reach their terminal point when they colide with enclosure walls. This is a basic implementation. The challenge finding a way to respect 3D space with projections of 2D vectors. 
