import time
import math

debug = False
def print_dbg(some_string, **kwargs):
    if debug:
        return print(some_string, **kwargs)

class DataSource():

    mock_frames = [
        (0x902, {
            "clt_cel": {
                "min": 75,
                "max": 115,
                "pattern": "zigzag",
                "increment": 1,
                "every": 5
            },
            "oilpres_psi": {
                "min": 1,
                "max": 110,
                "pattern": "sin",
                "increment": 1,
                "every": 10
            },
            "eng_rpm": {
                "min": 4400,
                "max": 7500,
                "pattern": "zigzag",
                "increment": 100,
                "every": 1
            },
            "o2_lambda": {
                "min": 0.7/0.0078125,
                "max": 1.3/0.0078125,
                "pattern": "zigzag",
                "increment": 0.1,
                "every": 2
            }
        }),
        (0x998, {
            "pm2_5": {
                "min": 0,
                "max": 150,
                "pattern": "sin",
                "increment": 0.15,
                "every": 1
            },
            "co2_ppm": {
                "min": 0,
                "max": 5000,
                "pattern": "zigzag",
                "increment": 1,
                "every": 1
            },
            "temp_cel": {
                "min": 0,
                "max": 100,
                "pattern": "zigzag",
                "increment": 1,
                "every": 1
            },
            "rhum_pct": {
                "min": 0,
                "max": 100,
                "pattern": "zigzag",
                "increment": 100,
                "every": 1
            },
            "liquid_lpm": {
                "min": 0,
                "max": 10,
                "pattern": "zigzag",
                "increment": .1,
                "every": 1
            },
        }),
        (0x999, {
            "cpu_pct": {
                "min": 0,
                "max": 100,
                "pattern": "sin",
                "increment": 0.15,
                "every": 1
            },
            "mem_pct": {
                "min": 0,
                "max": 100,
                "pattern": "zigzag",
                "increment": 1,
                "every": 1
            },
            "cputemp_cel": {
                "min": 0,
                "max": 100,
                "pattern": "zigzag",
                "increment": 1,
                "every": 1
            },
            "fan_rpm": {
                "min": 0,
                "max": 6000,
                "pattern": "zigzag",
                "increment": 100,
                "every": 1
            },
        })
    ]

    @staticmethod
    def _get_frame_id(mock_frame):
        print_dbg("Adding: {}".format(mock_frame[0]))
        return mock_frame[0]

    def __init__(self, name, resources, poll_freq=5, send_frame_ids='all') -> None:
        if send_frame_ids == 'all':
            self.send_frame_ids = list(map(self._get_frame_id, self.mock_frames))
        else:
            self.send_frame_ids = send_frame_ids
        # print(dir(target))
        #self.target = target
        self._poll_freq = poll_freq
        self.data_bus = resources['data_bus']
        self.frame_idx = 0

    @property
    def poll_freq(self):
        print_dbg("Poll freq: {}".format(self._poll_freq))
        return self._poll_freq


    @staticmethod
    def zigzag(prev):
        wrapped = False
        if 'value' not in prev:
            prev['value'] = prev['min']
            return prev
        if prev['value'] > prev['max'] or prev['value'] < prev['min']:
            wrapped = True
            prev['increment'] *= -1
            # print("{} is over {}. Wrapping!".format(prev['value'], prev['max']))
        if 'frames' not in prev:
            prev['frames'] = 0
        if prev['frames'] == prev['every'] or wrapped:
            prev['value'] += prev['increment']
            prev['frames'] = 0
        else:
            prev['frames'] += 1
        return prev
    
    @staticmethod
    def sin(prev):
        if 'x' not in prev:
            prev['x'] = 0
        else:
            prev['x'] += prev['increment']
        prev['value'] = (((math.sin(prev['x'])+1) - prev['min']) / prev['max']) * 100 * prev['max']
        print_dbg("v: {}".format(prev['value']))
        return prev
        
        
    def process_mock_frame(self, frame):
        id = frame[0]
        mock_payload = frame[1]
        payload = {}
        for name, contents in mock_payload.items():
            if contents['pattern'] == 'zigzag':
                # print("Calling zigzag for {}".format(name))
                contents = self.zigzag(contents)
            elif contents['pattern'] == 'sin':
                contents = self.sin(contents)
            payload[name] = contents['value']
            # print(name)
            # print(json.dumps(contents))
        return id, payload
    
    def _advance_frame(self):
        num_frames = len(self.mock_frames)
        self.frame_idx += 1
        if self.frame_idx == num_frames:
           self.frame_idx = 0
        
    async def poll(self):
        if 'all' not in self.send_frame_ids:
            while self.mock_frames[self.frame_idx][0] not in self.send_frame_ids:
                print_dbg("Current id: {}, not in {}".format(self.mock_frames[self.frame_idx][0], self.send_frame_ids))
                self._advance_frame()
                print_dbg("Advanced to {}".format(self.frame_idx))

        res = self.process_mock_frame(self.mock_frames[self.frame_idx])
        payload = res[1]
        for key, value in payload.items():
            msg_topic = "data.{}".format(key)
            self.data_bus.pub(msg_topic, value, auto_send=False)
        self.data_bus.send_all()

        self._advance_frame()