from gauge_face import GaugeFace
import math

debug = False
def print_dbg(some_string, **kwargs):
    if debug:
        return print(some_string, **kwargs)

class Face(GaugeFace):
    
    default_options = {
        'warning_level': 0.75, 
        'critical_level': 0.95, 
        'normal_color': 0x00ff00,
        'warning_color': 0xffff00, 
        'critical_color': 0xff0000,
        'off_color': 0x000000
    }

    def __init__(self, ts, options, resources) -> None:
        if not resources['leds'] or resources['leds'].n() < 2:
            raise ValueError("We need 2 or more NeoPixels")

        self.ts = ts
        self.options = self._apply_defaults(options)
        self.resources = resources
        self.pixels = resources['leds']

        self.pixels.fill(self.options['off_color'])

        self.prev_idx = 0

    def _range_per_segment(self):
        return (self.ts.stream_spec.max_val - self.ts.stream_spec.min_val) / self.pixels.n()

    def _value_to_segment(self):
        return math.floor((self.ts.value - self.ts.stream_spec.min_val) / (self.ts.stream_spec.max_val - self.ts.stream_spec.min_val) * (self.pixels.n() - 1))
    
    def _pick_color(self, idx):
        v = self._range_per_segment() * (idx + 1) + self.ts.stream_spec.min_val
        if v > self.options['critical_level']:
            print_dbg("Picked critical for {} ({})".format(v, idx))
            return self.options['critical_color']
        elif v > self.options['warning_level']:
            print_dbg("Picked warning for {} ({})".format(v, idx))
            return self.options['warning_color']
        else:
            print_dbg("Picked normal for {} ({})".format(v, idx))
            return self.options['normal_color']

    def _pick_color_old(self):
        if self.ts.value > self.options['critical_level']:
            return self.options['critical_color']
        elif self.ts.value > self.options['warning_level']:
            return self.options['warning_color']
        else:
            return self.options['normal_color']

    def config_updated(self, options):
        self.options = self._apply_defaults(options)
        print_dbg("Color set to: {}".format(self.options['normal_color']))
        self.pixels.fill(self.options['off_color'])
        self.prev_idx = 0
        self.update()

    def update(self):
        self.cur_idx = self._value_to_segment()
        print_dbg("Turning on  {}/{} LEDs for value {}/{}".format(self.cur_idx+1, self.pixels.n(), self.ts.value, self.ts.stream_spec.max_val))
        pix_range = range(self.pixels.n())
        for n in pix_range:
            if n < self.cur_idx:
                self.pixels[n] = self._pick_color(n)
            elif n == self.cur_idx:
                self.pixels[n] = self._pick_color_old()
            else:
                self.pixels[n] = self.options['off_color']

    def update_old(self):
        self.cur_idx = self._value_to_segment()
        # print("Rendering {}:{} as {}".format(self.stream_spec.field_spec, self.value, self.cur_idx))
        if self.prev_idx >= 0 and self.cur_idx < self.prev_idx:
            for s in range(self.cur_idx + 1, self.prev_idx + 1):
                self.pixels[s] = self.options['off_color']
        if self.prev_idx >= 0 and self.cur_idx > self.prev_idx:
            for s in range(self.prev_idx, self.cur_idx):
                self.pixels[s] = self._pick_color()
        self.pixels[self.cur_idx] = self._pick_color()
        # print("Displaying value: {} as {}".format(self._value, self.cur_idx))
        self.prev_idx = self.cur_idx