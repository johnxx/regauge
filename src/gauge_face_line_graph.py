from adafruit_display_shapes import line
from gauge_face import GaugeFace
import displayio
import math
import time

debug = False
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
        self.dots = displayio.Group()
        self.lines = displayio.Group()
        self.display_group.append(self.lines)
        self.display_group.append(self.dots)
        
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
        
        self.margin_top = 60
        self.margin_bottom = 40

        self._values = []
        
        self.last_x = 0
        self.last_y = 0

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
        return math.floor(self.last_x+self.seg_x)
        
    def pick_y(self, v):
        return (self.height - math.floor(((v - self.stream_spec.min_val) / self.stream_spec.max_val)*(self.height-self.margin_bottom-self.margin_top)))-self.margin_bottom

    def pick_y_full(self, v):
        return self.height - math.floor(((v - self.stream_spec.min_val) / self.stream_spec.max_val)*self.num_seg_y*self.seg_y)

    def _trim_sprites(self, display_group):
        n = 0
        for s in display_group:
            print_dbg("Removed a sprite at: {}x{}".format(s.x, s.y))
            display_group.remove(s)
            n += 1
            if n > self.num_seg_x:
                print_dbg("Trimming total sprites")
                break
        
    def update(self):
        # self._trim_sprites(self.lines)
        # self._trim_sprites(self.dots)
            
        added = 0
        for i, v in enumerate(self._values[-self.num_seg_x:]):
            x = self.pick_x(i)
            y = self.pick_y(v)
            # print_dbg("{} -> {}".format(v, y))
            print_dbg("Drawing {}, {} to {}x{}".format(i, v, x, y))
            graph_pixel = displayio.TileGrid(bitmap=self.sprite, height=1, width=1, pixel_shader=self.palette, x=x, y=y)
            self.dots.append(graph_pixel)
            # @TODO: Draw the rest of the horse
            line_conn = line.Line(x0=self.last_x, y0=self.last_y, x1=x, y1=y, color=self.palette[0])
            self.lines.append(line_conn)
            self.last_x = x
            self.last_y = y
            added += 1
        if len(self.lines) > self.num_seg_x:
            # print("last x was: {}".format(self.last_x))
            self.last_x -= self.seg_x*added
            # print("last x now: {}".format(self.last_x))
            for s in self.lines:
                s.x -= self.seg_x*added
                if s.x < 0:
                    # print("Removed line at {}x{}".format(s.x, s.y))
                    self.lines.remove(s)
                # if s.x > self.last_x:
                #     self.last_x = s.x

        if len(self.dots) > self.num_seg_x:
            for s in self.dots:
                s.x -= self.seg_x*added
                if s.x < 0:
                    print_dbg("Removed dot at {}x{}".format(s.x, s.y))
                    self.dots.remove(s)
        
        self._values = []
        print_dbg("Drew {} dots and {} lines".format(len(self.dots), len(self.lines)))
        print_dbg("print_dbged up to: {}x{}".format(self.last_x,self.last_y))