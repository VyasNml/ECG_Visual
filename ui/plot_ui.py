from PyQt5.QtWidgets import QWidget, QPushButton, QGridLayout, QHBoxLayout, QVBoxLayout, QApplication, QSlider, QLabel
from PyQt5.QtCore import Qt, QTimer
import pyqtgraph as pg
import sys
import numpy as np

class ECGViewer(QWidget):
    def __init__(self, df):
        super().__init__()
        self.df = df
        self.setWindowTitle("ECG Viewer")

        # Plot state
        self.current_index = 0
        self.selected_channel_data = None
        timestamps = self.df['timestamp'].values
        self.selected_time_data = (timestamps - timestamps[0]) / np.timedelta64(1, 's')  # convert to seconds
        self.is_paused = False

        # self.selected_channel_label = QLabel("Selected Channel: None")
        # self.selected_channel_label.setAlignment(Qt.AlignCenter)
        # self.layout.addWidget(self.selected_channel_label)

        self.init_ui()

    def toggle_plot(self):
        self.is_paused = not self.is_paused
        self.toggle_btn.setText("Resume" if self.is_paused else "Pause")

    def reset_plot(self):
        self.plot_widget.clear()
        self.current_index = 0
        print("Plot reset.")

    def init_ui(self):
        main_layout = QHBoxLayout()

        # --- Top Controls: Toggle + Reset + Slider ---
        control_layout = QHBoxLayout()

        self.toggle_btn = QPushButton("Pause")
        self.toggle_btn.clicked.connect(self.toggle_plot)

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self.reset_plot)

        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setRange(0, 100)
        self.seek_slider.setStyleSheet("background-color: #222;")

        # Apply consistent style
        for btn in [self.toggle_btn, self.reset_btn]:
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

        control_layout.addWidget(self.toggle_btn)
        control_layout.addWidget(self.reset_btn)
        control_layout.addWidget(self.seek_slider)

        # --- Channel Button Grid ---
        self.grid_layout = QGridLayout()
        self.buttons = []
        for i in range(40):
            btn = QPushButton(f'ch_{i + 1}')
            btn.setFixedSize(60, 60)
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 12px;
                    color: black;
                    background-color: 000000;
                    border: 1px solid #444;
                    border-radius: 10px;
                }
                QPushButton:hover {
                    background-color: #3c3c3c;
                }
                QPushButton:pressed {
                    background-color: #003300;
                }
            """)
            btn.clicked.connect(self.make_plot_callback(i + 1))
            row, col = divmod(i, 8)
            self.grid_layout.addWidget(btn, row, col)
            self.buttons.append(btn)

        # --- Left Section (Controls + Buttons) ---
        left_container = QVBoxLayout()
        left_container.addLayout(control_layout)
        left_container.addLayout(self.grid_layout)

        # --- Plot Area ---
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel('left', 'ECG Reading')
        self.plot_widget.setLabel('bottom', 'Time (s)')
        self.plot_widget.showGrid(x=True, y=True)

        main_layout.addLayout(left_container, 1)
        main_layout.addWidget(self.plot_widget, 3)

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

        self.plot_data_item.setData(x, y)
        self.current_index += 1


def launch_ui(df):
    app = QApplication(sys.argv)
    viewer = ECGViewer(df)
    viewer.show()
    sys.exit(app.exec_())