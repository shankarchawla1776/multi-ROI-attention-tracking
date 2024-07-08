import numpy as np
import cv2
import toml
import h5py
from tensorflow.keras.models import load_model
import matplotlib.pyplot as plt
import math 

def load_skeleton(config_path, frame):
    with open(config_path, 'r') as f:
        contents = toml.load(f)
        h5_path = contents['h5']['filepath']
    
    with h5py.File(h5_path, 'r') as h5:
        nodes = [name.decode() for name in h5['node_names'][:]]
        positions = h5["tracks"][:]
        
        print(f"positions shape: {positions.shape}")
        
        # if frame >= positions.shape[3]:

        #     raise IndexError(f"max frame i: {positions.shape[3] - 1}.") # should not have to run for sleap h5s
        
        positions = positions[:, :, :, frame]
    
    tracks_n = positions.shape[0]
    skeleton_data = {}
    for i in range(tracks_n):

        tracks = {}
        for j, node in enumerate(nodes):

            tracks[node] = positions[i, :, j].tolist()
        skeleton_data[f"track_{i}"] = tracks
    return skeleton_data, nodes

def get_nose_coords(config_path, skeleton_data):
    with open(config_path, 'r') as f:
        contents = toml.load(f)
        anchor = contents['markers']['anchor']
    for i in skeleton_data.values():
        # if "nose1" in i:
        #     return i["nose1"][:2]  
        if anchor in i: 
            return i[anchor][:2]
    return None

def set_prediction(model, frame):
    frame_rsz = cv2.resize(frame, (224, 224))
    frame_norm = frame_rsz.astype(np.float32) / 255.0 # ??? 
    frame_b = np.expand_dims(frame_norm, axis=0)
    prediction = model.predict(frame_b)[0]
    return prediction / np.linalg.norm(prediction)  

def draw_vector(image, start_point, direction, magnitude, color=(0, 255, 0), thickness=2):
    
    end_point = tuple(map(int, [
        start_point[0] + direction[0] * magnitude,
        start_point[1] + direction[1] * magnitude
    ])) # implement error handling bc this is where error is thrown if no nose is in the frame. 

    start_point = tuple(map(int, start_point))

    return cv2.arrowedLine(image.copy(), start_point, end_point, color, thickness, tipLength=0.1)

def vector_angle(center, nose_coords, direction):
    # use np.atan2 instead?

    distance = np.array(nose_coords) - np.array(center)
    dot_product = np.dot(distance, direction)
    mag = np.linalg.norm(distance) * np.linalg.norm(direction)
    rad = np.arccos(dot_product / mag)
    deg = np.degrees(rad)
    cross_prod = np.cross(distance, direction)
    if cross_prod < 0:
        deg = 360 - deg
    return deg 

def main(frame_number, config_path, vector_magnitude):
    model = load_model('vector_prediction_model.keras')

    with open(config_path, 'r') as f:
        config = toml.load(f)
        video_path = config['video']['filepath']

    video = cv2.VideoCapture(video_path)
    video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = video.read()
    video.release()

    # if not ret:
    #     print(f"frame {frame_number} is out of range") # should not run for actual implementation
    #     return

    skeleton_data, nodes = load_skeleton(config_path, frame_number)
    nose_coords = get_nose_coords(config_path, skeleton_data)

    # if nose_coords is None:
    #     print(f"No nose coordinates for frame {frame_number}") # FIXME: throws error in draw_vector() instead of here
    #     return

    predicted_dir = set_prediction(model, frame)
    print(f"predicted_dir = {predicted_dir}")

    center = (frame.shape[1] // 2, frame.shape[0] // 2) 
    angle = vector_angle(center, nose_coords, predicted_dir)
    print(f"vector angle (degrees) = {angle:.2f}")

    annotated_frame = draw_vector(frame, nose_coords, predicted_dir, vector_magnitude)

    plt.figure(figsize=(12, 8))
    plt.imshow(cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB))

    # plt.title(f"Frame {frame_number} with vector prediction")
    plt.axis('off')

    # plt.savefig('frame_prediction.png')
    plt.show()

    print("prediction completed")

if __name__ == "__main__":
    config_path = 'src/config.toml'

    with open(config_path, 'r') as f: 
        contents = toml.load(f)
        test_frame = contents['tests']['test_frame']
        magnitude = contents['attention_vectors']['magnitude']

    main(test_frame, config_path, magnitude)
