import board
import digitalio
import busio
import canio
import struct
import time
import uprofile
from collections import namedtuple
from adafruit_pm25.i2c import PM25_I2C

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
        reset_pin = None
        self.pm25 = PM25_I2C(self.bus, reset_pin) 

    async def poll(self):
        uprofile.start_segment('i2c_pm25', 'poll')
        result = self.pm25.read()
        print_dbg(
            "PM 1.0: %d\tPM2.5: %d\tPM10: %d"
            % (result["pm10 env"], result["pm25 env"], result["pm100 env"])
        )
        data = {
            'pm1_0': result['pm10 env'],
            'pm2_5': result['pm25 env'],
            'pm10': result['pm100 env'],
        }
        for key, value in data.items():
            # print_dbg("Set {} to {}".format(key, value))
            msg_topic = "data.{}".format(key)
            self.data_bus.pub(msg_topic, value, auto_send=False)
        self.data_bus.send_all()
        uprofile.end_segment('i2c_pm25', 'poll')