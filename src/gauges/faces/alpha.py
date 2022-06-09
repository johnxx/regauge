from adafruit_bitmap_font import bitmap_font
from adafruit_display_shapes import line
from adafruit_display_text.label import Label
from gauge_face import GaugeFace
import displayio
import json
import math
import time

instrumentation = False
debug = False
dump_cfg = False
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
        font = bitmap_font.load_font("/share/fonts/" + self.options['label_font'])
        self.text_top = Label(font, text='', color=self.options['font_color'], scale=1,
                                anchor_point=(0.5, 1), anchored_position=(self.options['label_offset_x'], self.options['label_offset_y']))
        self.display_group.append(self.text_top)
        self.top_line = line.Line(x0=0, y0=0, x1=self.width, y1=0, color=self.options['bottom_line_color'])
        self.display_group.append(self.top_line)

        self.text_bottom = Label(font, text='', color=self.options['font_color'], scale=1,
                                anchor_point=(0.5, 0), anchored_position=(self.options['label_offset_x'], self.options['label_offset_y']))
        self.display_group.append(self.text_bottom)
        self.bottom_line = line.Line(x0=0, y0=self.height, x1=self.width, y1=self.height, color=self.options['bottom_line_color'])
        self.display_group.append(self.bottom_line)


    def __init__(self, ts, options, resources) -> None:
        if dump_cfg:
            print("time_series: {}".format(json.dumps(ts)))
            print("options: {}".format(json.dumps(options)))
            print("resources: {}".format(json.dumps(resources)))
        self.ts = ts
        self.options = self._apply_defaults(options)
        self.resources = resources
        self.display_group = resources['display_group']
        self.dots = displayio.Group()
        self.lines = displayio.Group()
        self.display_group.append(self.lines)
        self.display_group.append(self.dots)

         
        self.palette = displayio.Palette(1) 
        self.palette[0] = self.options['graph_line_color']

        cell_fg = displayio.Bitmap(1, 1, 1)
        self.sprite = displayio.Bitmap(1, 1, 1)
        cell_fg.fill(1)
        self.sprite.blit(1, 1, cell_fg, x1=0, y1=0, x2=1, y2=1)

        self.seg_x = 10
        self.seg_y = 10

        self.width = 240
        self.height = 120
        
        self.margin_top = 10
        self.margin_bottom = 30

        self.last_x = 0
        self.last_y = 0
        
        self.latest_tstamp = 0
        self.ts.upto_vals = self.num_seg_x

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

    # no margins
    # def pick_y(self, v):
    #     return self.height - math.floor(((v - self.stream_spec.min_val) / self.stream_spec.max_val)*self.num_seg_y*self.seg_y)

    def update(self):
        # self._trim_sprites(self.lines)
        # self._trim_sprites(self.dots)
            
        num_segs = self.num_seg_x
        print_dbg("Current number of segments: {}".format(num_segs))
        added = 0
        for i, v in enumerate(self.ts.since(self.latest_tstamp)):
            if v[0] > self.latest_tstamp:
                self.latest_tstamp = v[0]
            x = self.pick_x(i)
            y = self.pick_y(v[1])
            # print_dbg("{} -> {}".format(v, y))
            print_dbg("Drawing {}, {} to {}x{}".format(i, v[1], x, y))
            graph_pixel = displayio.TileGrid(bitmap=self.sprite, height=1, width=1, pixel_shader=self.palette, x=x, y=y)
            self.dots.append(graph_pixel)
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

        min_y = self.pick_y(self.ts.min_val)
        self.bottom_line.y = min_y
        self.text_bottom.text = self.options['fmt_string'].format(self.ts.min_val, self.ts.stream_spec.units['suffix'])
        new_min = (self.text_bottom.anchored_position[0], min_y)
        self.text_bottom.anchored_position = new_min

        max_y = self.pick_y(self.ts.max_val)
        self.top_line.y = max_y
        self.text_top.text = self.options['fmt_string'].format(self.ts.max_val, self.ts.stream_spec.units['suffix'])
        new_max = (self.text_top.anchored_position[0], max_y)
        self.text_top.anchored_position = new_max
        
        if instrumentation:
            this_second = math.floor(time.monotonic())
            if self.current_second != this_second:
                print("framerate: {}".format(self.frames_this_second))
                self.frames_this_second = 1
                self.current_second = this_second
            else:
                self.frames_this_second += 1
        
        print_dbg("Drew {} dots and {} lines".format(len(self.dots), len(self.lines)))
        print_dbg("print_dbged up to: {}x{}".format(self.last_x,self.last_y))