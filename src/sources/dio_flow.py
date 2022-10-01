import board
import countio
import time
import uprofile
from collections import namedtuple

uprofile.enabled = False

debug = False
def print_dbg(some_string, **kwargs):
    if debug:
        return print(some_string, **kwargs)

class DataSource():

    def __init__(self, name, resources, poll_freq=5, pin="", topic="", send_frame_ids='all') -> None:
        self.name = topic;
        print_dbg("We're now known as {}".format(topic))
        edge = countio.Edge.FALL
        count_pin = getattr(board, pin)
        self.counter = countio.Counter(count_pin, edge=edge)
        self.data_bus = resources['data_bus']
        self.poll_freq = poll_freq
        print_dbg("Counting {}s {} times per second".format(edge, poll_freq))
        self.counter.reset();
        self.last_count = time.monotonic()
    
    async def poll(self):
        uprofile.start_segment('dio_counter', 'poll')
        now = time.monotonic()
        rate = self.counter.count * 0.00225 * 60 / (now - self.last_count)
        print_dbg("name: {}, ts: {}, count: {}, rate: {}".format(self.name, now, self.counter.count, rate))
        self.last_count = now
        self.counter.reset();
        # print_dbg("Set {} to {}".format(key, value))
        msg_topic = "data.{}".format(self.name)
        self.data_bus.pub(msg_topic, rate)
        self.data_bus.send_all()
        uprofile.end_segment('dio_counter', 'poll')