from gauge_face import GaugeFace
import math

class Face(GaugeFace):
    
    default_options = {
        'warning_level': 0.75, 
        'critical_level': 0.95, 
        'normal_color': 0x00ff00,
        'warning_color': 0xffff00, 
        'critical_color': 0xff0000,
        'off_color': 0x000000
    }

    def __init__(self, stream_spec, options, resources) -> None:
        if not stream_spec or not resources['leds']:
            raise ValueError("stream_spec is required")
        if not resources['leds'] or resources['leds'].n() < 2:
            raise ValueError("We need 2 or more NeoPixels")

        self.stream_spec = stream_spec
        self.options = self._apply_defaults(options)
        self.resources = resources
        self.pixels = resources['leds']

        self.pixels.fill(self.options['off_color'])

        self.prev_idx = 0

    def _value_to_segment(self):
        return math.floor((self.value - self.stream_spec.min_val) / self.stream_spec.max_val * (self.pixels.n() - 1))

    def _pick_color(self):
        if self.value > self.options['critical_level']:
            return self.options['critical_color']
        elif self.value > self.options['warning_level']:
            return self.options['warning_color']
        else:
            return self.options['normal_color']

    def config_updated(self, options):
        self.options = self._apply_defaults(options)
        print("Color set to: {}".format(self.options['normal_color']))
        self.pixels.fill(self.options['off_color'])
        self.prev_idx = 0
        self.update()


    def update(self):
        self.cur_idx = self._value_to_segment()
        if self.prev_idx >= 0 and self.cur_idx < self.prev_idx:
            for s in range(self.cur_idx + 1, self.prev_idx + 1):
                self.pixels[s] = self.options['off_color']
        if self.prev_idx >= 0 and self.cur_idx > self.prev_idx:
            for s in range(self.prev_idx, self.cur_idx):
                self.pixels[s] = self._pick_color()
        self.pixels[self.cur_idx] = self._pick_color()
        # print("Displaying value: {} as {}".format(self._value, self.cur_idx))
        self.prev_idx = self.cur_idx