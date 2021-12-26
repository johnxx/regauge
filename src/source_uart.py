import board
import busio
import struct
# import time

debug = False
def print_dbg(some_string, **kwargs):
    if debug:
        return print(some_string, **kwargs)

# uart = busio.UART(board.TX, board.RX, baudrate=115200)
class DataSource():

    frameDefinitions = {
        # The real one
        # 1536: "<HBbHH"
        0x600: "<HBbHH",
        0x602: "<HBBBBH",
        0x604: "<BbHHBB",
        0x900: "<BBBBBBBB"
        # 1536: "<hhhbbh"
    }

    fields = {
        0x600: ['eng_rpm', 'tps_pct', 'iat_cel', 'map_kpa', 'injpw_ms'],
        0x602: ['vss_kmh', 'baro_kpa', 'oiltemp_cel', 'oilpres_psi', 'fuelpres_kpa', 'clt_cel'],
        0x604: ['gear_num', 'ecutemp_cel', 'batt_volts', 'cel_bits', 'flags_bits', 'ethcont_pct'],
        0x900: ['cpu_pct', 'mem_pct', 'cput_cel', 'f4', 'f5', 'f6', 'f7', 'f8'],
    }

    frameMagic = bytearray([0x44, 0x33, 0x22, 0x11])

    def __init__(self, name, resources, target, poll_freq=5) -> None:
        self.target = target
        self._poll_freq = poll_freq
        self.data_bus = resources['data_bus']
        self.frame_idx = 0
        self.synced = False
        self.in_dev = busio.UART(board.TX, board.RX, baudrate=115200)

    @property
    def poll_freq(self):
        return self._poll_freq


    # Read a 16 byte frame
    def receiveCANFrame(in_dev):
        return in_dev.read(16)

    # Get aligned with remote and return the first usable frame
    def alignToRemote(self):
        # We're looking for the first character in the frame header (frameMagic)
        synced_to = 0
        # We'll take 10 attempts before giving up
        attempts_left = 10
        # Wait here until we see a complete frame header
        while synced_to < len(self.frameMagic):
            if attempts_left == 0:
                return None
            attempts_left -= 1
            # Read 1 byte from input
            data = self.in_dev.read(1)
            # If there's no data, loop and poll again
            if data == None:
                continue
            current_char = int.from_bytes(data, 'little')
            # If we receive the next character we're expecting in our frame header
            if self.frameMagic[synced_to] == current_char:
                # ... then look for the next character on the next loop
                synced_to += 1
            else:
                # otherwise start looking for matches from the beginning
                synced_to = 0
            if debug:
                print(" " + hex(current_char), end='')
        # If we get here, we just saw the frame header, so read the next 12 data bytes and return those
        return self.frameMagic + self.in_dev.read(12)

    def dostuff(self, frame):
        # This is where we'd do stuff with the frame we just got
        frameId, framePayload = self.unpackFrame(frame, self.frameDefinitions, self.fields)
        # if frameId == 0x600:
        #     return framePayload['eng_rpm']
        if frameId:
            return frameId, framePayload
        return None, None

    def unpackFrame(self, frame, defs, fields):
        # Fish the frame ID out of the 4 bytes after the header
        frameId = int.from_bytes(frame[4:8], 'little')
        if frameId not in fields or frameId not in defs:
            if debug:
                print(frameId, end='')
            return None, None
        # Field names
        keys = fields[frameId]
        # Unpack values from the struct
        values = struct.unpack(defs[frameId], frame[8:])
        # Make a dict from field names and frame values
        return frameId, dict(zip(keys, values))

    def receive(self):
        if self.synced:
            frame = self.receiveCANFrame()
            if not frame:
                return None, None

            if len(frame) == 16 and frame[:4] == self.frameMagic:
                # ... then do something with it
                return self.dostuff(frame)
            else:
                self.synced = False
        else:
            frame = self.alignToRemote()
            if frame:
                self.synced = True
                return self.dostuff(frame)
            else:
                return None, None

    async def poll(self):
        _, res = self.receive()
        if res:
            for key, value in res.items():
                if key not in self.target:
                    self.target[key] = {}
                if 'value' not in self.target[key] or self.target[key]['value'] != value:
                    print_dbg("Set {} to {}".format(key, value))
                    self.target[key]['value'] = value
                    msg_topic = "data.{}".format(key)
                    self.data_bus.pub(msg_topic, value, auto_send=False)
            self.data_bus.send_all()