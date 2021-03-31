
__version__ = '0.0.2'

from typing import List, Dict

from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QLineEdit, QGridLayout, QWidget, QHBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSignal

import sys
import ipaddress
import json
import argparse
import os
from threading import Thread

from tcp_gecko_client import TCPGeckoClient
from ww_rng_tracker import WWRNGTracker
from call_rate_plot_widget import CallRatePlotWidget
from tcpgecko_log_client import TCPGeckoLoggingClient

DEFAULT_CONFIG = {'log_file_path': 'logs/', 'saved_ip': '192.168.', 'average_count': 4, 'udp_logging': False}


class RNGCounterMainWindow(QMainWindow):
    _connection_complete_signal = pyqtSignal(bool, str)
    _disconnect_complete_signal = pyqtSignal()
    _new_data_signal = pyqtSignal(int, float, int)

    def __init__(self, client: TCPGeckoClient, config_dict: Dict[str, str]):
        super().__init__(parent=None)
        self._client = client
        self._log_dir = config_dict['log_file_path']
        self._average_count = config_dict['average_count']
        self._tracker = None
        self._connection_thread = None
        self._connected = False
        self._status_bar = self.statusBar()
        self._first_data_plot_drops = 5
        self._updated_config = dict()
        self.setWindowTitle('WWHD RNG Counter - V{}'.format(__version__))
        self._main_layout = QGridLayout()
        self._ip_entry_hbox = QHBoxLayout()
        self._ip_entry_hbox.addWidget(QLabel('Wii U IP:'))
        self._wii_u_ip_entry = QLineEdit(config_dict['saved_ip'])
        self._wii_u_ip_entry.returnPressed.connect(self._handle_wii_u_ip_return_pressed)
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

    def _handle_wii_u_ip_return_pressed(self):
        self._handle_connect_clicked(False)

    def _handle_connect_clicked(self, _: bool):
        self._connect_button.setDisabled(True)
        if self._connected:
            Thread(target=self._disconect_callback).start()
        else:
            if self._connection_thread is not None:
                return
            connect_ip = self._wii_u_ip_entry.text()
            self._connection_thread = Thread(target=self._connection_callback, args=(connect_ip, ))
            self._connection_thread.start()

    def _connection_callback(self, connect_ip: str):
        self._updated_config['saved_ip'] = connect_ip
        try:
            ipaddress.IPv4Address(connect_ip)
        except ValueError:
            self._connection_complete_signal.emit(False, 'Must enter a valid IP Address!')
            return
        connect_success = self._client.connect(connect_ip)
        if not connect_success:
            self._connection_complete_signal.emit(False, 'Unable to connect to Wii U!')
            return
        self._tracker = WWRNGTracker(
            self._client, 
            log_file_path=self._log_dir, 
            new_data_listener=self.receive_new_data,
            rolling_average_size=self._average_count
        )
        self._tracker.start()
        self._connection_complete_signal.emit(True, 'Connected! (may take a moment to find current RNG state)')

    def _disconect_callback(self):
        if self._tracker is not None:
            self._tracker.stop()
            self._tracker = None
        self._connected = False
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

    def get_updated_config(self):
        return self._updated_config


def main(args: List[str]):
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, default='config.json')
    result = vars(parser.parse_args(args))
    config_file_path = result['config']
    config = DEFAULT_CONFIG
    if os.path.isfile(config_file_path):
        with open(config_file_path, 'r') as config_file:
            config.update(json.load(config_file))
    client = TCPGeckoClient()
    if config['udp_logging']:
        logging_client = TCPGeckoLoggingClient(config['log_file_path'])
        logging_client.start_logging()
    app = QApplication(args)
    main_window = RNGCounterMainWindow(client, config)
    main_window.show()
    return_value = app.exec_()
    client.disconnect()
    if config['udp_logging']:
        logging_client.stop_logging()
    config.update(main_window.get_updated_config())
    with open(config_file_path, 'w') as config_file:
        json.dump(config, config_file, indent=2)
    return return_value


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
