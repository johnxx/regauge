import board
import digitalio
import busio
import canio
import time
from collections import namedtuple

Frame = namedtuple("Frame", "struct", "fields")

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

    def __init__(self, can) -> None:
        self.listener = can.listen(matches=[self.match], timeout=1)
        pass
    
    def poll(self):
        message = self.listener.receive()
        if message is None:
            print("No messsage received within timeout")
            return
     
        if len(message.data) != 8:
            print(f"Unusual message length {len(message.data)}")
            return