
from typing import Callable
from enum import IntEnum
from tcp_gecko_client import TCPGeckoClient
from threading import Thread
from collections import deque
import time
import struct


class WWRNGTracker:
    class RNGConstants(IntEnum):
        RNG_STATE_BASE_ADDR_PAL = 0x10701BD4

    def __init__(self, client: TCPGeckoClient, new_data_listener: Callable[[int, float, int], None]):
        self._client = client
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
        time_deltas = deque(maxlen=5)
        rng_reading_steps = deque(maxlen=5)
        while self._running:
            new_read_time = time.perf_counter()
            time_delta = new_read_time - prev_read_time
            prev_read_time = new_read_time
            raw_rng_state_data = self._client.read_memory_range(0x10701BD4, 0x10701BE0)
            if raw_rng_state_data is None:
                time.sleep(0.1)
                continue
            read_rng_state = list(struct.unpack('>III', raw_rng_state_data))
            steps_taken = self._forward_search_rng_state(read_rng_state, last_rng_state)
            total_ticks += steps_taken
            time_deltas.append(time_delta)
            rng_reading_steps.append(steps_taken)
            last_rng_state = read_rng_state
            last_second_avg = sum(rng_reading_steps) / sum(time_deltas)
            self._data_listener(steps_taken, last_second_avg, total_ticks)

    def start(self):
        self._running = True
        self._collection_thread = Thread(target=self._collect_rng_data_callback)
        self._collection_thread.start()

    def stop(self):
        self._running = False
        if self._collection_thread is None:
            return 
        self._collection_thread.join()
        self._collection_thread = None

    
