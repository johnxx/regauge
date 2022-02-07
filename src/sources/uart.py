import board
import busio
import struct
# import time

debug = False
debug1 = False
debug2 = False
debug3 = False
def print_dbg3(some_string, **kwargs):
    if debug3:
        return print(some_string, **kwargs)
def print_dbg2(some_string, **kwargs):
    if debug2:
        return print(some_string, **kwargs)
def print_dbg1(some_string, **kwargs):
    if debug1:
        return print(some_string, **kwargs)

# uart = busio.UART(board.TX, board.RX, baudrate=115200)
class DataSource():

    frameDefinitions = {
        # The real one
        # 1536: "<HBbHH"
        0x600: "<HBbHH",
        0x602: "<HBBBBH",
        0x603: "<BBBBHH",
        0x604: "<BbHHBB",
        0x900: "<BBBBBBBB"
        # 1536: "<hhhbbh"
    }

    fields = {
        0x600: ['eng_rpm', 'tps_pct', 'iat_cel', 'map_kpa', 'injpw_ms'],
        0x602: ['vss_kmh', 'baro_kpa', 'oiltemp_cel', 'oilpres_psi', 'fuelpres_kpa', 'clt_cel'],
        0x603: ['ignadv_deg', 'igndwell_ms', 'o2_lambda', 'egocor_pct', 'egt1_cel', 'egt2_cel'],
        0x604: ['gear_num', 'ecutemp_cel', 'batt_volts', 'cel_bits', 'flags_bits', 'ethcont_pct'],
        0x900: ['cpu_pct', 'mem_pct', 'cput_cel', 'f4', 'f5', 'f6', 'f7', 'f8'],
    }

    frameMagic = bytearray([0x44, 0x33, 0x22, 0x11])

    def __init__(self, name, resources, poll_freq=5) -> None:
        self._poll_freq = poll_freq
        self.data_bus = resources['data_bus']
        self.frame_idx = 0
        self.synced = False
        self.synced_for = 0
        self.in_dev = busio.UART(board.TX, board.RX, baudrate=115200)
        # self.in_dev = busio.UART(board.TX, board.RX, baudrate=57600)

    @property
    def poll_freq(self):
        return self._poll_freq


    # Read a 16 byte frame
    def receiveCANFrame(self):
        return self.in_dev.read(16)

    # Get aligned with remote and return the first usable frame
    def alignToRemote(self):
        # We're looking for the first character in the frame header (frameMagic)
        synced_to = 0
        # We'll take 10 attempts before giving up
        attempts_left = 5
        # Wait here until we see a complete frame header
        while synced_to < len(self.frameMagic):
            if attempts_left == 0:
                print_dbg1("We bailed")
                return None
            attempts_left -= 1
            # print("{} attempts left".format(attempts_left))
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
        print_dbg1("We succeeded with {} attempts left".format(attempts_left))
        return self.frameMagic + self.in_dev.read(12)

    def dostuff(self, frame):
        # This is where we'd do stuff with the frame we just got
        frameId, framePayload = self.unpackFrame(frame, self.frameDefinitions, self.fields)
        # if frameId == 0x600:
        #     return framePayload['eng_rpm']
        if frameId:
            # print(10)
            return frameId, framePayload
        # print(20)
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
                # print(1)
                return None, None
            if len(frame) == 16 and frame[:4] == self.frameMagic:
                # ... then do something with it
                # print(2)
                frameId, payload = self.dostuff(frame)
                # print(frameId)
                # print(payload)
                self.synced_for += 1
                print_dbg2("Synced for {} frames".format(self.synced_for))
                print_dbg1("Returned frame while synced")
                return frameId, payload
            else:
                print_dbg1("Out of sync")
                self.synced_for = 0
                self.synced = False
                return None, None
        else:
            frame = self.alignToRemote()
            if frame:
                self.synced = True
                # print(3)
                frameId, payload = self.dostuff(frame)
                # print(frameId)
                print_dbg1("Synced")
                self.synced_for = 1
                return frameId, payload
            else:
                # print(4)
                print_dbg1("Failed to sync")
                return None, None

    async def poll(self):
        res = None
        try:
            _, res = self.receive()
        except:
            print("We barfed")
            pass
        if res:
            for key, value in res.items():
                print_dbg3("Set {} to {}".format(key, value))
                msg_topic = "data.{}".format(key)
                self.data_bus.pub(msg_topic, value, auto_send=False)
            self.data_bus.send_all()