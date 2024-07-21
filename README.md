# Multi-ROI Animal Tracking and Attention Analysis

Issues: 
- training data has limited variability (recursive adjustment GUI model)
- Overgitting 
- U-Net complexity 
- training process (probably not)
- the model might not be extracting the most relevant features (figure this out) 

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

[attention_vectors]
human_labled_frames = # int: number of annotated frames you want to train the model with
magnitude = # int: magnitude of model-placed attention vectors (arbitrary) 

[markers]
anchor = # str: marker that will serve as the origin point for attention vectors

[tests]
test_frame = # int: example frame for testing the model

```

To run analysis, first run the ROI labeling GUI:

```zsh
python3 src/main.py
```
This will output basic ROI analysis consisting of marker-ROI overlap in the project's main directory as a .csv file. 

Next, run the attention analysis: 
```zsh
python3 src/tests/test_rois.py
```
This will output frame-by-frame data of head vector orientation in the project's main directory as a .csv file. 

To begin using the U-Net based model for attention tracking, annotate some frames with attention vectors:
```zsh
python3 src/tests/vector_placement.py
```
Then, to train the model, run: 
```zsh
python3 src/vector_inference/model.py
```
Test the model using:
```zsh
python3 src/vector_inference/test_model.py
```

### Methods 

##### Head orientation attention vectors
- Mice (lacking a fovea) do not use eye movements in the same fashion as humans. Mice use head movements for orientation towards objects of interest and eyes play a supportive role [Michaiel at al., 2020](https://elifesciences.org/articles/57458). 
- Sound are important for guiding exploratory mechanisms in mice [Snyder et al., 2012](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3273855/).
This evidence supports the decision to use vectors to represent mouse attention. 