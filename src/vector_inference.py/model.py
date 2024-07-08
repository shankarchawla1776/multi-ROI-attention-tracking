import json
import numpy as np
import cv2
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Conv2D, MaxPooling2D, UpSampling2D, concatenate, Dropout, Flatten, Dense
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping
import matplotlib.pyplot as plt
import os
import toml

def preprocess_data(json_file, video_path):
    with open(json_file, 'r') as f:
        vector_data = json.load(f)
    
    X = []
    y = [] 

    video = cv2.VideoCapture(video_path)
    
    for frame_number, i in vector_data.items():
        if any(np.isnan(value) for value in i.values()):
            print(f"skip frame {frame_number} because of nans in annotations")
            continue

        frame_number = int(frame_number)
        video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = video.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            start = (int(i['nose_x']), int(i['nose_y']))
            end = (int(i['vector_end_x']), int(i['vector_end_y']))
            cv2.arrowedLine(frame, start, end, (0, 255, 0), 2)
            
            frame = cv2.resize(frame, (224, 224))
            
            direction = np.array(end) - np.array(start)
            direction = direction / np.linalg.norm(direction) # normalization fixes the errors here
            
            X.append(frame)
            y.append(direction)
    
    video.release()
    return np.array(X), np.array(y)

def create_model(input_shape=(224, 224, 3)): # basic u-net setup
    inputs = Input(input_shape)
    
    x = Conv2D(32, 3, activation='relu', padding='same')(inputs)
    x = MaxPooling2D()(x)

    x = Conv2D(64, 3, activation='relu', padding='same')(x)
    x = MaxPooling2D()(x)

    x = Conv2D(128, 3, activation='relu', padding='same')(x)
    x = MaxPooling2D()(x)
    
    x = Flatten()(x)

    x = Dense(128, activation='relu')(x)
    
    outputs = Dense(2, activation='linear')(x) # would it be better to use 3d or 2d? 
    
    model = Model(inputs=inputs, outputs=outputs)
    return model

def train_model(X, y):
    model = create_model()
    model.compile(optimizer=Adam(learning_rate=0.001), loss='mse', metrics=['mae']) # discuss these
    
    checkpoint = ModelCheckpoint('vector_prediction_model.keras', save_best_only=True)
    early_stopping = EarlyStopping(patience=20, restore_best_weights=True) # should not run, but does sometimes
    
    history = model.fit(X, y, validation_split=0.2, epochs=100, batch_size=4, callbacks=[checkpoint, early_stopping])
    return model, history

def main():
    json_file = 'vector_data.json'
    config_path = 'src/config.toml'
    with open (config_path) as f: 
        contents = toml.load(f)
        video_path = contents['video']['filepath']

    X, y = preprocess_data(json_file, video_path)
    print(f"loaded {len(X)} training samples")
    
    if len(X) == 0:
        print("data has no valid samples") # check data
        return
    
    model, history = train_model(X, y)
    
    # standard training history 
    # maybe look for a live training graph method
    plt.figure(figsize=(12, 4))
    plt.subplot(121)
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.title('Model Loss')
    plt.ylabel('Loss')
    plt.xlabel('Epoch')
    plt.legend(['Train', 'Validation'], loc='upper right')
    plt.subplot(122)
    plt.plot(history.history['mae'])
    plt.plot(history.history['val_mae'])
    plt.title('Model MAE')
    plt.ylabel('MAE')
    plt.xlabel('Epoch')
    plt.legend(['Train', 'Validation'], loc='upper right')
    plt.tight_layout()
    plt.savefig('training_history.png')
    plt.close()

if __name__ == "__main__":
    main()