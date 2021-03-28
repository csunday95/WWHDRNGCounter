
from typing import List

from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QLineEdit, QGridLayout, QWidget, QHBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSignal

import sys
import ipaddress

from tcp_gecko_client import TCPGeckoClient
from ww_rng_tracker import WWRNGTracker
from call_rate_plot_widget import CallRatePlotWidget
from threading import Thread


class RNGCounterMainWindow(QMainWindow):
    _connection_complete_signal = pyqtSignal(bool, str)
    _disconnect_complete_signal = pyqtSignal()
    _new_data_signal = pyqtSignal(int, float, int)

    def __init__(self, client: TCPGeckoClient):
        super().__init__(parent=None)
        self._client = client
        self._tracker = None
        self._connection_thread = None
        self._connected = False
        self._status_bar = self.statusBar()
        self._first_data_plot_drops = 8
        self.setWindowTitle('WWHD RNG Counter')
        self._main_layout = QGridLayout()
        self._ip_entry_hbox = QHBoxLayout()
        self._ip_entry_hbox.addWidget(QLabel('Wii U IP:'))
        self._wii_u_ip_entry = QLineEdit()
        self._ip_entry_hbox.addWidget(self._wii_u_ip_entry)
        self._connect_button = QPushButton('Connect')
        self._connect_button.clicked.connect(self._handle_connect_clicked)
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
        self._connection_complete_signal.connect(self._handle_connection_complete)
        self._disconnect_complete_signal.connect(self._handle_disconnect_complete)
        self._new_data_signal.connect(self._handle_new_data)

    def closeEvent(self, event):
        if self._connection_thread is not None:
            self._connection_thread.join()
        if self._tracker is not None:
            self._tracker.stop()

    def receive_new_data(self, latest, average, total):
        self._new_data_signal.emit(latest, average, total)

    def _handle_new_data(self, latest, average, total):
        if latest < 0:
            self._status_bar.showMessage('Got timeout from TCPGecko... May need to restart console/homebrew')
            return
        self._latest_ticks_display.setText(str(latest))
        self._rolling_avg_ticks_display.setText(f'{average:.2f}')
        self._total_ticks_display.setText(str(total))
        if self._first_data_plot_drops > 0:
            self._first_data_plot_drops -= 1
        else:
            self._call_rate_plot.append_new_call_data(latest, average, total)

    def _handle_connect_clicked(self, _: bool):
        self._connect_button.setDisabled(True)
        if self._connected:
            Thread(target=self._disconect_callback).start()
        else:
            if self._connection_thread is not None:
                return
            self._connection_thread = Thread(target=self._connection_callback)
            self._connection_thread.start()

    def _connection_callback(self):
        connect_ip = self._wii_u_ip_entry.text()
        try:
            ipaddress.IPv4Address(connect_ip)
        except ValueError:
            self._connection_complete_signal.emit(False, 'Must enter a valid IP Address!')
            return
        connect_success = self._client.connect(connect_ip)
        if not connect_success:
            self._connection_complete_signal.emit(False, 'Unable to connect to Wii U!')
            return
        self._tracker = WWRNGTracker(self._client, new_data_listener=self.receive_new_data)
        self._tracker.start()
        self._connection_complete_signal.emit(True, 'Connected! (may take a moment to find current RNG state)')

    def _disconect_callback(self):
        self._tracker.stop()
        self._tracker = None
        self._client.disconnect()
        self._disconnect_complete_signal.emit()

    def _handle_connection_complete(self, success: bool, message: str):
        self._status_bar.showMessage(message, 5000)
        self._connected = success
        if success:
            self._connect_button.setText('Disconnect')
        self._connect_button.setDisabled(False)
        self._connection_thread = None
    
    def _handle_disconnect_complete(self):
        self._connect_button.setText('Connect')
        self._connect_button.setDisabled(False)


def main(args: List[str]):
    client = TCPGeckoClient()
    app = QApplication(args)
    main_window = RNGCounterMainWindow(client)
    main_window.show()
    return_value = app.exec_()
    client.disconnect()
    return return_value


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
