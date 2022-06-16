from adafruit_bitmap_font import bitmap_font
from adafruit_display_shapes import line
from adafruit_display_shapes.polygon import Polygon
from adafruit_display_shapes.line import Line
from adafruit_display_shapes.circle import Circle
from adafruit_display_text.label import Label
from gauge_face import GaugeFace
from ulab.numpy import dot, array
import displayio
import json
import math
import time
import vectorio

instrumentation = False
debug = False
dump_cfg = False

y_offset = 120
x_offset = 120

def ccw(A,B,C):
    return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])

# Return true if line segments AB and CD intersect
def intersect(A,B,C,D):
    return ccw(A,C,D) != ccw(B,C,D) and ccw(A,B,C) != ccw(A,B,D) 

# line segment a given by endpoints a1, a2
# line segment b given by endpoints b1, b2
# return 
def seg_intersect(a1, a2, b1, b2):
    da = a2 - a1
    db = b2 - b1
    dp = a1 - b1
    dap = array([-da[1], da[0]])
    denom = dot(dap, db)
    num = dot(dap, dp)
    return (num / denom) * db + b1

def poly_xings(poly, seg):
    print(seg)
    seg = array([seg[0], seg[1]])
    xings = []
    n = -1
    end = len(poly)
    while n < end - 1:
        p1 = array([poly[n][0], poly[n][1]])
        p2 = array([poly[n+1][0], poly[n+1][1]])
        if intersect(p1, p2, seg[0], seg[1]):
            xings.append(seg_intersect(p1, p2, seg[0], seg[1]))
        n += 1
    return sorted(xings, key=lambda p: p[1])

def poly_bbox(points):
    min_x, min_y, max_x, max_y = [None] * 4
    for x, y in points:
        if min_x == None or x > min_x:
            min_x = x
        if max_x == None or x < max_x:
            max_x = x
        if min_y == None or y > min_y:
            min_y = y
        if max_y == None or y < max_y:
            max_y = y
    return (min_x, min_y), (max_x, max_y)

def arc_points(r, a1, a2, center=(0, 0), segments=None):
    if not segments:
        segments = abs((a2 - a1) * 36)
    points = []
    a = a1
    s = 0
    while s <= segments:
        x = int(r * math.cos(a) + center[0])
        y = int(r * math.sin(a) + center[1])
        a += (a2 - a1)/segments
        s += 1
        points.append(o_tl((x, y)))

    return points


def height_to_angle(h):
    return math.asin(h/y_offset)

def o_tl(p):
    return p[0] + x_offset, -p[1] + y_offset

def tl_o(p):
    return p[0] - x_offset, y_offset - p[1]

# Results undefined if q outside of polygon
def poly_line_min_x(points, q):
    return poly_line_max_x(points[::-1], q)

# Results undefined if q outside of polygon
def poly_line_max_x(points, q):
    return poly_line_max_y(list(map(lambda p: (p[1], p[0]), points)), q)

# Results undefined if q outside of polygon
def poly_line_min_y(points, q):
    return poly_line_max_y(points[::-1], q)

# Results undefined if q outside of polygon
def poly_line_max_y(points, q):
    left = None
    for x, y in points:
        if x < q:
            left = (x, y)
        if x > q and left:
            right = (x, y)
            # print("left: {}, right: {}, q: {}".format(left, right, q))
            slope = (right[1] - left[1]) / (right[0] - left[0])
            # @TODO: Uhm, that's not quite right.
            return int(slope * (q - left[0]) + left[1])
    # print("Comin' back around again")
    left = points[-1]
    right = points[0]
    # print("left: {}, right: {}, q: {}".format(left, right, q))
    if right[0] == left[0]:
        # print("By special dispensation")
        return int((right[1] + left[1])/2)
    slope = (right[1] - left[1]) / (right[0] - left[0])
    # @TODO: Uhm, that's not quite right.
    return int(slope * (q - left[0]) + left[1])
    
def min_x(points):
    point_low_x = None
    for x, y in points:
        if not point_low_x or point_low_x[0] > x:
            point_low_x = (x, y)
    return point_low_x
    
def min_y(points):
    point_low_y = None
    for x, y in points:
        if not point_low_y or point_low_y[1] > y:
            point_low_y = (x, y)
    return point_low_y

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

    def _setup_display(self):
        def setup_bezel():
            y1 = 0 
            y2 = 80 
            y3 = 20 
            
            a1 = height_to_angle(y1)
            a2 = height_to_angle(y2)
            a3 = height_to_angle(y3)

            r = 105

            points = arc_points(r, math.pi-a1, math.pi-a2)
            points += arc_points(r, a2, a3)
            points[-1] = (points[-1][0], -y3+y_offset)
            points.append(o_tl((18,20)))
            points.append(o_tl((10,0)))

            return points

        bezel = setup_bezel()
        p = Polygon(points=bezel, outline=0xCCCCCC)
        self.display_group.append(p)

        total_segments = 19
        margin = 5 
        radius = 2.5 
        a = .4*math.pi

        colors = [
            0x0000ff,
            0x0044ff,
            0x0062ff,
            0x007aff,
            0x008eff,
            0x00a0ff,
            0x00b0ff,
            0x00c0ff,
            0x00cfff,
            0x00ddff,
            0x00eaff,
            0x00eaff,
            0x00eaff,
            0x00eaff,
            0x00eaff,
            0x00eaff,
            0x00eaff,
            0x00eaff,
            0x00eaff,
            0x00eaff
        ]

        def seg_inside(poly, margin, a, offset=0):
            bl, tr = poly_bbox(poly)
            mid_y = (tr[1]+bl[1])/2
            left_mid = (poly_line_min_x(poly, mid_y) + offset + margin, int(mid_y))
            slope = math.tan(a)

            top_y = tr[1] - 2
            top_x = left_mid[0] + (1/slope)*(mid_y-top_y)

            bottom_y = bl[1] + 2
            bottom_x = left_mid[0] + (1/slope)*(mid_y-bottom_y)

            outer_seg = (bottom_x, bottom_y), (top_x, top_y)
            top_xing, bottom_xing = poly_xings(poly, outer_seg)

            it_y = top_xing[1] + margin
            it_x = left_mid[0] + (1/slope)*(mid_y-it_y)
            inner_top = (it_x, it_y)
            
            ib_y = bottom_xing[1] - margin
            ib_x = left_mid[0] + (1/slope)*(mid_y-ib_y)
            inner_bottom = (ib_x, ib_y)
            
            return inner_top, inner_bottom
            
        def barify(s, r):
            bar = []
            bar += arc_points(r, 1*math.pi, 0*math.pi, center=tl_o(s[0]))
            bar += arc_points(r, -0*math.pi, -1*math.pi, center=tl_o(s[1]))
            return bar

        segments = total_segments

        offset = 10
        while segments > 0:
            si = seg_inside(bezel, margin, a, offset=offset)
            bar = barify(si, radius)
            
            pal = displayio.Palette(1)
            pal[0] = colors[total_segments - segments]

            bar_poly = vectorio.Polygon(points=bar, pixel_shader=pal)
            bar_poly_outline = Polygon(points=bar, outline=0x55AAFF)

            self.display_group.append(bar_poly)
            self.display_group.append(bar_poly_outline)
            
            offset += margin*2
            segments -= 1

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
