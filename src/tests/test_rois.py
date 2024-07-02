import cv2
import numpy as np
import json
import toml
import h5py
import csv
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene
from PyQt5.QtGui import QImage, QPixmap, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QTimer, QPointF, QLineF

class playback_GUI(QMainWindow):
    def __init__(self, video_path, rois, roi_names, config_path, op_csv):
        super().__init__()
        self.video = cv2.VideoCapture(video_path)
        self.rois = rois
        self.roi_names = roi_names
        self.config_path = config_path

        # change to 1? no frame 0 
        self.current_frame = 0
        self.total_frames = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
        self.prev_np = None
        self.op_csv = op_csv

        self.r_csv = open(self.op_csv, 'w', newline='')
        self.csv_w = csv.writer(self.r_csv)
        self.csv_w.writerow(['Frame', 'Target ROI'])  # Write header
        self.initUI()

    def initUI(self):
        # self.setWindowTitle('Video Player with ROIs and Tracking') # not disp title 
        self.setGeometry(100, 100, 800, 600) # change last 
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.setCentralWidget(self.view)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(40)  # 25 FPS -> 1000ms / 25 = 40

    def update_frame(self):
        frame = self.load_frame()
        if frame is not None:
            self.showImage(frame)
            self.current_frame += 1
        else:
            self.timer.stop()
            self.r_csv.close()

    def load_frame(self):
        ret, frame = self.video.read()
        if ret:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return None

    def get_nose_marker(self, skeleton_data):
        for i, j in skeleton_data.items():
            if "nose1_x" in j and "nose1_y" in j:

                return QPointF(j["nose1_x"], j["nose1_y"])
        return None

    def get_roi_centers(self):
        roi_centers = []
        for roi in self.rois:
            center = np.mean(roi, axis=0)
            roi_centers.append(QPointF(center[0], center[1]))
        return roi_centers

    def get_target_roi(self, nose_point, movement_direction):
        roi_centers = self.get_roi_centers()
        best_alignment = -1
        target_idx = -1

        for i, j in enumerate(roi_centers):
            roi_direction = QPointF(j.x() - nose_point.x(), j.y() - nose_point.y())
            roi_dir_len = (roi_direction.x()**2 + roi_direction.y()**2)**0.5 # assumption
            if roi_dir_len > 0:
                roi_direction = QPointF(roi_direction.x() / roi_dir_len, roi_direction.y() / roi_dir_len)

                alignment = roi_direction.x() * movement_direction.x() + roi_direction.y() * movement_direction.y() # in dosc

                if alignment > best_alignment:
                    best_alignment = alignment
                    target_idx = i

        return target_idx, roi_centers[target_idx] if target_idx != -1 else None

    def intersection_p(self, line1, line2): # does processing speed scale w/ fps -> CPU %? 
        x1, y1, x2, y2 = line1
        x3, y3, x4, y4 = line2
        
        det = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if det == 0:
            return None  # if same slp/parll
        
        """
        check math here. 
        it can also be modified to avoid instant-switching bouts 
        also look for ways to process the geomtetric data faster so larger videos can be processed. 
        """
        
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / det

        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / det 
        
        if 0 <= t <= 1 and 0 <= u <= 1:
            x = x1 + t * (x2 - x1)
            y = y1 + t * (y2 - y1)
            return QPointF(x, y)
        
        return None # default

    def find_intersection(self, start_point, direction, rois):
        max_length = 1000  # maximum length of the v_1, might need to define lengths in toml for this to work. consider making a length calulator as part of the initial GUI. 
        end_point = QPointF(start_point.x() + direction.x() * max_length,
                            start_point.y() + direction.y() * max_length)
        vector_line = (start_point.x(), start_point.y(), end_point.x(), end_point.y())

        closest = None
        min_d = float('inf')

        for j in rois:
            for i in range(len(j)):

                roi_line = (j[i][0], j[i][1], j[(i + 1) % len(j)][0], j[(i + 1) % len(j)][1]) # per algo, consider using alt 

                intersection = self.intersection_p(vector_line, roi_line)
                if intersection:
                    distance = QLineF(start_point, intersection).length()
                    if distance < min_d:
                        min_d = distance
                        closest = intersection

        return closest

    def showImage(self, frame):
        self.scene.clear()
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        self.scene.addPixmap(pixmap)

        for roi, name in zip(self.rois, self.roi_names):
            for i in range(len(roi)):
                start = roi[i]
                end = roi[(i + 1) % len(roi)] # per same algo 
                self.scene.addLine(start[0], start[1], end[0], end[1], QPen(Qt.red, 2))

            center = np.mean(roi, axis=0)

            text = self.scene.addText(name)
            text.setFont(QFont("Arial", 12))
            text.setDefaultTextColor(Qt.yellow)
            text.setPos(center[0], center[1])

        skeleton_data, nodes = load_skeleton(self.config_path, self.current_frame)
        for track_id, tracks in skeleton_data.items():
            for node in nodes:
                if f"{node}_x" in tracks and f"{node}_y" in tracks:
                    x = tracks[f"{node}_x"]
                    y = tracks[f"{node}_y"]
                    if x is not None and y is not None:
                        # other plot methods might be faster
                        self.scene.addEllipse(x - 2, y - 2, 4, 4, QPen(Qt.blue), QColor(Qt.blue))

        # draw vector from nose to ROI intersection (or center)
        nose_point = self.get_nose_marker(skeleton_data)
        if nose_point: # filter by frames w/ nose markers
            if self.prev_np:
                # take from frame_idx - 1 
                movement_direction = QPointF(nose_point.x() - self.prev_np.x(), nose_point.y() - self.prev_np.y())
                movement_length = (movement_direction.x()**2 + movement_direction.y()**2)**0.5
                if movement_length > 0:
                    # ignore bad frames, maybe consider negating pauses (grooming) for less random lockons. 
                    movement_direction = QPointF(movement_direction.x() / movement_length, movement_direction.y() / movement_length)
                    target_idx, target_roi_center = self.get_target_roi(nose_point, movement_direction)
                    if target_roi_center:
                        # try using center
                        direction = QPointF(target_roi_center.x() - nose_point.x(), target_roi_center.y() - nose_point.y())
                        direction_length = (direction.x()**2 + direction.y()**2)**0.5
                        if direction_length > 0:
                            direction = QPointF(direction.x() / direction_length, direction.y() / direction_length)
                            intersection = self.find_intersection(nose_point, direction, self.rois)
                            if intersection:
                                self.scene.addLine(QLineF(nose_point, intersection), QPen(Qt.green, 2))
                                # Record the target ROI for this frame
                                self.csv_w.writerow([self.current_frame, self.roi_names[target_idx]])
                                # should not run for three test groups of mice
                            else:
                                self.csv_w.writerow([self.current_frame, 'No intersection'])
                        else:
                            self.csv_w.writerow([self.current_frame, 'Zero direction length'])
                    else:
                        self.csv_w.writerow([self.current_frame, 'No target ROI'])
                else:
                    self.csv_w.writerow([self.current_frame, 'No movement'])
            else:
                self.csv_w.writerow([self.current_frame, 'First frame'])
            self.prev_np = nose_point
        else:
            self.csv_w.writerow([self.current_frame, 'No nose point'])

        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def resizeEvent(self, event):
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def closeEvent(self, event):
        self.video.release()
        self.r_csv.close()

def load_config(config_path):
    with open(config_path, 'r') as f:
        return toml.load(f)

def load_rois(roi_path):
    with open(roi_path, 'r') as f:
        roi_data = json.load(f)
    return roi_data['data'], list(roi_data['names'].values())

def load_skeleton(config_path, frame): # function from sleap_h5s.py
    with open(config_path, 'r') as f: 
        contents = toml.load(f)
        h5_path = contents['h5']['filepath']
    with h5py.File(h5_path, 'r') as h5:
        nodes = [name.decode() for name in h5['node_names'][:]]
        positions = h5["tracks"][:, :, :, frame] # structure might vary
    tracks_n = positions.shape[0]
    skeleton_data = {}
    for i in range(tracks_n):
        tracks = {}
        for node_idx, node in enumerate(nodes):
            coords = positions[i, :, node_idx]
            tracks[f"{node}_x"] = coords[0]
            tracks[f"{node}_y"] = coords[1]
            if len(coords) > 2:
                tracks[f"{node}_z"] = coords[2]
        skeleton_data[f"track_{i}"] = tracks
    return skeleton_data, nodes
    
def play_video(config_path, roi_path):
    config = load_config(config_path)
    video_path = config['video']['filepath']
    rois, roi_names = load_rois(roi_path)

    app = QApplication([])
    window = playback_GUI(video_path, rois, roi_names, config_path)
    window.show()
    app.exec_()

def play_video(config_path, roi_path, op_csv):
    config = load_config(config_path)
    video_path = config['video']['filepath']
    rois, roi_names = load_rois(roi_path)
    app = QApplication([])
    window = playback_GUI(video_path, rois, roi_names, config_path, op_csv)
    window.show()
    app.exec_()

if __name__ == "__main__":
    config_path = 'src/config.toml'
    roi_path = 'rois.json'
    op_csv = 'roi_data.csv'  
    play_video(config_path, roi_path, op_csv)