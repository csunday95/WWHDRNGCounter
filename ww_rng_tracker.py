
from typing import Callable
from enum import IntEnum
from tcp_gecko_client import TCPGeckoClient
from threading import Thread
from collections import deque
import datetime
import time
import struct
import os
import csv


class WWRNGTracker:
    RNG_STATE_BASE_ADDR_PAL = 0x10701BD4
    TCP_REQUEST_DELAY = 0.050

    def __init__(self, 
                 client: TCPGeckoClient, 
                 log_file_path: str = 'logs/', 
                 new_data_listener: Callable[[int, float, int], None] = None,
                 rolling_average_size: int = 4):
        self._client = client
        self._log_file_path = log_file_path
        self._rolling_average_size = rolling_average_size
        self._log_file_handle = None
        self._running = False
        self._data_listener = new_data_listener
        self._collection_thread = None

    @staticmethod
    def _wichmann_hill_step(state):
        state[0] = (state[0] * 171) % 30269
        state[1] = (state[1] * 172) % 30307
        state[2] = (state[2] * 170) % 30323
        return (state[0] / 30269.0 + state[1] / 30307.0 + state[2] / 30323.0) % 1.0

    def _forward_search_rng_state(self, search_state, start_state):
        count = 0
        while search_state != start_state and self._running:
            WWRNGTracker._wichmann_hill_step(start_state)
            count += 1
        return count

    def _collect_rng_data_callback(self):
        last_rng_state = [100, 100, 100]
        prev_read_time = 0
        total_ticks = 0
        time_deltas = deque(maxlen=self._rolling_average_size)
        rng_reading_steps = deque(maxlen=self._rolling_average_size)
        if self._log_file_handle is not None:
            log_file_writer = csv.writer(self._log_file_handle)
            log_file_writer.writerow(['Timestamp', 'Runtime', 'Time Delta', 'Steps', 'Avg Steps', 'Total Steps'])
        else:
            log_file_writer = None
        while self._running:
            new_read_time = time.perf_counter()
            time_delta = new_read_time - prev_read_time
            prev_read_time = new_read_time
            raw_rng_state_data = self._client.read_memory_range(
                self.RNG_STATE_BASE_ADDR_PAL, 
                self.RNG_STATE_BASE_ADDR_PAL + 12
            )
            if raw_rng_state_data is None:
                self._data_listener(-1, -1, -1)
                time.sleep(0.1)
                continue
            read_rng_state = list(struct.unpack('>III', raw_rng_state_data))
            steps_taken = self._forward_search_rng_state(read_rng_state, last_rng_state)
            total_ticks += steps_taken
            time_deltas.append(time_delta)
            rng_reading_steps.append(steps_taken)
            last_rng_state = read_rng_state
            last_second_avg = sum(rng_reading_steps) / sum(time_deltas)
            if self._log_file_handle is not None:
                log_file_writer.writerow(
                    [datetime.datetime.now().timestamp(), time.perf_counter(), time_delta, steps_taken, last_second_avg, total_ticks]
                )
            if self._data_listener is not None:
                self._data_listener(steps_taken, last_second_avg, total_ticks)
            time.sleep(self.TCP_REQUEST_DELAY)

    def _open_log_file(self):
        log_file_name = 'WWRNG_log_{}.csv'.format(time.strftime('%Y%m%d-%H%M'))
        if not os.path.isdir(self._log_file_path):
            try:
                os.makedirs(self._log_file_path)
            except OSError:
                return None
        return open(os.path.join(self._log_file_path, log_file_name), 'w')

    def start(self):
        self._running = True
        if self._log_file_path is not None:
            self._log_file_handle = self._open_log_file()
        self._collection_thread = Thread(target=self._collect_rng_data_callback)
        self._collection_thread.start()

    def stop(self):
        self._running = False
        if self._log_file_handle is not None:
            self._log_file_handle.close()
            self._log_file_handle = None
        if self._collection_thread is None:
            return 
        self._collection_thread.join()
        self._collection_thread = None

    
