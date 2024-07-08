import cv2
import numpy as np
import json
import toml
import h5py
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene
from PyQt5.QtGui import QImage, QPixmap, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QTimer

class PlaybackGUI(QMainWindow):
    def __init__(self, video_path, rois, roi_names, config_path):
        super().__init__()
        self.video = cv2.VideoCapture(video_path)
        self.rois = rois
        self.roi_names = roi_names
        self.config_path = config_path
        self.current_frame = 0
        self.total_frames = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
        self.initUI()

    def initUI(self):
        self.setGeometry(100, 100, 800, 600)
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.setCentralWidget(self.view)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(40)  # 25 FPS

    def update_frame(self):
        frame = self.load_frame()
        if frame is not None:
            self.showImage(frame)
            self.current_frame += 1
        else:
            self.timer.stop()

    def load_frame(self):
        ret, frame = self.video.read()
        if ret:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return None

    def showImage(self, frame):
        self.scene.clear()
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        self.scene.addPixmap(pixmap)

        # Draw ROIs
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

        # Draw skeleton points
        skeleton_data, nodes = load_skeleton(self.config_path, self.current_frame)
        for track_id, tracks in skeleton_data.items():
            for node in nodes:
                if f"{node}_x" in tracks and f"{node}_y" in tracks:
                    x = tracks[f"{node}_x"]
                    y = tracks[f"{node}_y"]
                    if x is not None and y is not None:
                        self.scene.addEllipse(x - 2, y - 2, 4, 4, QPen(Qt.blue), QColor(Qt.blue))

        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def resizeEvent(self, event):
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def closeEvent(self, event):
        self.video.release()

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

def play_video(config_path, roi_path):
    config = load_config(config_path)
    video_path = config['video']['filepath']
    rois, roi_names = load_rois(roi_path)
    app = QApplication([])
    window = PlaybackGUI(video_path, rois, roi_names, config_path)
    window.show()
    app.exec_()

if __name__ == "__main__":
    config_path = 'src/config.toml'
    roi_path = 'rois.json'
    play_video(config_path, roi_path)