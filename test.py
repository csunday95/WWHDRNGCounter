
from tcp_gecko_client import *
import sys
import struct
import time
from collections import deque


def wichmann_hill_step(state):
    state[0] = (state[0] * 171) % 30269
    state[1] = (state[1] * 172) % 30307
    state[2] = (state[2] * 170) % 30323
    return (state[0] / 30269.0 + state[1] / 30307.0 + state[2] / 30323.0) % 1.0


def forward_search_rng_state(search_state, start_state):
    count = 0
    while search_state != start_state:
        wichmann_hill_step(start_state)
        count += 1
    return count


def main(args):
    last_rng_state = [100, 100, 100]
    client = TCPGeckoClient()
    client.connect('192.168.1.163')
    print(client.get_server_version_hash())
    prev_read_time = 0
    time_deltas = deque(maxlen=5)
    rng_reading_steps = deque(maxlen=5)
    for _ in range(1000):
        new_read_time = time.perf_counter()
        time_delta = new_read_time - prev_read_time
        prev_read_time = new_read_time
        raw_rng_state_data = client.read_memory_range(0x10701BD4, 0x10701BE0)
        if raw_rng_state_data is None:
            continue
        read_rng_state = list(struct.unpack('>III', raw_rng_state_data))
        steps_taken = forward_search_rng_state(read_rng_state, last_rng_state)
        time_deltas.append(time_delta)
        rng_reading_steps.append(steps_taken)
        last_rng_state = read_rng_state
        print('steps in last {}ms: {}'.format(int(time_delta * 1000), steps_taken))
        last_second_avg = sum(rng_reading_steps) / sum(time_deltas)
        print('last second average: ', last_second_avg)
    client.disconnect()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
