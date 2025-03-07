"""
Author: Joseph Nguyen
Description: This module defines the ServerFileTransferGUI class, which provides an advanced, UI/UX-friendly
graphical interface for monitoring the file transfer on the server side. It displays a progress bar (with a percentage),
an FSM log for state messages, and a live image preview area that updates as the file is being received.
"""

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar, QTextEdit
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt, pyqtSlot
import sys

_app = None

def get_app():
    """
    Returns a singleton QApplication instance.
    This ensures that only one QApplication exists per process.
    """
    global _app
    if QApplication.instance() is None:
        _app = QApplication(sys.argv)
    else:
        _app = QApplication.instance()
    return _app

class ServerFileTransferGUI(QWidget):
    """
    The main GUI window for the server.
    Displays the transfer progress, FSM log, and a live preview of the image being received.
    """
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initializes and configures the GUI layout and widgets."""
        self.setWindowTitle("Server File Transfer Monitor")
        self.resize(800, 600)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Title Label
        title_label = QLabel("Server File Transfer Monitor")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Progress Label (shows percentage)
        self.progress_label = QLabel("Progress: 0%")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setFont(QFont("Arial", 12))
        layout.addWidget(self.progress_label)
        
        # Progress Bar widget
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # FSM Log label and text area
        fsm_label = QLabel("FSM Log:")
        fsm_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(fsm_label)
        
        self.fsm_log = QTextEdit()
        self.fsm_log.setReadOnly(True)
        self.fsm_log.setFont(QFont("Courier New", 10))
        layout.addWidget(self.fsm_log)
        
        # Image Display Area (live preview of received file)
        image_label = QLabel("Image Preview:")
        image_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(image_label)
        
        self.image_display = QLabel("Waiting for image data...")
        self.image_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_display.setStyleSheet("border: 1px solid #cccccc;")
        layout.addWidget(self.image_display)
        
        self.setLayout(layout)
        self.show()
    
    @pyqtSlot(int, int)
    def update_progress(self, current, total):
        """
        Updates the progress bar and the percentage label.
        
        Parameters:
            current (int): The number of packets received so far.
            total (int): The total number of packets expected.
        """
        if total > 0:
            progress_percent = int((current / total) * 100)
        else:
            progress_percent = 0
        self.progress_bar.setValue(progress_percent)
        self.progress_label.setText(f"Progress: {progress_percent}%")
    
    @pyqtSlot(str)
    def update_fsm_state(self, state):
        """
        Appends a new state message to the FSM log.
        
        Parameters:
            state (str): The message or state update to log.
        """
        self.fsm_log.append(state)
    
    @pyqtSlot(str)
    def update_image(self, image_path):
        """
        Updates the image preview area with the image at the specified path.
        
        Parameters:
            image_path (str): Path to the image file to display.
        """
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            # Scale the image smoothly while preserving its aspect ratio.
            scaled_pixmap = pixmap.scaled(self.image_display.size(),
                                          Qt.AspectRatioMode.KeepAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation)
            self.image_display.setPixmap(scaled_pixmap)
        else:
            self.image_display.setText("Unable to load image.")

if __name__ == "__main__":
    app = get_app()
    gui = ServerFileTransferGUI()
    sys.exit(app.exec())