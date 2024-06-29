# import matplotlib.pyplot as plt
# from matplotlib.patches import Polygon
# from matplotlib.widgets import PolygonSelector 

# class ROISelection: 

#     def __init__(self, ax, cb):
#         self.ax = ax
#         self.callback = cb
#         self.polygon = PolygonSelector(ax, self.onselect)
#         self.rois = [] 

#     def onselect(self, verts):
#         self.rois.append(verts)
#         self.callback(self.rois)

# def select_ROIs(frame, frame_n, exesting=None):
#     fig, ax = plt.subplots(figsize=(10, 6))
#     ax.imshow(frame)
#     ax.axis('off')
#     ax.set_title(f"Frame {frame_n} - Define ROIs")

#     rois = exesting or []

#     def update(new_rois):
#         nonlocal rois 
#         rois = new_rois 
    
#     roi_selector = ROISelection(ax, update)
#     for i in rois: 
#         polygon = Polygon(i, fill=False, edgecolor='r')
#         ax.add_patch(polygon)
#     plt.show(block=True)
#     plt.close(fig)
#     return rois 

import sys
import numpy as np
import toml
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt5.QtGui import QImage, QPixmap, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QPointF

class ROIGraphicsScene(QGraphicsScene):
    def __init__(self, roi_names, parent=None):
        super().__init__(parent)
        self.roi_names = roi_names
        self.current_roi = []
        self.rois = []
        self.start_point = None
        self.close_threshold = 10  # pixels
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
                np.sqrt((pos.x() - self.start_point.x())**2 + (pos.y() - self.start_point.y())**2) < self.close_threshold)

    def finish_roi(self):
        if len(self.current_roi) > 2:
            self.addLine(self.current_roi[-1].x(), self.current_roi[-1].y(),
                         self.start_point.x(), self.start_point.y(), QPen(Qt.red, 2))
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
        self.setWindowTitle(f'ROI Selector - Frame {self.frame_number}')
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.scene = ROIGraphicsScene(self.roi_names)
        self.view = QGraphicsView(self.scene)
        layout.addWidget(self.view)

        self.info_label = QLabel(f"Define ROI: {self.roi_names[0]}")
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
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

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

if __name__ == "__main__":
    config = load_config('config.toml')
    video_path = config['video']['filepath']
    roi_names = list(config['rois']['names'].values())

    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    frame[:] = (200, 200, 200)  

    rois = select_rois(frame, 0, roi_names)
    save_rois(rois, config)