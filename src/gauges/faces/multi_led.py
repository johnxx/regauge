from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.label import Label
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
        'off_color': 0x000000,
        'label': None,
        'label_font': 'PixelLCD-7-16.bdf',
        'font_color':0xCCCCCC, 
        'fmt_string': "{:>3.0f}{}", 
    }

    def __init__(self, ts, options, resources) -> None:
        if not resources['leds'] or resources['leds'].n() < 2:
            raise ValueError("We need 2 or more NeoPixels")

        self.ts = ts
        self.options = self._apply_defaults(options)
        self.resources = resources
        self.pixels = resources['leds']
        
        if self.options['label']:
            self.lcd = resources['lcd']
            font = bitmap_font.load_font("/share/fonts/" + self.options['label_font'])
            if self.options['label'] == 'top':
                self.label = Label(font, text='', color=self.options['font_color'], scale=1,
                                        anchor_point=(1, 0), anchored_position=(145, 20))
            elif self.options['label'] == 'bottom':
                self.label = Label(font, text='', color=self.options['font_color'], scale=1,
                                        anchor_point=(1, 0), anchored_position=(145, 220))
            resources['display_group'].append(self.label)

        self.pixels.fill(self.options['off_color'])

        self.prev_idx = 0
        self.prev_val = 0

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
        self.label.color = options['font_color']
        self.update()

    def update(self):
        if self.prev_val == self.ts.value:
            return
        self.prev_val = self.ts.value
        if self.options['label']:
            print_dbg("Updating label: {}".format(self.ts.value))
            self.label.text = self.options['fmt_string'].format(self.ts.value, self.ts.stream_spec.units['suffix'])
            self.lcd['dirty'] = True
        self.cur_idx = self._value_to_segment()
        if self.prev_idx == self.cur_idx:
            return
        print_dbg("Turning on  {}/{} LEDs for value {}/{}".format(self.cur_idx+1, self.pixels.n(), self.ts.value, self.ts.stream_spec.max_val))
        pix_range = range(self.pixels.n())
        print_dbg("Only {} need to be updated".format(len(pix_range)))
        for n in pix_range:
            if n < self.cur_idx:
                self.pixels[n] = self._pick_color(n)
            elif n == self.cur_idx:
                self.pixels[n] = self._pick_color_old()
            else:
                self.pixels[n] = self.options['off_color']
        self.prev_idx = self.cur_idx
