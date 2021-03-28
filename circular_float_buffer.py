
from typing import Union, Type, List
import numpy as np

class CircularFloatBuffer:
    def __init__(self, channel_count: int, maxlen: int = 100):
        """
        An efficient circular buffer with single item appending and
        full buffer getting only.
        """
        self.channel_count = channel_count
        self.maxlen = maxlen
        self.buffer = np.zeros((maxlen, channel_count), dtype=float)
        self.current_size = 0
        self.idx_arr = np.arange(maxlen)
        self.current_index = 0

    def __len__(self) -> int:
        return self.channel_count

    def append(self, value_list: np.ndarray) -> None:
        """
        Add item x to the end of the buffer at the given channel.

        :param value_list: the items to add
        :type value_list: np.ndarray
        """
        self.buffer[self.current_index][:] = value_list
        self.current_index = (self.current_index + 1) % self.maxlen
        if self.current_size < self.maxlen:
            self.current_size += 1
        else:
            self.idx_arr = (self.idx_arr + 1) % self.current_size

    def get_all_for_channel(self, channel: int) -> np.ndarray:
        """

        :param channel: the index of the channel to retrieve the data for
        :type channel: int
        :return: Get the entire buffer in its current state in the correct order, oldest to newest
        :rtype: np.ndarray
        """
        if self.current_size < self.maxlen:
            return self.buffer[:self.current_size][:, channel]
        return self.buffer[self.idx_arr][:, channel]

    def get_all_for_channel_list(self, channel_list: List[int]) -> np.ndarray:
        """

        :param channel_list: the list of indices of the channels to retrieve the data for
        :type channel_list: List[int]
        :return: Get the entire buffer in its current state in the correct order, oldest to newest
        :rtype: np.ndarray
        """
        if self.current_size < self.maxlen:
            return self.buffer[:self.current_index][:, channel_list]
        return self.buffer[self.idx_arr][:, channel_list]

    def get_latest(self, channel: int) -> float:
        """
        :return: Get the most recent entry
        :rtype: float
        """
        if self.current_size < self.maxlen:
            return self.buffer[self.current_index - 1][channel]
        return self.buffer[self.current_index - 1][channel]

    def get_latest_for_all_channels(self) -> np.ndarray:
        if self.current_size < self.maxlen:
            return self.buffer[self.current_index - 1][:]
        return self.buffer[self.current_index - 1][:]

    def clear(self) -> None:
        """reset buffer"""
        self.current_size = 0
        self.buffer.fill(0)
        self.current_index = 0
        self.idx_arr = np.arange(self.maxlen)