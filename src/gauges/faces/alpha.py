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
import uprofile
import vectorio

uprofile.enabled = False
instrumentation = False
debug = True
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
        if min_x == None or x < min_x:
            min_x = x
        if max_x == None or x > max_x:
            max_x = x
        if min_y == None or y < min_y:
            min_y = y
        if max_y == None or y > max_y:
            max_y = y
    # return (min_x, min_y), (max_x, max_y)
    return (max_x, max_y), (min_x, min_y)

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

def seg_inside(poly, margin, a, offset=0, mid_y=None):
    bl, tr = poly_bbox(poly)
    if not mid_y:
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
    
def barify(s, r, a=0):
    bar = []
    bar += arc_points(r, 1*math.pi-1/a, 0*math.pi-1/a, center=tl_o(s[0]))
    bar += arc_points(r, -0*math.pi-1/a, -1*math.pi-1/a, center=tl_o(s[1]))
    return bar

def print_dbg(some_string, **kwargs):
    if debug:
        return print(some_string, **kwargs)

class Face(GaugeFace):
    default_options = {
        # 'label_font': 'UpheavalTT-BRK--20.bdf',
        # 'label_font': 'Cloude_Regular_Bold_1.02-32.bdf',
        'position': 'top',
        'gradient': "yellow_blurple",
        'label_font': 'PixelLCD-7-16.bdf',
        'font_color': 0xCCCCCC, 
        'fmt_string': "{:>3.0f}{}", 
        'bar_color': 0xFF8888, 
    }
    gradients = {
        # blue to orange: 9.5/10
        "blue_orange": [
            0x36578e,
            0x455894,
            0x545999,
            0x63599c,
            0x72589f,
            0x8257a0,
            0x91569f,
            0xa0549e,
            0xae529b,
            0xbc5096,
            0xc84e91,
            0xd44d8a,
            0xdf4d82,
            0xe84e79,
            0xf0506f,
            0xf65465,
            0xfb5a5a,
            0xfe624e,
            0xff6a42
        ],
        # yellow to blue/purple: 10/10 for general gauge
        "yellow_blurple": [
            0xfac76e,
            0xffbb6f,
            0xffaf72,
            0xffa477,
            0xff997d,
            0xfd8f84,
            0xf6878c,
            0xee8093,
            0xe37a9a,
            0xd676a1,
            0xc673a6,
            0xb671aa,
            0xa36fad,
            0x8f6eae,
            0x7a6cad,
            0x646baa,
            0x4c69a5,
            0x31669e,
            0x066395
        ],
        # blue to yellow with green in the middle 8/10 looks nice
        "blue_yellow": [
            0x2b7ea9,
            0x0086b0,
            0x008eb5,
            0x0096b8,
            0x009eb8,
            0x00a6b6,
            0x00adb1,
            0x00b4aa,
            0x00baa1,
            0x00c096,
            0x00c689,
            0x23cb7b,
            0x50d06b,
            0x70d45b,
            0x8ed74b,
            0xaad939,
            0xc6da27,
            0xe2da13,
            0xffd800
        ]
    }

    def _setup_display(self):
        def setup_bezel_mirrored(opts):
            y1 = -90
            y2 = -20
            y3 = -2
            
            a1 = height_to_angle(y1)
            a2 = height_to_angle(y2)
            a3 = height_to_angle(y3)

            r = 105

            points = arc_points(r, math.pi-a1, math.pi-a2)
            points[-1] = (points[-1][0], -y2+y_offset)
            points.append(o_tl((-18, -20)))
            points.append(o_tl((-10, -2)))
            points += arc_points(r, a3, a1)
            # points[-1] = (points[-1][0], -y3+y_offset)

            font = bitmap_font.load_font("/share/fonts/" + opts['label_font'])
            label = Label(font, text='', color=opts['font_color'], scale=1,
                                    anchor_point=(1, 0), anchored_position=(100, 123))

            return points, label

        def setup_bezel(opts):
            y1 = 2
            y2 = 90
            y3 = 20
            
            a1 = height_to_angle(y1)
            a2 = height_to_angle(y2)
            a3 = height_to_angle(y3)

            r = 105

            points = arc_points(r, math.pi-a1, math.pi-a2)
            points += arc_points(r, a2, a3)
            points[-1] = (points[-1][0], -y3+y_offset)
            points.append(o_tl((18, 20)))
            points.append(o_tl((10, 2)))

            font = bitmap_font.load_font("/share/fonts/" + opts['label_font'])
            label = Label(font, text='', color=opts['font_color'], scale=1,
                                    anchor_point=(1, 0), anchored_position=(225, 103))

            return points, label

        if self.options['position'] == 'top':
            bezel, label = setup_bezel(self.options)
        else:
            bezel, label = setup_bezel_mirrored(self.options)
        surround_bezel = Polygon(points=bezel, outline=0xCCCCCC)
        self.display_group.append(surround_bezel)

        total_segments = 19
        margin = 5 
        radius = 3.5 
        a = .4*math.pi

        current_segment = 0

        offset = 10
        segments = []
        while current_segment < total_segments:
            if self.options['position'] == 'top':
                si = seg_inside(bezel, margin, a, offset=offset)
            else:
                si = seg_inside(bezel, margin, a, offset=offset, mid_y=140)
            bar = barify(si, radius, a=a)
            
            pal = displayio.Palette(2)
            pal[0] = 0x222222
            pal[1] = self.gradients[self.options['gradient']][current_segment]
            bar_poly = vectorio.Polygon(points=bar, pixel_shader=pal)
            bar_poly.color_index = 1
            # bar_poly_outline = Polygon(points=bar, outline=0x55AAFF)

            # self.display_group.append(bar_poly)
            segments.append(bar_poly)
            # self.display_group.append(bar_poly_outline)
            
            offset += margin*2
            current_segment += 1
        return segments, label

    def __init__(self, ts, options, resources) -> None:
        if dump_cfg:
            print("time_series: {}".format(json.dumps(ts)))
            print("options: {}".format(json.dumps(options)))
            print("resources: {}".format(json.dumps(resources)))
        self.ts = ts
        self.options = self._apply_defaults(options)
        self.resources = resources
        self.display_group = resources['display_group']
        self.lcd = resources['lcd']

        self.palette = displayio.Palette(1) 
        self.palette[0] = 0xFFFFFF

        self.segments, self.label = self._setup_display()
        self.display_segments = displayio.Group()
        self.display_group.append(self.display_segments)

        self.display_group.append(self.label)
        self.last_val = 0
        self.last_lit = 0

    def pick_seg(self, v):
        as_pct = (v - self.ts.stream_spec.min_val) / self.ts.stream_spec.max_val 
        if as_pct > 1:
            as_pct = 1
        elif as_pct < 0:
            as_pct = 0
        return math.floor(as_pct * len(self.segments))

    def config_updated(self, options):
        self.options = self._apply_defaults(options)
        self.label.color = self.options['font_color']
        if 'gradient_start' in options and 'gradient_end' in options:
            start = options['gradient_start'].lstrip('#')
            end = options['gradient_end'].lstrip('#')
            start_rgb = tuple(int(start[i:i+2], 16) for i in (0, 2, 4))
            end_rgb = tuple(int(end[i:i+2], 16) for i in (0, 2, 4))
            n = len(self.segments) - 1
            r_step = int((end_rgb[0] - start_rgb[0])/n)
            g_step = int((end_rgb[1] - start_rgb[1])/n)
            b_step = int((end_rgb[2] - start_rgb[2])/n)
            seg_step = (r_step, g_step, b_step)
            # seg_color = int(start, 16)
            seg_rgb = start_rgb
            print(r_step)
            print(g_step)
            print(b_step)
            # print("Color: {}".format(seg_color))
            for s in self.segments:
                print("R: {}, G: {}, B: {}".format(seg_rgb[0], seg_rgb[1], seg_rgb[2]))
                pal = displayio.Palette(2)
                pal[0] = 0x222222
                pal[1] = seg_rgb
                s.pixel_shader = pal
                # print("Color: {}".format(seg_color))
                seg_rgb = (seg_rgb[0] + seg_step[0], seg_rgb[1] + seg_step[1], seg_rgb[2] + seg_step[2])

    @uprofile.profile('alpha', 'update')
    def update(self):
        num_segs = len(self.segments)
        if self.last_val == self.ts.value:
            return
        self.label.text = self.options['fmt_string'].format(self.ts.value, self.ts.stream_spec.units['suffix'])
        self.lcd['dirty'] = True

        lit = self.pick_seg(self.ts.value)

        if lit >= num_segs:
            lit = num_segs - 1
        elif lit < 1:
            lit = 1

        if lit == self.last_lit:
            return
        if lit > self.last_lit:
            for n in range(self.last_lit, lit):
                print_dbg("Turning on segment {}/{}".format(n, num_segs))
                self.display_segments.append(self.segments[n])
        elif lit < self.last_lit:
            for n in range(self.last_lit - 1, lit - 1, -1):
                print_dbg("Turning off segment {}/{}".format(n, num_segs))
                del self.display_segments[n]
                print_dbg("Turned off segment {}/{}".format(n, num_segs))
        print_dbg("Tried to light {}/{} segments".format(lit, num_segs))
        self.last_lit = lit
        self.last_val = self.ts.value
