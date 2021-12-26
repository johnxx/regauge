import time

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
                "every": 50
            },
            "oilpres_psi": {
                "min": 1,
                "max": 110,
                "pattern": "zigzag",
                "increment": 5,
                "every": 2
            },
            "eng_rpm": {
                "min": 4400,
                "max": 7500,
                "pattern": "zigzag",
                "increment": 150,
                "every": 1
            }
        }),
        (0x999, {
            "cpu_pct": {
                "min": 0,
                "max": 100,
                "pattern": "zigzag",
                "increment": 1,
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

    def __init__(self, name, resources, target, poll_freq=5) -> None:
        self.target = target
        self._poll_freq = poll_freq
        self.data_bus = resources['data_bus']
        self.frame_idx = 0

    @property
    def poll_freq(self):
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
        
    def process_mock_frame(self, frame):
        id = frame[0]
        mock_payload = frame[1]
        payload = {}
        for name, contents in mock_payload.items():
            if contents['pattern'] == 'zigzag':
                # print("Calling zigzag for {}".format(name))
                contents = self.zigzag(contents)
            payload[name] = contents['value']
            # print(name)
            # print(json.dumps(contents))
        return id, payload
        
    async def poll(self):
        num_frames = len(self.mock_frames)
        res = self.process_mock_frame(self.mock_frames[self.frame_idx])
        payload = res[1]
        for key, value in payload.items():
            if key not in self.target:
                self.target[key] = {}
            if 'value' not in self.target[key] or self.target[key]['value'] != value:
                print_dbg("Set {} to {}".format(key, value))
                self.target[key]['value'] = value
                msg_topic = "data.{}".format(key)
                self.data_bus.pub(msg_topic, value, auto_send=False)
        self.data_bus.send_all()

        self.frame_idx += 1
        if self.frame_idx == num_frames:
           self.frame_idx = 0
