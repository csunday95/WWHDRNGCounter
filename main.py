
from typing import List

from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QLineEdit, QGridLayout, QWidget, QHBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSignal

import sys

from tcp_gecko_client import TCPGeckoClient
from ww_rng_tracker import WWRNGTracker
from call_rate_plot_widget import CallRatePlotWidget


class RNGCounterMainWindow(QMainWindow):
    _new_data_signal = pyqtSignal(int, float, int)

    def __init__(self):
        super().__init__(parent=None)
        self.setWindowTitle('WWHD RNG Counter')
        self._main_layout = QGridLayout()
        self._ip_entry_hbox = QHBoxLayout()
        self._ip_entry_hbox.addWidget(QLabel('Wii U IP:'))
        self._wii_u_ip_entry = QLineEdit()
        self._ip_entry_hbox.addWidget(self._wii_u_ip_entry)
        self._connect_button = QPushButton('Connect')
        self._ip_entry_hbox.addWidget(self._connect_button)
        self._main_layout.addLayout(self._ip_entry_hbox, 0, 0)
        self._call_rate_plot = CallRatePlotWidget(self)
        self._main_layout.addWidget(self._call_rate_plot, 1, 0)
        self._info_hbox = QHBoxLayout()
        self._info_hbox.addWidget(QLabel('latest ticks:'))
        self._latest_ticks_display = QLineEdit()
        self._latest_ticks_display.setReadOnly(True)
        self._info_hbox.addWidget(self._latest_ticks_display)
        self._info_hbox.addWidget(QLabel('last second avg:'))
        self._rolling_avg_ticks_display = QLineEdit()
        self._rolling_avg_ticks_display.setReadOnly(True)
        self._info_hbox.addWidget(self._rolling_avg_ticks_display)
        self._info_hbox.addWidget(QLabel('total ticks:'))
        self._total_ticks_display = QLineEdit()
        self._total_ticks_display.setReadOnly(True)
        self._info_hbox.addWidget(self._total_ticks_display)
        self._main_layout.addLayout(self._info_hbox, 2, 0)
        self._central_widget = QWidget()
        self._central_widget.setLayout(self._main_layout)
        self.setCentralWidget(self._central_widget)
        self._new_data_signal.connect(self._handle_new_data)

    def receive_new_data(self, latest, average, total):
        self._new_data_signal.emit(latest, average, total)

    def _handle_new_data(self, latest, average, total):
        self._latest_ticks_display.setText(str(latest))
        self._rolling_avg_ticks_display.setText(f'{average:.2f}')
        self._total_ticks_display.setText(str(total))


def main(args: List[str]):
    client = TCPGeckoClient()
    # if not client.connect('192.168.1.163'):
    #     print('Unable to connect to TCPGecko')
    #     return 1
    # print(client.get_server_version_hash())
    app = QApplication(args)
    main_window = RNGCounterMainWindow()
    tracker = WWRNGTracker(client, main_window.receive_new_data)
    main_window.show()
    # tracker.start()
    return_value = app.exec_()
    tracker.stop()
    return return_value


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
