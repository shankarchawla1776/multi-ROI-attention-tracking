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
Configure the toml file.

To run analysis, first run the ROI labeling GUI:

```zsh
python3 src/main.py
```
This will output basic ROI analysis consisting of marker-ROI overlap in the project's main directory as a .csv file. 


