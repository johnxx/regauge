import board
import digitalio
import busio
import canio
import struct
import time
from collections import namedtuple

Frame = namedtuple("Frame", ("struct", "fields"))

debug = False
def print_dbg(some_string, **kwargs):
    if debug:
        return print(some_string, **kwargs)

class DataSource():

    frame_defs = {
        0x600: Frame("<HBbHH", ['eng_rpm', 'tps_pct', 'iat_cel', 'map_kpa', 'injpw_ms']),
        0x602: Frame("<HBBBBH", ['vss_kmh', 'baro_kpa', 'oiltemp_cel', 'oilpres_psi', 'fuelpres_kpa', 'clt_cel']),
        0x603: Frame("<BBBBHH", ['ignadv_deg', 'igndwell_ms', 'o2_lambda', 'egocor_pct', 'egt1_cel', 'egt2_cel']),
        0x604: Frame("<BbHHBB", ['gear_num', 'ecutemp_cel', 'batt_volts', 'cel_bits', 'flags_bits', 'ethcont_pct']),
        0x900: Frame("<BBBBBBBB", ['cpu_pct', 'mem_pct', 'cput_cel', 'f4', 'f5', 'f6', 'f7', 'f8']),
    }

    magic = bytearray([0x44, 0x33, 0x22, 0x11])

    match = canio.Match(0x600, 0x100)

    def __init__(self, name, resources, poll_freq=5, send_frame_ids='all') -> None:
        self.bus = resources['can']
        self.data_bus = resources['data_bus']
        self.poll_freq = poll_freq
        print_dbg("Listening for CANbus messages {} times per second".format(poll_freq))
        self.listener = self.bus.listen(matches=[self.match], timeout=1)

    def unpack_frame(self, frame):
        # Fish the frame ID out of the 4 bytes after the header
        #id = int.from_bytes(frame[4:8], 'little')
        id = frame.id
        # We saw a frame we can't decode
        if id not in self.frame_defs:
            print_dbg(id, end='')
            return None, None
        # Unpack values from the struct
        #values = struct.unpack(self.frame_defs[id].struct, frame[8:])
        values = struct.unpack(self.frame_defs[id].struct, frame.data)
        # Make a dict from field names and frame values
        return id, dict(zip(self.frame_defs[id].fields, values))
    
    async def poll(self):
        if self.listener.in_waiting() == 0:
            print_dbg("No messages waiting, returned early")
            return
        print_dbg("messages waiting: {}".format(self.listener.in_waiting()))
        message = self.listener.receive()
        if message is None:
            print_dbg("No messsage received within timeout")
            return
     
        if len(message.data) != 8:
            print_dbg(f"Unusual message length {len(message.data)}")
            return
        
        id, frame_data = self.unpack_frame(message)
        print_dbg("Got frame with id: {}".format(id))

        if frame_data:
            for key, value in frame_data.items():
                print_dbg("Set {} to {}".format(key, value))
                msg_topic = "data.{}".format(key)
                self.data_bus.pub(msg_topic, value, auto_send=False)
            self.data_bus.send_all()