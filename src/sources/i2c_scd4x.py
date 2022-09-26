import board
import digitalio
import busio
import canio
import struct
import time
import uprofile
from collections import namedtuple
from adafruit_scd4x import SCD4X

uprofile.enabled = False

debug = False
def print_dbg(some_string, **kwargs):
    if debug:
        return print(some_string, **kwargs)

class DataSource():

    def __init__(self, name, resources, poll_freq=5, send_frame_ids='all') -> None:
        self.bus = resources['i2c']
        self.data_bus = resources['data_bus']
        self.poll_freq = poll_freq
        print_dbg("Listening for i2c messages {} times per second".format(poll_freq))
        self.scd = SCD4X(i2c_bus=self.bus)
        self.scd.start_periodic_measurement() 
    
    async def poll(self):
        uprofile.start_segment('i2c_scd4x', 'poll')
        if self.scd.data_ready:
            data = {
                'temp_cel': self.scd.temperature,
                'rhum_pct': self.scd.relative_humidity,
                'co2_ppm': self.scd.CO2,
            }
            for key, value in data.items():
                # print_dbg("Set {} to {}".format(key, value))
                msg_topic = "data.{}".format(key)
                self.data_bus.pub(msg_topic, value, auto_send=False)
            self.data_bus.send_all()
            print_dbg("Got data this round")
        uprofile.end_segment('i2c_scd4x', 'poll')