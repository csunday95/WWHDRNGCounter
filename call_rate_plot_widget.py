
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QHBoxLayout, QLabel, QLineEdit, QCheckBox
from PyQt5.QtCore import pyqtSignal, Qt
from pyqtgraph import PlotWidget, PlotItem, ViewBox
import numpy as np
from circular_float_buffer import CircularFloatBuffer
import time


class CallRatePlotWidget(QWidget):
    WWHD_FPS_ESTIMATE = 30

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._backlog_length = 0
        self._display_as_fps = False
        self._main_layout = QVBoxLayout()
        self._plot_controls_hbox = QHBoxLayout()
        self._plot_controls_hbox.addWidget(QLabel('Show Latest N Seconds:'))
        self._backlog_time_edit = QLineEdit()
        self._backlog_time_edit.textChanged.connect(self._handle_backlog_time_changed)
        self._backlog_time_edit.setFixedWidth(40)
        self._plot_controls_hbox.addWidget(self._backlog_time_edit)
        self._plot_controls_hbox.addWidget(QLabel('Show as Calls/Frame (estimated):'))
        self._fps_display_checkbox = QCheckBox()
        self._fps_display_checkbox.stateChanged.connect(self._handle_fps_display_changed)
        self._plot_controls_hbox.addWidget(self._fps_display_checkbox)
        self._plot_controls_hbox.addStretch()
        self._main_layout.addLayout(self._plot_controls_hbox)
        self._rate_plot_widget = PlotWidget()
        self._rate_plot_item = self._rate_plot_widget.getPlotItem()
        self._rate_plot_item.setTitle('RNG Call Rate')
        self._rate_plot_item.setLabels(left='Call Rate [Calls/sec]', bottom='Time [s]')
        self._rate_plot = self._rate_plot_item.plot(antialias=False)
        self._main_layout.addWidget(self._rate_plot_widget)
        self._total_plot_widget = PlotWidget()
        self._total_plot_item = self._total_plot_widget.getPlotItem()
        self._total_plot_item.setTitle('Total RNG Calls')
        self._total_plot_item.setLabels(left='Total RNG Calls', bottom='Time [s]')
        self._total_plot = self._total_plot_item.plot()
        self._main_layout.addWidget(self._total_plot_widget)
        self._buffer = CircularFloatBuffer(3, maxlen=10000)
        self._start_time = time.perf_counter()
        self.setLayout(self._main_layout)

    def append_new_call_data(self, steps_taken, last_second_avg, total_steps):
        time_elapsed = time.perf_counter() - self._start_time
        self._buffer.append([time_elapsed, last_second_avg, total_steps])
        time_base = self._buffer.get_all_for_channel(0)
        avg_data = self._buffer.get_all_for_channel(1)
        total_data = self._buffer.get_all_for_channel(2)
        if self._display_as_fps:
            avg_data = avg_data / self.WWHD_FPS_ESTIMATE
        if self._backlog_length > 0:
            backlog_index = (time_base > (time_elapsed - self._backlog_length))
            time_base = time_base[backlog_index]
            avg_data = avg_data[backlog_index]
            total_data = total_data[backlog_index]
        self._rate_plot.setData(time_base, avg_data)
        self._total_plot.setData(time_base, total_data)

    def _handle_backlog_time_changed(self, new_text: str):
        if len(new_text) == 0:
            self._backlog_length = 0
        try:
            new_backlog_length = int(new_text)
        except (ValueError, TypeError):
            return
        if new_backlog_length <= 0:
            return
        self._backlog_length = new_backlog_length

    def _handle_fps_display_changed(self, state: int):
        if state == Qt.Unchecked:
            self._display_as_fps = False
            self._rate_plot_item.setLabels(left='Call Rate [Calls/sec]')
        elif state == Qt.Checked:
            self._display_as_fps = True
            self._rate_plot_item.setLabels(left='Call Rate [Calls/frame]')
        
