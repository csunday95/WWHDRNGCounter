from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSignal
from pyqtgraph import PlotWidget, PlotItem, ViewBox
import numpy as np
from circular_float_buffer import CircularFloatBuffer
import time


class CallRatePlotWidget(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._main_layout = QVBoxLayout()
        self._rate_plot_widget = PlotWidget()
        self._rate_plot_item = self._rate_plot_widget.getPlotItem()
        self._rate_plot = self._rate_plot_item.plot()
        self._main_layout.addWidget(self._rate_plot_widget)
        self._buffer = CircularFloatBuffer(2, maxlen=10000)
        self._start_time = time.perf_counter()
        self.setLayout(self._main_layout)

    def append_new_call_data(self, steps_taken, last_second_avg, total_steps):
        time_elapsed = time.perf_counter() - self._start_time
        self._buffer.append([time_elapsed, last_second_avg])
        self._rate_plot.setData(
            self._buffer.get_all_for_channel(0), self._buffer.get_all_for_channel(1)
        )
