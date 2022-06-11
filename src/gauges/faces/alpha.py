from adafruit_bitmap_font import bitmap_font
from adafruit_display_shapes import line
from adafruit_display_shapes.polygon import Polygon
from adafruit_display_text.label import Label
from gauge_face import GaugeFace
from area import Area
import displayio
import json
import math
import time

instrumentation = False
debug = False
dump_cfg = False

y_offset = 120
x_offset = 120

def print_dbg(some_string, **kwargs):
    if debug:
        return print(some_string, **kwargs)

class Face(GaugeFace):
    default_options = {
        # 'label_font': 'UpheavalTT-BRK--20.bdf',
        'label_font': 'Cloude_Regular_Bold_1.02-32.bdf',
        'font_color':0xCCCCCC, 
        'bar_color':0xFF8888, 
    }

    def arc_points(self, r, a1, a2, segments=None):
        if not segments:
            segments = abs((a2 - a1) * 36)
        points = []
        a = a1
        s = 0
        while s <= segments:
            x = int(r * math.cos(a))
            y = int(r * math.sin(a))
            a += (a2 - a1)/segments
            s += 1
            points.append(self.tl_o((x, y)))

        return points


    def height_to_angle(self, h):
        return math.asin(h/y_offset)
    
    def tl_o(self, p):
        return p[0] + x_offset, -p[1] + y_offset
    
    # Results undefined if q outside of polygon
    def max_y(self, points, q):
        left_x = None
        right_x = None
        for x, y in points:
            if x < q:
                left = (x, y)
            if x > q and left_x:
                right = (x, y)
                slope = (right[1] - left[1]) / (right[0] - left[0])
                # @TODO: Uhm, that's probably not right.
                return q, left[1] + (right[0] - q) * slope
    def _setup_display(self):
        
        y1 = 0 
        y2 = 80 
        y3 = 20 
        
        a1 = self.height_to_angle(y1)
        a2 = self.height_to_angle(y2)
        a3 = self.height_to_angle(y3)

        r = 110

        points = self.arc_points(r, math.pi-a1, math.pi-a2)
        points += self.arc_points(r, a2, a3)
        points.append(self.tl_o((40,20)))
        points.append(self.tl_o((30,0)))
        print(json.dumps(points))

        p = Polygon(points=points, outline=0xFF8888)
        self.display_group.append(p)

    def __init__(self, ts, options, resources) -> None:
        if dump_cfg:
            print("time_series: {}".format(json.dumps(ts)))
            print("options: {}".format(json.dumps(options)))
            print("resources: {}".format(json.dumps(resources)))
        self.ts = ts
        self.options = self._apply_defaults(options)
        self.resources = resources
        self.display_group = resources['display_group']

        self.palette = displayio.Palette(1) 
        self.palette[0] = 0xFFFFFF

        if instrumentation:
            self.current_second = math.floor(time.monotonic())
            self.frames_this_second = 0

        self._setup_display()

    @property
    def num_seg_x(self):
        return math.floor(self.width / self.seg_x)

    @property
    def num_seg_y(self):
        return math.floor(self.height / self.seg_y)

    def pick_x(self, v):
        return math.floor(self.last_x+self.seg_x)
        
    def pick_y(self, v):
        as_pct = (v - self.ts.stream_spec.min_val) / self.ts.stream_spec.max_val
        # print("Showing value {} as pct {}".format(v, as_pct))
        return (self.height - math.floor(as_pct*(self.height-self.margin_bottom-self.margin_top)))-self.margin_bottom

    def update(self):
        pass