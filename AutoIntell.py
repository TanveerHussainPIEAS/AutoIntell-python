import sys
import cv2
import numpy as np
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget, QFileDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.capture = cv2.VideoCapture(0)
        if not self.capture.isOpened():
            sys.exit("Camera not found!")

        self.image_label = QLabel(self)
        self.width_label = QLabel(self)
        self.height_label = QLabel(self)

        # Styling for height and width labels
        font = QFont()
        font.setPointSize(14)  # Adjust font size as needed
        self.width_label.setFont(font)
        self.height_label.setFont(font)

        self.capture_button = QPushButton("Take a picture", self)
        self.capture_button.clicked.connect(self.capture_image)
        self.capture_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 10px 20px; border: none; width: 300px;}")

        self.import_button = QPushButton("Import Image", self)
        self.import_button.clicked.connect(self.import_image)
        self.import_button.setStyleSheet("QPushButton { background-color: #008CBA; color: white; padding: 10px 20px; border: none;  width: 300px;}")

        layout = QVBoxLayout()
        layout.addWidget(self.capture_button)
        layout.addWidget(self.import_button)
        layout.addWidget(self.image_label)
        layout.addWidget(self.width_label)
        layout.addWidget(self.height_label)
        layout.setSpacing(10)  # Reduce the gap between labels

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(3)  # Adjust the timer interval as needed for the frame rate

        self.captured_image = None
        self.is_capturing = False

        self.setWindowTitle("AutoIntell")
        self.setGeometry(100, 100, 1200, 700)

    def capture_image(self):
        if not self.is_capturing:
            self.is_capturing = True
            self.capture_button.setText("Retake Image")
            self.captured_image = self.frame.copy()

            if self.captured_image is not None:
                height, width, _ = self.captured_image.shape
                self.width_label.setText(f"Width: {width}")
                self.height_label.setText(f"Height: {height}")
        else:
            self.is_capturing = False
            self.capture_button.setText("Take a picture")

    def import_image(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Image File", "", "Image Files (*.jpg *.jpeg *.png *.bmp)", options=options)
        if file_name:
            self.captured_image = cv2.imread(file_name)
            height, width, _ = self.captured_image.shape
            self.width_label.setText(f"Width: {width}")
            self.height_label.setText(f"Height: {height}")
            
            # Clear the previous image and set the new pixmap
            self.image_label.clear()
            self.update_image_label(self.captured_image)

    def update_image_label(self, image):
        height, width, channel = image.shape
        bytes_per_line = 3 * width
        q_image = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_image)
        self.image_label.setPixmap(pixmap.scaledToWidth(800, Qt.SmoothTransformation))

    def update_frame(self):
        ret, frame = self.capture.read()
        if ret:
            self.frame = frame
            if not self.is_capturing:
                self.update_image_label(frame)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
