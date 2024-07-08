import cv2
import numpy as np
import json
import toml
import h5py
import random
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QGraphicsLineItem
from PyQt5.QtGui import QImage, QPixmap, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QPointF, QLineF
"""
add a function for random frame presentation filtration. this may be the cause of the 1 directional model. 
"""
class RandomFrameGUI(QMainWindow):
    def __init__(self, video_path, rois, roi_names, config_path):
        super().__init__()
        self.video = cv2.VideoCapture(video_path)
        self.rois = rois
        self.roi_names = roi_names
        self.config_path = config_path
        self.total_frames = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
        self.current_frame = None
        self.nose_point = None # change these to toml config w/ anchor 
        self.vector_end = None
        self.mosue_pos = None
        self.vector_data = {}
        self.valid_frames = 0
        self.hypothetical_line = None
        self.vector_placed = False
        self.initUI()

    def initUI(self):
        self.setGeometry(100, 100, 800, 600)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout()

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        layout.addWidget(self.view)

        button_layout = QHBoxLayout()
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.next_frame)
        button_layout.addWidget(self.next_button)

        self.invalid_button = QPushButton("Invalid Frame")
        self.invalid_button.clicked.connect(self.invalid_frame)
        button_layout.addWidget(self.invalid_button)

        layout.addLayout(button_layout)

        self.central_widget.setLayout(layout)

        self.get_valid_frame()

    def get_valid_frame(self):
        while True:
            frame_number = random.randint(0, self.total_frames - 1)
            skeleton_data, _ = load_skeleton(self.config_path, frame_number)
            nose_point = self.get_nose_point(skeleton_data) # change these to toml config w/ anchor
            if nose_point and not self.is_in_roi(nose_point):
                self.current_frame = frame_number
                self.show_frame()
                break

    def get_nose_point(self, skeleton_data): # change these to toml config w/ anchor
        for track in skeleton_data.values():
            if "nose1_x" in track and "nose1_y" in track:
                if track["nose1_x"] is not None and track["nose1_y"] is not None:
                    return (track["nose1_x"], track["nose1_y"])
        return None

    def is_in_roi(self, point):
        for roi in self.rois:
            if cv2.pointPolygonTest(np.array(roi), point, False) >= 0: # other polygon method? 
                return True
        return False

    def show_frame(self):
        self.video.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        ret, frame = self.video.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.display_frame(frame, self.current_frame)
        else:
            print("failed to read frame")

    def display_frame(self, frame, frame_number):
        self.scene.clear()
        height, width, channel = frame.shape
        bytes_in_line = 3 * width
        q_img = QImage(frame.data, width, height, bytes_in_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        self.scene.addPixmap(pixmap)

        # here 
        for roi, name in zip(self.rois, self.roi_names):
            for i in range(len(roi)):
                start = roi[i]
                end = roi[(i + 1) % len(roi)]
                self.scene.addLine(start[0], start[1], end[0], end[1], QPen(Qt.red, 2))

            center = np.mean(roi, axis=0)
            text = self.scene.addText(name)
            text.setFont(QFont("Arial", 12))
            text.setDefaultTextColor(Qt.yellow)
            text.setPos(center[0], center[1])

        # Draw skeleton points and get nose point
        skeleton_data, nodes = load_skeleton(self.config_path, frame_number)
        self.nose_point = None # change these to toml config w/ anchor 
        for track_id, k in skeleton_data.items():
            for j in nodes:
                if f"{j}_x" in k and f"{j}_y" in k:
                    x = k[f"{j}_x"]
                    y = k[f"{j}_y"]
                    if x is not None and y is not None:
                        self.scene.addEllipse(x - 2, y - 2, 4, 4, QPen(Qt.blue), QColor(Qt.blue))
                        if j == "nose1": # change these to toml config w/ anchor 
                            self.nose_point = QPointF(x, y) # change these to toml config w/ anchor 

        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        self.view.setMouseTracking(True)
        self.view.mousePressEvent = self.mousePressEvent
        self.view.mouseMoveEvent = self.mouseMoveEvent

    def mousePressEvent(self, event):
        if self.nose_point and not self.vector_placed: # change these to toml config w/ anchor 
            scene_pos = self.view.mapToScene(event.pos())
            self.vector_end = scene_pos
            self.save_vector_data(self.current_frame)
            self.draw_vector(final=True)
            self.vector_placed = True

    def mouseMoveEvent(self, event):
        if self.nose_point and not self.vector_placed: # change these to toml config w/ anchor 
            self.mosue_pos = self.view.mapToScene(event.pos())
            self.update_hypothetical_vector()

    def draw_vector(self, final=False):
        if self.nose_point: # change these to toml config w/ anchor
            end_point = self.vector_end if final else self.mosue_pos
            if end_point:
                color = Qt.green if final else Qt.yellow
                pen = QPen(color, 2, Qt.SolidLine if final else Qt.DashLine)
                if final:
                    self.scene.addLine(QLineF(self.nose_point, end_point), pen)
                else:
                    if self.hypothetical_line:
                        self.scene.removeItem(self.hypothetical_line)
                    self.hypothetical_line = self.scene.addLine(QLineF(self.nose_point, end_point), pen)

    def update_hypothetical_vector(self):
        if not self.vector_placed:
            self.draw_vector(final=False)

    def save_vector_data(self, frame_number):
        if self.nose_point and self.vector_end:
            self.vector_data[frame_number] = {
                "nose_x": self.nose_point.x(), # change these to toml config w/ anchor
                "nose_y": self.nose_point.y(),
                "vector_end_x": self.vector_end.x(),
                "vector_end_y": self.vector_end.y()
            }

    def next_frame(self):
        if self.vector_placed:
            self.valid_frames += 1
            if self.valid_frames >= 20:
                self.close()
            else:
                self.reset_frame()
        else:
            print("please place a vector")

    def invalid_frame(self):
        self.reset_frame()

    def reset_frame(self):
        self.vector_end = None
        self.mosue_pos = None
        self.hypothetical_line = None
        self.vector_placed = False
        self.get_valid_frame()

    def closeEvent(self, event):
        self.video.release()
        self.to_json()

    def to_json(self):
        with open("vector_data.json", "w") as f:
            json.dump(self.vector_data, f, indent=2)

def load_config(config_path):
    with open(config_path, 'r') as f:
        return toml.load(f)

def load_rois(roi_path):
    with open(roi_path, 'r') as f:
        roi_data = json.load(f)
    return roi_data['data'], list(roi_data['names'].values())

def load_skeleton(config_path, frame):
    with open(config_path, 'r') as f:
        contents = toml.load(f)
        h5_path = contents['h5']['filepath']
    with h5py.File(h5_path, 'r') as h5:
        nodes = [name.decode() for name in h5['node_names'][:]]
        positions = h5["tracks"][:, :, :, frame]
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

def run_gui(config_path, roi_path):
    config = load_config(config_path)
    video_path = config['video']['filepath']
    rois, roi_names = load_rois(roi_path)
    app = QApplication([])
    window = RandomFrameGUI(video_path, rois, roi_names, config_path)
    window.show()
    app.exec_()

if __name__ == "__main__":
    config_path = 'src/config.toml'
    roi_path = 'rois.json'
    run_gui(config_path, roi_path)