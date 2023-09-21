import sys
import cv2
import numpy as np
from PyQt5.QtCore import Qt, QTimer, QObject, pyqtSignal, QThread
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog

def detect_objects(image, threshold=0.5):
    cfg_path = 'yolo/yolov3.cfg'
    weight_path = 'yolo/yolov3.weights'
    coco_names_path = 'yolo/coco.names'
    output = np.copy(image)
    
    # Load YOLOv3 weights and configuration
    net = cv2.dnn.readNetFromDarknet(cfg_path, weight_path)
    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)

    # Load COCO class labels (you can customize this for your specific use case)
    classes = open(coco_names_path).read().strip().split('\n')

    # Get height and width of the output
    height, width, _ = output.shape

    # Create a blob from the output and pass it through the network
    blob = cv2.dnn.blobFromImage(output, 1/255.0, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)
    layer_names = net.getUnconnectedOutLayersNames()
    detections = net.forward(layer_names)

    # Loop over the detections and draw rectangles around objects
    for detection in detections:
        for obj in detection:
            scores = obj[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > threshold:  # Adjust the confidence threshold as needed
                center_x = int(obj[0] * width)
                center_y = int(obj[1] * height)
                obj_width = int(obj[2] * width)
                obj_height = int(obj[3] * height)
                x = int(center_x - obj_width / 2)
                y = int(center_y - obj_height / 2)

                # Draw a rectangle around the detected object
                cv2.rectangle(output, (x, y), (x + obj_width, y + obj_height), (0, 255, 0), 2)
                label = f"{classes[class_id]}: {confidence:.2f}"
                cv2.putText(output, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    return output

class Worker(QObject):

    image_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()

    def import_image(self, file_name):
        image = cv2.imread(file_name)
        self.image_signal.emit(image)

    def detect_objects(self, frame):
        frame = detect_objects(frame, threshold=0.5)
        self.image_signal.emit(frame)

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.capture = cv2.VideoCapture(0)
        if not self.capture.isOpened():
            sys.exit("Camera not found!")

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)  # Center-align the image label
        self.image_label.setFixedSize(800, 600)  # Set a fixed size for the image label

        self.capture_button = QPushButton("Take a picture", self)
        self.capture_button.clicked.connect(self.capture_image)
        self.capture_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 10px 20px; border: none; width: 300px;}")

        self.import_button = QPushButton("Import Image", self)
        self.import_button.clicked.connect(self.import_image)
        self.import_button.setStyleSheet("QPushButton { background-color: #008CBA; color: white; padding: 10px 20px; border: none;  width: 300px;}")

        self.width_label = QLabel(self)
        self.height_label = QLabel(self)

        # Styling for height and width labels
        font = QFont()
        font.setPointSize(14)  # Adjust font size as needed
        self.width_label.setFont(font)
        self.height_label.setFont(font)

        # Styling for labels
        label_style = "QLabel { background-color: #333; color: white; padding: 5px; border-radius: 5px; }"
        self.width_label.setStyleSheet(label_style)
        self.height_label.setStyleSheet(label_style)

        button_layout = QVBoxLayout()
        button_layout.addWidget(self.capture_button)
        button_layout.addWidget(self.import_button)

        labels_layout = QHBoxLayout()
        labels_layout.addWidget(self.width_label)
        labels_layout.addWidget(self.height_label)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.image_label)
        main_layout.addLayout(labels_layout)
        main_layout.addLayout(button_layout)
        main_layout.setSpacing(10)  # Reduce the gap between labels

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(3)  # Adjust the timer interval as needed for the frame rate

        self.captured_image = None
        self.is_capturing = False

        self.worker = Worker()
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)
        self.worker.image_signal.connect(self.update_image_label)
        self.worker_thread.start()

        self.setWindowTitle("AutoIntell")
        self.setGeometry(0, 0, 1200, 700)

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
            self.worker.import_image(file_name)
            self.captured_image = self.frame.copy()

    def update_image_label(self, image):
        if image is not None:
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
                # Detect objects and draw rectangles on the frame
                self.worker.detect_objects(frame)
            else:
                self.update_image_label(frame)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    # image = cv2.imread('horse.jpg')
    # print('[image]', image.shape)
    # cv2.imshow('input', image)
    # image = detect_objects(image, threshold=0.9)
    # print('[image]', image.shape)
    # cv2.imshow('output', image)
    # cv2.waitKey(0)

    sys.exit(app.exec_())
