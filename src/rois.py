import sys
import numpy as np
import toml
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt5.QtGui import QImage, QPixmap, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QPointF
import pandas as pd

class ROIsScene(QGraphicsScene):
    def __init__(self, roi_names, parent=None):
        super().__init__(parent)
        self.roi_names = roi_names
        self.current_roi = []
        self.rois = []
        self.start_point = None
        self.close_thresh = 10  # pixels
        self.current_roi_index = 0

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.current_roi_index < len(self.roi_names):
            pos = event.scenePos()
            if not self.start_point:
                self.start_point = pos
                self.current_roi.append(pos)
            elif self.is_near_start(pos):
                self.finish_roi()
            else:
                self.current_roi.append(pos)
                if len(self.current_roi) > 1:
                    self.addLine(self.current_roi[-2].x(), self.current_roi[-2].y(),
                                 pos.x(), pos.y(), QPen(Qt.red, 2))
            self.update()

    def is_near_start(self, pos):
        return (self.start_point is not None and 
                np.sqrt((pos.x() - self.start_point.x())**2 + (pos.y() - self.start_point.y())**2) < self.close_thresh)

    def finish_roi(self):
        if len(self.current_roi) > 2:
            self.addLine(self.current_roi[-1].x(), self.current_roi[-1].y(),
                         self.start_point.x(), self.start_point.y(), QPen(Qt.red, 2)) # turns off w/ vectors for original rand img
            
            center = np.mean(self.current_roi, axis=0)
            text = self.addText(self.roi_names[self.current_roi_index])
            text.setFont(QFont("Arial", 12))
            text.setDefaultTextColor(Qt.yellow)
            text.setPos(center.x(), center.y())
            
            self.rois.append(self.current_roi)
            self.current_roi = []
            self.start_point = None
            self.current_roi_index += 1

class ROISelector(QMainWindow):
    def __init__(self, frame, frame_number, roi_names):
        super().__init__()
        self.frame = frame
        self.frame_number = frame_number
        self.roi_names = roi_names
        self.initUI()

    def initUI(self):
        self.setWindowTitle(f'ROI Selector - Frame {self.frame_number}') # FIXME: this doesnt update
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.scene = ROIsScene(self.roi_names)
        self.view = QGraphicsView(self.scene)
        layout.addWidget(self.view)

        self.info_label = QLabel(f"Define ROI: {self.roi_names[0]}") # FIXME: this doesnt update 
        layout.addWidget(self.info_label)

        self.done_button = QPushButton('Done', self)
        self.done_button.clicked.connect(self.close)
        layout.addWidget(self.done_button)

        self.showImage()

    def showImage(self):
        height, width, channel = self.frame.shape
        bytes_per_line = 3 * width
        q_img = QImage(self.frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        self.scene.addPixmap(pixmap)
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def resizeEvent(self, event):
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio) # add QOL

def select_rois(frame, frame_number, roi_names):
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    selector = ROISelector(frame, frame_number, roi_names)
    selector.show()
    app.exec_()
    return selector.scene.rois

def load_config(config_path):
    with open(config_path, 'r') as f:
        return toml.load(f)

def save_rois(rois, config):

    print("Saving ROIs:", rois)
    print("ROI names:", config['rois']['names'])

def compute_ROI_point(x, y, polygon):
    n = len(polygon) # will this work for weirder ROIs?, though all reasonable rois are polygons. 
    inside = False
    p1x, p1y = polygon[0]

    for i in range(n + 1):
        p2x, p2y = polygon[i % n] # check here w/ manip
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):

                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x # how to make 2d shape fit in 2d representation of 3d space? 
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside

def compute_entries(skeleton_data, rois, roi_names, nodes, total_frames):
    data = []
    # tracks_n, _, nodes_n, _ = skeleton_data.shape 
    tracks_n, _, nodes_n, frames_n = skeleton_data.shape

    rois_np = [np.array([(int(p.x()), int(p.y())) for p in roi]) for roi in rois]

    # for frame in range(total_frames):  
    for frame in range(min(total_frames, frames_n)):
        # for track in range(tracks_n):
        #     for i, j in enumerate(nodes):
        #         # FIXME: does not work with all frame counts: index i out of bound for axis 3 with size i 
        #         x, y = skeleton_data[track, :, i, frame][:2]  # only use x and y coordinates

        #         for roi_index, roi in enumerate(rois_np):
        #             if compute_ROI_point(x, y, roi):
        #                 data.append({
        #                     'Frame': frame,
        #                     'Track': f'track_{track}',
        #                     'Marker': j,
        #                     'ROI': roi_names[roi_index]
        #                 }) # track? 

        for track in range(tracks_n):
            for i, j in enumerate(nodes):
                if i < nodes_n and frame < frames_n:  # Add this check
                    x, y = skeleton_data[track, :, i, frame][:2]  # only use x and y coordinates

                    for roi_index, roi in enumerate(rois_np):
                        if compute_ROI_point(x, y, roi):
                            data.append({
                                'Frame': frame,
                                'Track': f'track_{track}',
                                'Marker': j,
                                'ROI': roi_names[roi_index]
                            })

    return pd.DataFrame(data)


if __name__ == "__main__":
    config = load_config('config.toml') # for QOL, maybe use better methods than script pathing and search for the config file in dirs
    video_path = config['video']['filepath']
    roi_names = list(config['rois']['names'].values())

    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    frame[:] = (200, 200, 200)  

    rois = select_rois(frame, 0, roi_names)
    save_rois(rois, config)

