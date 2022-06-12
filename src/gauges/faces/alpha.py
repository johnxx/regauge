from adafruit_bitmap_font import bitmap_font
from adafruit_display_shapes import line
from adafruit_display_shapes.polygon import Polygon
from adafruit_display_shapes.line import Line
from adafruit_display_shapes.circle import Circle
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

    def arc_points(self, r, a1, a2, center=(0, 0), segments=None):
        if not segments:
            segments = abs((a2 - a1) * 36)
        points = []
        a = a1
        s = 0
        while s <= segments:
            x = int(r * math.cos(a)) + center[0]
            y = int(r * math.sin(a)) + center[1]
            a += (a2 - a1)/segments
            s += 1
            points.append(self.o_tl((x, y)))

        return points


    def height_to_angle(self, h):
        return math.asin(h/y_offset)
    
    def o_tl(self, p):
        return p[0] + x_offset, -p[1] + y_offset
    
    def tl_o(self, p):
        return p[0] - x_offset, y_offset - p[1]
    
    # Results undefined if q outside of polygon
    def min_x(self, points, q):
        return self.max_x(points[::-1], q)

    # Results undefined if q outside of polygon
    def max_x(self, points, q):
        return self.max_y(list(map(lambda p: (p[1], p[0]), points)), q)

    # Results undefined if q outside of polygon
    def min_y(self, points, q):
        return self.max_y(points[::-1], q)

    # Results undefined if q outside of polygon
    def max_y(self, points, q):
        left = None
        for x, y in points:
            if x < q:
                left = (x, y)
            if x > q and left:
                right = (x, y)
                print("left: {}, right: {}, q: {}".format(left, right, q))
                slope = (right[1] - left[1]) / (right[0] - left[0])
                # @TODO: Uhm, that's not quite right.
                return int(slope * (q - left[0]) + left[1])
        print("Comin' back around again")
        left = points[-1]
        right = points[0]
        print("left: {}, right: {}, q: {}".format(left, right, q))
        if right[0] == left[0]:
            print("By special dispensation")
            return int((right[1] + left[1])/2)
        slope = (right[1] - left[1]) / (right[0] - left[0])
        # @TODO: Uhm, that's not quite right.
        return int(slope * (q - left[0]) + left[1])

    def _setup_display(self):
        
        y1 = 0 
        y2 = 80 
        y3 = 20 
        
        a1 = self.height_to_angle(y1)
        a2 = self.height_to_angle(y2)
        a3 = self.height_to_angle(y3)

        r = 105

        points = self.arc_points(r, math.pi-a1, math.pi-a2)
        points += self.arc_points(r, a2, a3)
        points.append(self.o_tl((40,20)))
        points.append(self.o_tl((30,0)))

        p = Polygon(points=points, outline=0xFF8888)
        self.display_group.append(p)
        margin = 5
        radius = 5
        _, bly = self.o_tl((0, y1 + margin + radius))
        blx = self.min_x(points, bly) + margin + radius
        print("blx: {}".format(blx))
        segments = 15
        x = blx
        x_bonus = 20
        bar = []
        while segments > 0:
            y = self.min_y(points, x)
            # c = Circle(x0=x, y0=y - margin, r=radius, outline=0xCCCCCC)
            # self.display_group.append(c)
            bar += self.arc_points(radius, 0.5, 1.5, center=(x, y))

            top_x = x + x_bonus
            top_y = self.max_y(points, top_x)
            # c = Circle(x0=top_x, y0=top_y + margin, r=radius, outline=0xCCCCCC)
            # self.display_group.append(c)
            bar += self.arc_points(radius, 1.5, 0.5, center=(top_x, top_y))

            x += margin + radius
            segments -= 1

        bar_poly = Polygon(points=bar, outline=0x9944FF)
        self.display_group.append(bar_poly)

    # min max testing
    def test_min_max(self, poly, oqx, oqy):
        qx, _ = self.o_tl((oqx, 0))
        miny = self.min_y(poly, qx)
        maxy = self.max_y(poly, qx)
        l1 = Line(x0=qx, y0=miny, x1=qx, y1=maxy, color=0xCCFFCC)
        self.display_group.append(l1)

        qy, _ = self.o_tl((oqy, 0))
        minx = self.min_x(poly, qy)
        maxx = self.max_x(poly, qy)
        l2 = Line(x0=minx, y0=qy, x1=maxx, y1=qy, color=0xCCCCFF)
        self.display_group.append(l2)
        # print("max: {}".format((q, self.max_y(points, q))))
        # print("o max: {}".format(self.tl_o((q, self.max_y(points, q)))))
        # print("min: {}".format((q, self.min_y(points, q))))
        # print("o min: {}".format(self.tl_o((q, self.min_y(points, q)))))

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