import cv2
import numpy as np
import random
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene
from PyQt5.QtGui import QImage, QPixmap, QPen, QColor, QFont
from PyQt5.QtCore import Qt

class ROIVisualizationWindow(QMainWindow):
    def __init__(self, frame, rois, roi_names):
        super().__init__()
        self.frame = frame
        self.rois = rois
        self.roi_names = roi_names
        self.initUI()

    def initUI(self):
        self.setWindowTitle('ROI Visualization Test')
        self.setGeometry(100, 100, 800, 600)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.setCentralWidget(self.view)

        self.showImage()

    def showImage(self):
        height, width, channel = self.frame.shape
        bytes_per_line = 3 * width
        q_img = QImage(self.frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        self.scene.addPixmap(pixmap)

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

        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def resizeEvent(self, event):
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

def load_frame(video, frame_number):
    video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = video.read()
    if ret:
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return None

def load_config(config_path):
    import toml
    with open(config_path, 'r') as f:
        return toml.load(f)

def load_rois(roi_path):
    with open(roi_path, 'r') as f:
        roi_data = json.load(f)
    return roi_data['data'], list(roi_data['names'].values())

def test_roi_visualization(config_path, roi_path):
    config = load_config(config_path)
    video_path = config['video']['filepath']
    
    video = cv2.VideoCapture(video_path)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    
    random_frame_number = random.randint(0, total_frames - 1)
    frame = load_frame(video, random_frame_number)
    
    if frame is None:
        print(f"Failed to load frame {random_frame_number}")
        return

    rois, roi_names = load_rois(roi_path)

    app = QApplication([])
    window = ROIVisualizationWindow(frame, rois, roi_names)
    window.show()
    app.exec_()

    video.release()

if __name__ == "__main__":
    config_path = 'src/config.toml'
    roi_path = 'rois.json'
    test_roi_visualization(config_path, roi_path)