#!/usr/bin/env python3
"""
Author: Joseph Nguyen
Description: This module defines the ServerFileTransferGUI class, which provides an advanced, UI/UX-friendly
graphical interface for monitoring the RDT 3.0 file transfer process. It displays:
  - A progress bar (updated from "progress.txt")
  - Real-time stats from "stats.txt" (packets sent, acknowledged, retransmitted)
  - Sender and receiver FSM logs (from "sender_fsm.txt" and "receiver_fsm.txt") with color-coded entries
  - A live image preview (updated from "received_file.jpg") using Pillow to decode partial JPEG data
  - A button to plot performance graphs (from "performance_data.csv")
Usage:
    python gui.py
"""

import sys, os, csv, matplotlib.pyplot as plt
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar, QTextEdit, QPushButton, QGroupBox, QHBoxLayout
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSlot, QTimer
from PIL import Image, ImageQt, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

def get_app():
    if QApplication.instance() is None:
        return QApplication(sys.argv)
    else:
        return QApplication.instance()

def load_performance_data():
    data = {}
    try:
        with open("performance_data.csv", "r") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                option = int(row[0])
                loss_rate = int(row[1])
                completion_time = float(row[2])
                throughput = float(row[3])
                retransmissions = int(row[4]) + int(row[5])
                ack_efficiency = float(row[6])
                if option not in data:
                    data[option] = {"loss_rates": [], "completion_time": [], "throughput": [], "retransmissions": [], "ack_efficiency": []}
                data[option]["loss_rates"].append(loss_rate)
                data[option]["completion_time"].append(completion_time)
                data[option]["throughput"].append(throughput)
                data[option]["retransmissions"].append(retransmissions)
                data[option]["ack_efficiency"].append(ack_efficiency)
    except FileNotFoundError:
        print("No performance data file found. Run experiments first.")
    return data

def read_text_file(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return f.readlines()
    return []

def colorize_message(msg):
    if "LOSS" in msg.upper():
        color = "red"
    elif "CORRUPTION" in msg.upper():
        color = "orange"
    elif "SUCCESS" in msg.upper():
        color = "green"
    else:
        color = "black"
    return f'<span style="color:{color};">{msg}</span>'

class ServerFileTransferGUI(QWidget):
    def __init__(self):
        super().__init__()
        # Clear old progress and stats files.
        for fname in ["progress.txt", "stats.txt"]:
            if os.path.exists(fname):
                os.remove(fname)
        self.init_ui()
        # Timer for progress.txt updates
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.read_progress)
        self.progress_timer.start(500)
        # Timer for stats.txt updates
        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self.update_stats)
        self.stats_timer.start(500)
        # Timer for FSM logs updates
        self.fsm_timer = QTimer(self)
        self.fsm_timer.timeout.connect(self.update_fsm_logs)
        self.fsm_timer.start(1000)
        # Timer for image preview updates using Pillow
        self.image_timer = QTimer(self)
        self.image_timer.timeout.connect(self.check_for_image)
        self.image_timer.start(500)
    
    def init_ui(self):
        self.setWindowTitle("RDT 3.0 File Transfer Monitor")
        self.resize(900, 700)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15,15,15,15)
        main_layout.setSpacing(10)

        title_label = QLabel("RDT 3.0 File Transfer Monitor")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        main_layout.addWidget(title_label)

        # Progress and Stats Group
        progress_group = QGroupBox("Transfer Progress and Stats")
        progress_layout = QVBoxLayout()
        self.progress_label = QLabel("Progress: 0%")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setFont(QFont("Arial", 14))
        progress_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        self.stats_label = QLabel("sent:0  acked:0  retrans:0")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stats_label.setFont(QFont("Arial", 12))
        progress_layout.addWidget(self.stats_label)
        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)

        # FSM Logs Group
        fsm_group = QGroupBox("FSM Logs")
        fsm_layout = QHBoxLayout()
        sender_group = QGroupBox("Sender FSM")
        sender_layout = QVBoxLayout()
        self.sender_fsm = QTextEdit()
        self.sender_fsm.setReadOnly(True)
        self.sender_fsm.setFont(QFont("Courier New", 10))
        sender_layout.addWidget(self.sender_fsm)
        sender_group.setLayout(sender_layout)
        fsm_layout.addWidget(sender_group)
        receiver_group = QGroupBox("Receiver FSM")
        receiver_layout = QVBoxLayout()
        self.receiver_fsm = QTextEdit()
        self.receiver_fsm.setReadOnly(True)
        self.receiver_fsm.setFont(QFont("Courier New", 10))
        receiver_layout.addWidget(self.receiver_fsm)
        receiver_group.setLayout(receiver_layout)
        fsm_layout.addWidget(receiver_group)
        fsm_group.setLayout(fsm_layout)
        main_layout.addWidget(fsm_group)

        # Image Preview Group
        image_group = QGroupBox("Live Image Preview")
        image_layout = QVBoxLayout()
        self.image_display = QLabel("Waiting for image data...")
        self.image_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_display.setStyleSheet("border: 1px solid #cccccc;")
        image_layout.addWidget(self.image_display)
        image_group.setLayout(image_layout)
        main_layout.addWidget(image_group)

        # Plot Performance Button
        self.plot_button = QPushButton("Plot Performance Graphs")
        self.plot_button.clicked.connect(self.plot_performance_graphs)
        main_layout.addWidget(self.plot_button)

        self.setLayout(main_layout)
        self.show()
    
    def read_progress(self):
        try:
            with open("progress.txt", "r") as f:
                content = f.read().strip()
                if content:
                    parts = content.split()
                    if len(parts) == 2:
                        current = int(parts[0])
                        total = int(parts[1])
                        percent = int((current / total) * 100) if total > 0 else 0
                        self.progress_bar.setValue(percent)
                        self.progress_label.setText(f"Progress: {percent}%")
        except Exception:
            pass
    
    def update_stats(self):
        try:
            with open("stats.txt", "r") as f:
                line = f.readline().strip()
                if line:
                    self.stats_label.setText(line)
        except Exception:
            pass

    def update_fsm_logs(self):
        sender_lines = read_text_file("sender_fsm.txt")
        receiver_lines = read_text_file("receiver_fsm.txt")
        sender_html = "<br>".join([colorize_message(line.strip()) for line in sender_lines])
        receiver_html = "<br>".join([colorize_message(line.strip()) for line in receiver_lines])
        self.sender_fsm.setHtml(sender_html)
        self.receiver_fsm.setHtml(receiver_html)
    
    def check_for_image(self):
        image_path = "received_file.jpg"
        if os.path.exists(image_path):
            try:
                from PIL import Image, ImageQt
                im = Image.open(image_path)
                im.load()
                qimage = ImageQt.ImageQt(im)
                from PyQt6.QtGui import QPixmap
                pixmap = QPixmap.fromImage(qimage)
                scaled_pixmap = pixmap.scaled(self.image_display.size(), 
                                              Qt.AspectRatioMode.KeepAspectRatio, 
                                              Qt.TransformationMode.SmoothTransformation)
                self.image_display.setPixmap(scaled_pixmap)
            except Exception as e:
                self.image_display.setText("Unable to load image.")
    
    def plot_performance_graphs(self):
        data = load_performance_data()
        if not data:
            return
        fig, axs = plt.subplots(2, 2, figsize=(12, 10))
        for option, metrics in data.items():
            axs[0, 0].plot(metrics["loss_rates"], metrics["completion_time"], marker='o', label=f"Option {option}")
            axs[0, 1].plot(metrics["loss_rates"], metrics["throughput"], marker='o', label=f"Option {option}")
            axs[1, 0].plot(metrics["loss_rates"], metrics["retransmissions"], marker='o', label=f"Option {option}")
            axs[1, 1].plot(metrics["loss_rates"], metrics["ack_efficiency"], marker='o', label=f"Option {option}")
        axs[0, 0].set_title("File Completion Time vs Loss/Error Rate")
        axs[0, 0].set_xlabel("Loss/Error Rate (%)")
        axs[0, 0].set_ylabel("Time (s)")
        axs[0, 0].legend()
        axs[0, 0].grid(True)
        axs[0, 1].set_title("Throughput vs Loss/Error Rate")
        axs[0, 1].set_xlabel("Loss/Error Rate (%)")
        axs[0, 1].set_ylabel("Bytes/s")
        axs[0, 1].legend()
        axs[0, 1].grid(True)
        axs[1, 0].set_title("Retransmissions vs Loss/Error Rate")
        axs[1, 0].set_xlabel("Loss/Error Rate (%)")
        axs[1, 0].set_ylabel("Count")
        axs[1, 0].legend()
        axs[1, 0].grid(True)
        axs[1, 1].setTitle("ACK Efficiency vs Loss/Error Rate")
        axs[1, 1].set_xlabel("Loss/Error Rate (%)")
        axs[1, 1].set_ylabel("Ratio")
        axs[1, 1].legend()
        axs[1, 1].grid(True)
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    app = get_app()
    gui = ServerFileTransferGUI()
    sys.exit(app.exec())