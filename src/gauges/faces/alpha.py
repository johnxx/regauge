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
    xings = []
    n = -1
    end = len(poly)
    while n < end - 1:
        p1 = array([poly[n][0], poly[n][1]])
        p2 = array([poly[n+1][0], poly[n+1][1]])
        if intersect(p1, p2, seg[0], seg[1]):
            xings.append(seg_intersect(p1, p2, seg[0], seg[1]))
        n += 1
    return xings

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
        x = int(r * math.cos(a)) + center[0]
        y = int(r * math.sin(a)) + center[1]
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
        y1 = 0 
        y2 = 80 
        y3 = 20 
        
        a1 = height_to_angle(y1)
        a2 = height_to_angle(y2)
        a3 = height_to_angle(y3)

        r = 105

        points = arc_points(r, math.pi-a1, math.pi-a2)
        points += arc_points(r, a2, a3)
        points.append(o_tl((20,20)))
        points.append(o_tl((10,0)))
        # bl, tr = poly_bbox(points)
        # c1 = Circle(x0=bl[0], y0=bl[1], r=5, outline=0xCCCCCC)
        # self.display_group.append(c1)
        # c2 = Circle(x0=tr[0], y0=tr[1], r=5, outline=0xCCCCCC)
        # self.display_group.append(c2)

        # line = [array([0, 50]), array([120, 130])]
        # l1 = Line(x0=int(line[0][0]), y0=int(line[0][1]), x1=int(line[1][0]), y1=int(line[1][1]), color=0xCCFFCC)
        # self.display_group.append(p)
        # self.display_group.append(l1)
        # xings = poly_xings(points, line)
        # for n in xings:
        #     c = Circle(x0=int(n[0]), y0=int(n[1]), r=5, outline=0xCCCCCC)
        #     self.display_group.append(c)

        p = Polygon(points=points, outline=0xCCCCCC)
        self.display_group.append(p)
        margin = 9 
        radius = 5 
        _, bly = o_tl((0, y1 + margin + radius))
        blx = poly_line_min_x(points, bly) + margin + radius
        print("blx: {}".format(blx))
        total_segments = 10
        x = blx
        x_bonus = 20
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
            0x00eaff
        ]
        # pal = displayio.Palette(len(colors))
        # for idx, val in enumerate(colors):
        #     pal[idx] = val
        bl, tr = poly_bbox(points)
        mid_y = (tr[1]+bl[1])/2
        left_mid = (poly_line_min_x(points, mid_y) + 15, int(mid_y))
        bar_angle = .4*math.pi
        bar_slope = math.tan(bar_angle)
        print(bar_angle*(180/math.pi))

        c1 = Circle(x0=left_mid[0], y0=left_mid[1], r=5, outline=0xCCCCCC)
        self.display_group.append(c1)

        top_y = tr[1] - 10
        top_x = left_mid[0] + (1/bar_slope)*(mid_y-top_y)

        bottom_y = bl[1] + 10
        bottom_x = left_mid[0] + (1/bar_slope)*(mid_y-bottom_y)
        print((bottom_x, bottom_y))

        l0 = Line(x0=int(bottom_x), y0=int(bottom_y), x1=int(top_x), y1=int(top_y), color=0xCCFFCC)
        self.display_group.append(l0)
        # ten_above = array([(bl[0], tr[1] - 10), (tr[0], tr[1] - 10)])
        # l1 = Line(x0=int(ten_above[0][0]), y0=int(ten_above[0][1]), x1=int(ten_above[1][0]), y1=int(ten_above[1][1]), color=0xCCFFCC)
        # self.display_group.append(l1)

        segments = total_segments
        while segments > 0:
            # place the leftmost point 
            # figure out the slope of the line based on the passed in angle
            # draw a segment between leftmost point and the lower intersection
            # draw a segment between leftmost point and the upper intersection
            # Get the new segment into its own variable
            # figure out where it crosses the bottom and top of the polygon
            # Move $margin points in along the segment, taking slope into account
            # with these new points, draw the actual bar
            # Move right x points from the leftmost point and repeat
            x += margin + radius
            segments -= 1
            
        while segments > 0:
            bar = []
            y = poly_line_min_y(points, x) - margin
            # c = Circle(x0=x, y0=y - margin, r=radius, outline=0xCCCCCC)
            # self.display_group.append(c)
            # bar += self.arc_points(radius, 0.5, 1.5, center=(x, y))
            bar += arc_points(radius, -0*math.pi, -1*math.pi, center=tl_o((x, y)))

            # top_x = x + x_bonus
            top_x = x + x_bonus
            top_y = poly_line_max_y(points, top_x) + margin
            # c = Circle(x0=top_x, y0=top_y + margin, r=radius, outline=0xCCCCCC)
            # self.display_group.append(c)

            bar += arc_points(radius, 1*math.pi, 0*math.pi, center=tl_o((top_x, top_y)))

            print("Lower: {}, Upper: {}".format((x,y), (top_x,top_y)))
            pal = displayio.Palette(1)
            pal[0] = colors[total_segments - segments]
            bar_poly = vectorio.Polygon(points=bar, pixel_shader=pal)
            # bar_poly_outline = Polygon(points=bar, outline=pal[0] + 0x1111)
            bar_poly_outline = Polygon(points=bar, outline=0x55AAFF)
            # bar_poly.color_index = total_segments - segments
            self.display_group.append(bar_poly)
            self.display_group.append(bar_poly_outline)

            x += margin + radius
            segments -= 1


    # min max testing
    def test_min_max(self, poly, oqx, oqy):
        qx, _ = o_tl((oqx, 0))
        miny = poly_line_min_y(poly, qx)
        maxy = poly_line_max_y(poly, qx)
        l1 = Line(x0=qx, y0=miny, x1=qx, y1=maxy, color=0xCCFFCC)
        self.display_group.append(l1)

        qy, _ = o_tl((oqy, 0))
        minx = poly_line_min_x(poly, qy)
        maxx = poly_line_max_x(poly, qy)
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
