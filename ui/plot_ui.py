from PyQt5.QtWidgets import QWidget, QPushButton, QGridLayout, QHBoxLayout, QVBoxLayout, QApplication, QSlider, QLabel
from PyQt5.QtCore import Qt, QTimer, QDateTime
from PyQt5.QtGui import QPixmap, QPainter
from datetime import datetime
import pyqtgraph as pg
import sys
import numpy as np
import os


class ECGButton(QWidget):
    def __init__(self, channel_number):
        super().__init__()

        self.setStyleSheet("background-color: transparent; border: none;")
        self.channel_number = channel_number

        # Top label - Channel name
        self.label_name = QLabel(f'ch_{channel_number}')
        self.label_name.setStyleSheet("font-size: 12px; color: black; background-color: transparent; border: none;")

        # Bottom label - Dynamic ECG value
        self.label_value = QLabel("0.00")
        self.label_value.setStyleSheet("font-size: 14px; color: black; background-color: transparent; border: none;")

        # Container widget to hold both labels and apply border/background
        self.container = QWidget(self)
        self.container.setStyleSheet("""
            background-color: #ffffff;
            border: 1px solid black;
            border-radius: 10px;
        """)

        # Layout for the container
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        container_layout.addWidget(self.label_name, alignment=Qt.AlignHCenter)
        container_layout.addWidget(self.label_value, alignment=Qt.AlignHCenter)
        self.container.setLayout(container_layout)

        # Outer layout of ECGButton
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)
        outer_layout.addWidget(self.container)
        self.setLayout(outer_layout)

        self.setFixedSize(60, 60)

    def update_button(self, value: float):
        self.label_value.setText(f"{value:.2f}")

        value = max(800, min(65000, value))

        gray = int(255 * (1 - (value - 800) / (65000 - 800)))
        gray_hex = f"{gray:02x}"
        color = f"#{gray_hex}{gray_hex}{gray_hex}"

        # Apply background to the container
        self.container.setStyleSheet(f"background-color: {color}; border-radius: 5px;")

class ECGViewer(QWidget):
    def __init__(self, df):
        super().__init__()
        self.data = None
        self.df = df
        self.total_points = len(self.df)
        self.setWindowTitle("ECG Viewer")

        # Plot state
        self.current_index = 0
        self.selected_channel_data = None
        timestamps = self.df['timestamp'].values
        self.selected_time_data = (timestamps - timestamps[0]) / np.timedelta64(1, 's')  # convert to seconds
        self.is_paused = False

        self.timestamp_label = QLabel()
        self.init_ui()

    def toggle_plot(self):
        self.is_paused = not self.is_paused
        self.toggle_btn.setText("Resume" if self.is_paused else "Pause")

    def reset_plot(self):
        self.plot_widget.clear()
        self.current_index = 0
        print("Plot reset.")

    def seek_to_position(self, value):
        if self.selected_channel_data is not None and len(self.selected_channel_data) > 0:
            max_index = len(self.selected_channel_data)
            new_index = int((value / 100) * max_index)
            self.current_index = new_index
            self.update_plot()
            self.update_all_buttons(new_index)

    def save_current_plot(self):

        # Create pixmap with the same size as the widget
        size = self.plot_widget.size()
        pixmap = QPixmap(size)
        pixmap.fill(Qt.white)

        # Use QPainter to render the widget into the pixmap
        painter = QPainter(pixmap)
        self.plot_widget.render(painter)
        painter.end()

        # Create assets directory if not exists
        save_dir = os.path.join(os.path.dirname(__file__), '..', 'assets')
        os.makedirs(save_dir, exist_ok=True)

        # Timestamped filename
        timestamp = QDateTime.currentDateTime().toString("yyyyMMdd_HHmmss")
        file_path = os.path.join(save_dir, f"ecg_plot_{timestamp}.png")

        # Save to file
        pixmap.save(file_path)

        print(f"Plot saved to {file_path}")

    def init_ui(self):
        main_layout = QHBoxLayout()

        self.timestamp_label = QLabel("Timestamp: ")
        self.timestamp_label.setStyleSheet("color: red; background-color: black; font-size: 12px; padding: 4px;")
        self.timestamp_label.setAlignment(Qt.AlignCenter)

        # --- Top Controls: Toggle + Reset + Slider ---
        button_layout = QHBoxLayout()
        slider_layout = QHBoxLayout()

        self.toggle_btn = QPushButton("Pause")
        self.toggle_btn.clicked.connect(self.toggle_plot)

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self.reset_plot)

        self.exit_btn = QPushButton("Exit")
        self.exit_btn.clicked.connect(QApplication.quit)

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_current_plot)

        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setRange(0, 100)
        self.seek_slider.setStyleSheet("""
            QSlider {
                background: white;
            }

            QSlider::groove:horizontal {
                border: none;
                height: 6px;
                background: black;
                border-radius: 3px;
            }

            QSlider::handle:horizontal {
                background-color: black;
                border: 2px solid white;
                width: 16px;
                height: 16px;
                margin: -6px 0;  /* centers the circle */
                border-radius: 8px;  /* half of width/height to make it a circle */
            }
        """)

        # self.seek_slider.setStyleSheet("background-color: #222;")
        self.seek_slider.valueChanged.connect(self.seek_to_position)

        # Apply consistent style
        for btn in [self.toggle_btn, self.reset_btn, self.exit_btn, self.save_btn]:
            btn.setFixedHeight(40)
            btn.setFixedWidth(60)
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 12px;
                    color: black;
                    background-color: 000000;
                    border: 1px solid #444;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background-color: #3c3c3c;
                }
                QPushButton:pressed {
                    background-color: #003300;
                }
            """)

        button_layout.addWidget(self.toggle_btn)
        button_layout.addWidget(self.reset_btn)
        button_layout.addWidget(self.exit_btn)
        button_layout.addWidget(self.save_btn)

        slider_layout.addWidget(self.seek_slider)

        self.grid_layout = QGridLayout()

        self.buttons = []
        for i in range(40):
            btn = ECGButton(i + 1)
            btn.mousePressEvent = lambda e, ch=i + 1: self.make_plot_callback(ch)()
            row, col = divmod(i, 8)
            self.grid_layout.addWidget(btn, row, col)
            self.buttons.append(btn)

        # --- Left Section (Controls + Buttons) ---
        left_container = QVBoxLayout()

        # --- Top Control Panel Container ---
        left_up_layout = QVBoxLayout()
        left_down_layout = QVBoxLayout()

        left_up_layout.addLayout(button_layout)
        left_up_layout.addSpacing(20)
        left_up_layout.addLayout(slider_layout)

        left_up_layout.addLayout(slider_layout)
        left_down_layout.addLayout(self.grid_layout)

        left_container.addLayout(left_up_layout)
        left_container.addLayout(left_down_layout)

        left_container.addLayout(self.grid_layout)
        # --- Plot Area ---
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel('left', 'ECG Reading')
        self.plot_widget.setLabel('bottom', 'Time (s)')
        self.plot_widget.showGrid(x=True, y=True)

        main_layout.addLayout(left_container, 1)
        self.plot_widget = pg.PlotWidget()
        plot_container = QVBoxLayout()
        plot_container.setSpacing(0)
        plot_container.setContentsMargins(0, 0, 0, 0)
        plot_container.addWidget(self.plot_widget)
        plot_container.addWidget(self.timestamp_label)
        main_layout.addLayout(plot_container, 3)

        self.setLayout(main_layout)
        self.setStyleSheet("background-color: 000000;")

    def make_plot_callback(self, ch_index):
        def callback():
            self.plot_widget.clear()
            self.current_index = 0
            ch_name = f'ch_{ch_index}'
            self.selected_channel_data = self.df[ch_name].values

            y_min = np.min(self.selected_channel_data)
            y_max = np.max(self.selected_channel_data)
            center = (y_min + y_max) / 2
            span = (y_max - y_min) * 1.0  # add padding

            self.plot_widget.setYRange(center - span / 2, center + span / 2)
            self.plot_data_item = self.plot_widget.plot(pen='g')  # green line

            self.timer = QTimer()
            self.timer.timeout.connect(self.update_plot)
            self.timer.start(20)  # 20ms = 50Hz

        return callback

    def update_plot(self):
        if self.is_paused or self.selected_channel_data is None:
            return

        if self.current_index >= len(self.selected_channel_data):
            self.current_index = 0
            return

        window_size = 100
        start_idx = max(0, self.current_index - window_size)
        x = self.selected_time_data[start_idx:self.current_index]
        y = self.selected_channel_data[start_idx:self.current_index]

        self.timestamp_label.setText(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        self.plot_data_item.setData(x, y)
        self.update_all_buttons(self.current_index)

        if self.selected_channel_data is not None and len(self.selected_channel_data) > 0:
            self.seek_slider.blockSignals(True)
            slider_value = min(100, round((self.current_index / len(self.selected_channel_data)) * 100))
            self.seek_slider.setValue(slider_value)
            self.seek_slider.blockSignals(False)

        self.current_index += 1

    def update_all_buttons(self, index: int):
        if index < 0 or index >= len(self.df):
            return

        for i, btn in enumerate(self.buttons):
            value = self.df.iloc[index, i + 1] if (i + 1) < self.df.shape[1] else 0
            btn.update_button(value)


def launch_ui(df):
    app = QApplication(sys.argv)
    viewer = ECGViewer(df)
    viewer.show()
    sys.exit(app.exec_())