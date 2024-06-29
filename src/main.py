# # execution time: 0.0876 seconds 
# import toml 
# import cv2 
# import random
# import matplotlib.pyplot as plt 

# def define_ROIS(toml_fp):
#     with open(toml_fp, 'r') as f: 
#         config = toml.load(f)

#     video_fp = config.get('video', {}).get('filepath')
#     if not video_fp: 
#         raise ValueError("There is no .mp4 filepath defined in config.toml")
#     video = cv2.VideoCapture(video_fp)
#     frames_n = (config.get('video', {}).get('frames'))
#     if frames_n:
#         frames_n = int(frames_n.replace(',', ''))  # remove commas for int()
#     else:
#         frames_n = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
#     random_frame = random.randint(0, int(frames_n) -1)
#     video.set(cv2.CAP_PROP_POS_FRAMES, random_frame)
#     r, f = video.read()
#     if r: 
#         f_rgb = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
#         plt.imshow(f_rgb)
#         plt.axis('off')
#         plt.show()
#     else: 
#         print("could not find frame")

#     video.release()

# toml_fp = 'src/config.toml'
# define_ROIS(toml_fp)
 
# main.py

# import toml
# import cv2
# import random
# import matplotlib.pyplot as plt
# from concurrent.futures import ThreadPoolExecutor
# import numpy as np
# from collections import deque
# import time
# import psutil
# from matplotlib.patches import Polygon

# from rois import select_ROIs

# def load_frame(video, frame_number):
#     video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
#     ret, frame = video.read()
#     if ret:
#         return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     return None

# def find_buffer_s(video, target=0.1):
#     total_mem = psutil.virtual_memory().total
#     frame_w = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
#     frame_h = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
#     frame_s = frame_w * frame_h * 3
#     target_buff_mem = total_mem * target
#     buff_size = int(target_buff_mem / frame_s)
#     return max(1, buff_size)

# def define_ROIS(toml_fp, num_frames_to_show=5):
#     with open(toml_fp, 'r') as f:
#         config = toml.load(f)
#     video_fp = config.get('video', {}).get('filepath')
#     if not video_fp:
#         raise ValueError("There is no .mp4 filepath defined in config.toml")
#     video = cv2.VideoCapture(video_fp)
#     frames_n = config.get('video', {}).get('frames')
#     if frames_n:
#         frames_n = int(frames_n.replace(',', ''))
#     else:
#         frames_n = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
#     buffer_size = find_buffer_s(video)
#     frame_buffer = deque(maxlen=buffer_size)

#     rois = []

#     with ThreadPoolExecutor(max_workers=4) as executor:
#         for _ in range(num_frames_to_show):
#             random_frame = random.randint(0, frames_n - 1)
#             buffered_frame = next((f for f in frame_buffer if f[0] == random_frame), None)
#             if buffered_frame:
#                 frame = buffered_frame[1]
#             else:
#                 frame = load_frame(video, random_frame)
#                 if frame is not None:
#                     frame_buffer.append((random_frame, frame))
#             if frame is not None:
#                 rois = select_ROIs(frame, random_frame, rois)
#             next_frames = [random.randint(0, frames_n - 1) for _ in range(5)]
#             executor.map(lambda x: load_frame(video, x), next_frames)
#     video.release()
#     return rois

# def process_video_with_rois(video_path, rois, frames_to_process=100):
#     video = cv2.VideoCapture(video_path)
#     for _ in range(frames_to_process):
#         ret, frame = video.read()
#         if not ret:
#             break
#         frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         fig, ax = plt.subplots(figsize=(10, 6))
#         ax.imshow(frame_rgb)
#         ax.axis('off')
#         for roi in rois:
#             polygon = Polygon(roi, fill=False, edgecolor='r')
#             ax.add_patch(polygon)
#         plt.show(block=False)
#         plt.pause(0.1)
#         plt.close()
    
#     video.release()

# if __name__ == "__main__":
#     toml_fp = 'src/config.toml'
#     defined_rois = define_ROIS(toml_fp)
#     with open(toml_fp, 'r') as f:
#         config = toml.load(f)
#     process_video_with_rois(config['video']['filepath'], defined_rois)

# import cv2
# import numpy as np
# import toml
# import random
# from collections import deque
# from concurrent.futures import ThreadPoolExecutor
# import psutil
# from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
# from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen
# from PyQt5.QtCore import Qt, QTimer

# from rois import select_rois

# def load_frame(video, frame_number):
#     video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
#     ret, frame = video.read()
#     if ret:
#         return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     return None

# def find_buffer_s(video, target=0.1):
#     total_mem = psutil.virtual_memory().total
#     frame_w = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
#     frame_h = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
#     frame_s = frame_w * frame_h * 3
#     target_buff_mem = total_mem * target
#     buff_size = int(target_buff_mem / frame_s)
#     return max(1, buff_size)

# def define_ROIS(toml_fp, num_frames_to_show=5):
#     with open(toml_fp, 'r') as f:
#         config = toml.load(f)
#     video_fp = config.get('video', {}).get('filepath')
#     if not video_fp:
#         raise ValueError("There is no .mp4 filepath defined in config.toml")
#     video = cv2.VideoCapture(video_fp)
#     frames_n = config.get('video', {}).get('frames')
#     if frames_n:
#         frames_n = int(frames_n.replace(',', ''))
#     else:
#         frames_n = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
#     buffer_size = find_buffer_s(video)
#     frame_buffer = deque(maxlen=buffer_size)

#     rois = []

#     with ThreadPoolExecutor(max_workers=4) as executor:
#         for _ in range(num_frames_to_show):
#             random_frame = random.randint(0, frames_n - 1)
#             buffered_frame = next((f for f in frame_buffer if f[0] == random_frame), None)
#             if buffered_frame:
#                 frame = buffered_frame[1]
#             else:
#                 frame = load_frame(video, random_frame)
#                 if frame is not None:
#                     frame_buffer.append((random_frame, frame))
            
#             if frame is not None:
#                 new_rois = select_rois(frame, random_frame)
#                 rois.extend(new_rois)

#             next_frames = [random.randint(0, frames_n - 1) for _ in range(5)]
#             executor.map(lambda x: load_frame(video, x), next_frames)

#     video.release()
#     return rois

# class VideoPlayer(QMainWindow):
#     def __init__(self, video_path, rois):
#         super().__init__()
#         self.video_path = video_path
#         self.rois = rois
#         self.initUI()

#     def initUI(self):
#         self.setWindowTitle('Video Player with ROIs')
#         self.setGeometry(100, 100, 800, 600)

#         central_widget = QWidget()
#         self.setCentralWidget(central_widget)
#         layout = QVBoxLayout(central_widget)

#         self.image_label = QLabel(self)
#         layout.addWidget(self.image_label)

#         self.video = cv2.VideoCapture(self.video_path)
#         self.timer = QTimer(self)
#         self.timer.timeout.connect(self.update_frame)
#         self.timer.start(30)  # Update every 30 ms

#     def update_frame(self):
#         ret, frame = self.video.read()
#         if ret:
#             frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#             height, width, channel = frame_rgb.shape
#             bytes_per_line = 3 * width
#             q_image = QImage(frame_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
#             pixmap = QPixmap.fromImage(q_image)
            
#             painter = QPainter(pixmap)
#             painter.setRenderHint(QPainter.Antialiasing)
#             painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
            
#             for roi in self.rois:
#                 for i in range(len(roi) - 1):
#                     painter.drawLine(roi[i][0], roi[i][1], roi[i+1][0], roi[i+1][1])
#                 painter.drawLine(roi[-1][0], roi[-1][1], roi[0][0], roi[0][1])
            
#             painter.end()
            
#             self.image_label.setPixmap(pixmap)
#         else:
#             self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)

#     def closeEvent(self, event):
#         self.video.release()

# if __name__ == "__main__":
#     toml_fp = 'src/config.toml'
#     defined_rois = define_ROIS(toml_fp)
#     with open(toml_fp, 'r') as f:
#         config = toml.load(f)
    
#     app = QApplication([])
#     player = VideoPlayer(config['video']['filepath'], defined_rois)
#     player.show()
#     app.exec_()


import cv2
import numpy as np
import json
from rois import select_rois, load_config

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

def main():
    config = load_config('src/config.toml')
    video_path = config['video']['filepath']
    roi_names = list(config['rois']['names'].values())

    video = cv2.VideoCapture(video_path)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

    frame = load_frame(video, 0)
    if frame is None:
        print("Failed to load the first frame")
        return

    rois = select_rois(frame, 0, roi_names)
    
    save_rois(rois, config, 'rois.json')

    video.release()

if __name__ == "__main__":
    main()