from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QTextEdit, QApplication
import sys

class FileTransferGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("File Transfer Progress & FSM Visualization")

        layout = QVBoxLayout()

        # ✅ Transfer Progress
        self.progress_label = QLabel("Transfer Progress:")
        layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # ✅ FSM State Log
        self.fsm_label = QLabel("FSM State Log (Sender & Receiver):")
        layout.addWidget(self.fsm_label)

        self.fsm_log = QTextEdit()
        self.fsm_log.setReadOnly(True)
        layout.addWidget(self.fsm_log)

        self.setLayout(layout)
        self.show()

    def update_progress(self, current, total):
        """Update progress bar."""
        progress_percent = int((current / total) * 100)
        self.progress_bar.setValue(progress_percent)
        self.progress_label.setText(f"Progress: {progress_percent}%")

    def update_fsm_state(self, state):
        """Update FSM log."""
        self.fsm_log.append(state)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = FileTransferGUI()
    sys.exit(app.exec())