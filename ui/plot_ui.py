from PyQt5.QtWidgets import QWidget, QPushButton, QGridLayout, QHBoxLayout, QVBoxLayout, QApplication
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
        # self.selected_time_data = self.df['timestamp'].values
        timestamps = self.df['timestamp'].values
        self.selected_time_data = (timestamps - timestamps[0]) / np.timedelta64(1, 's')  # seconds

        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()

        # --- Left Side: 5x8 Button Grid ---
        self.grid_layout = QGridLayout()
        self.buttons = []
        for i in range(40):
            btn = QPushButton(f'ch_{i+1}')
            btn.clicked.connect(self.make_plot_callback(i+1))
            row, col = divmod(i, 8)
            self.grid_layout.addWidget(btn, row, col)
            self.buttons.append(btn)

        # --- Right Side: Plot Area ---
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel('left', 'ECG Reading')
        self.plot_widget.setLabel('bottom', 'Time (s)')
        self.plot_widget.showGrid(x=True, y=True)

        # --- Combine Layouts ---
        left_container = QVBoxLayout()
        left_container.addLayout(self.grid_layout)
        main_layout.addLayout(left_container, 1)
        main_layout.addWidget(self.plot_widget, 3)

        self.setLayout(main_layout)

    def make_plot_callback(self, ch_index):
        def callback():
            # Clear previous plot
            self.plot_widget.clear()

            # Reset data and state
            self.current_index = 0
            ch_name = f'ch_{ch_index}'
            self.selected_channel_data = self.df[ch_name].values

            y_min = np.min(self.selected_channel_data)
            y_max = np.max(self.selected_channel_data)
            center = (y_min + y_max) / 2
            span = (y_max - y_min) * 1.2  # add padding

            self.plot_widget.setYRange(center - span / 2, center + span / 2)

            self.plot_data_item = self.plot_widget.plot(pen='g')  # green line

            # Timer to simulate real-time plotting at 50Hz
            self.timer = QTimer()
            self.timer.timeout.connect(self.update_plot)
            self.timer.start(20)  # 20 ms = 50 Hz

        return callback

    def update_plot(self):
        # if self.current_index >= len(self.selected_channel_data):
        #     self.timer.stop()
        if self.current_index >= len(self.selected_channel_data):
            self.current_index = 0  # <-- restart from beginning
            return


        # Define sliding window size (500ms = 25 samples at 50Hz)
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
