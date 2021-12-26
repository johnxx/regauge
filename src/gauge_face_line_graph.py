from adafruit_display_shapes import line
from gauge_face import GaugeFace
import displayio
import math
import time

debug = True
def print_dbg(some_string, **kwargs):
    if debug:
        return print(some_string, **kwargs)

class Face(GaugeFace):
    default_options = {}

    def __init__(self, stream_spec, options, resources) -> None:
        self.stream_spec = stream_spec
        self.options = self._apply_defaults(options)
        self.resources = resources
        self.display_group = resources['display_group']

        
        self.palette = displayio.Palette(1) 
        self.palette[0] = 0xFF0000

        cell_fg = displayio.Bitmap(1, 1, 1)
        self.sprite = displayio.Bitmap(1, 1, 1)
        cell_fg.fill(1)
        self.sprite.blit(1, 1, cell_fg, x1=0, y1=0, x2=1, y2=1)

        self.seg_x = 10
        self.seg_y = 10

        self.width = 240
        self.height = 120

        self._values = []

    @property
    def num_seg_x(self):
        return math.floor(self.width / self.seg_x)

    @property
    def num_seg_y(self):
        return math.floor(self.height / self.seg_y)

    @property
    def subscribed_streams(self):
        return [self.stream_spec.field_spec]
        
    @property
    def value(self):
        return self._values[-1]

    @value.setter
    def value(self, value):
        self._values.append(value)
        if len(self._values) > self.num_seg_y:
            print_dbg("Truncate")
            del self._values[:-self.num_seg_x]
        
    def pick_x(self, v):
        return math.floor(v*self.seg_x)
        
    def pick_y(self, v):
        return self.height - math.floor(((v - self.stream_spec.min_val) / self.stream_spec.max_val)*self.num_seg_y*self.seg_y)

    def update(self):
        n = 0
        for i in self.display_group:
            self.display_group.remove(i)
            n += 1
            if n > self.num_seg_x:
                print_dbg("Trimming total sprites")
                break
            
        x = y = 0
        prev_x = -1
        prev_y = -1
        for i, v in enumerate(self._values[-self.num_seg_x:]):
            x = self.pick_x(i)
            y = self.pick_y(v)
            # print_dbg("{} -> {}".format(v, y))
            # print_dbg("Drawing to {}x{}".format(x, y))
            graph_pixel = displayio.TileGrid(bitmap=self.sprite, height=1, width=1, pixel_shader=self.palette, x=x, y=y)
            self.display_group.append(graph_pixel)
            if prev_x >= 0:
                # @TODO: Draw the rest of the horse
                line_conn = line.Line
        print_dbg("print_dbged up to: {}x{}".format(x,y))