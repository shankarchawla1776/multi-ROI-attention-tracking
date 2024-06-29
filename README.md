# Multi-ROI Animal Pose Tracking and Attention Calcluation

Developed by Shankar Chawla in collaboration with the SOCIAL Neurobiology Lab at Arizona State University. 

### Usage 
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
count = 4

[rois.names]
1 = "ButtonL"
2 = "ButtonR"
3 = "Reward"
4 = "Middle Space"
```

Run the GUI: 
```zsh
python3 src/main.py
```

Define your ROIs and click done. 

### Tests

To check your rois, run the following:
```zsh
python3 src/tests/test_rois.py
```