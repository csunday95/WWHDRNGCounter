import socket
import sys
import time
import datetime
import os
from threading import Thread


class TCPGeckoLoggingClient:

    def __init__(self, log_file_dir: str):
        self._log_file_dir = log_file_dir
        self._is_logging = False

    def start_logging(self):
        if self._is_logging:
            return
        self._is_logging = True
        self._logging_thread = Thread(target=self._logging_callback)
        self._logging_thread.start()

    def _logging_callback(self):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.bind(('0.0.0.0', 4405))
        client_socket.settimeout(0.1)
        log_file_name = 'tckgecko_udp_log_{}.log'.format(time.strftime('%y%d%m-%H%M'))
        log_file_name = os.path.join(self._log_file_dir, log_file_name)
        print('Starting UDP log at: {}'.format(log_file_name))
        while self._is_logging:
            try:
                msg, addr = client_socket.recvfrom(1400)
                msg = '{} @ {}: {}\n\n'.format(datetime.datetime.now(), msg, addr)
                print(msg)
                with open(log_file_name, 'a') as log_file:
                    log_file.write(msg)
            except socket.timeout:
                time.sleep(0.1)

    def stop_logging(self):
        if not self._is_logging:
            return
        self._is_logging = False
        self._logging_thread.join()
        self._logging_thread = None
