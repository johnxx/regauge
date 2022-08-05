from adafruit_bitmap_font import bitmap_font
from adafruit_display_shapes import line
from adafruit_display_text.label import Label
from gauge_face import GaugeFace
import displayio
import json
import math
import time
import uprofile

uprofile.enabled = True
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
        'graph_line_color': 0x0066AA,
        'top_line_color':0x666666, 
        'bottom_line_color':0x666666, 
        'fmt_string': "{:>3.0f}{}", 
        'label_offset_x': 120, 
        'label_offset_y': 60, 
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
        
        self.text_right = Label(font, text='', color=self.options['font_color'], scale=1,
                                anchor_point=(0, 0.5), anchored_position=(self.latest_x, self.last_y))
        self.display_group.append(self.text_right)


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

        self.width = 240
        self.height = 120
        
        self.margin_right = 45
        self.margin_top = 12
        self.margin_bottom = 40

        self.latest_x = self.width - self.margin_right
        self.last_x = 240
        self.last_y = 0
        
        self.time_window = 120
        self.dot_every = 2
        
        self.last_update = time.monotonic()
        self.latest_tstamp = self.last_update
        self.min_scroll = 2
        
        self.min_y = self.max_y = 0

        self._setup_display()


    @property
    def num_seg_y(self):
        return math.floor(self.height / self.seg_y)

    def pick_y(self, v):
        as_pct = (v - self.ts.stream_spec.min_val) / self.ts.stream_spec.max_val
        # print("Showing value {} as pct {}".format(v, as_pct))
        return (self.height - math.floor(as_pct*(self.height-self.margin_bottom-self.margin_top)))-self.margin_bottom

    # no margins
    # def pick_y(self, v):
    #     return self.height - math.floor(((v - self.stream_spec.min_val) / self.stream_spec.max_val)*self.num_seg_y*self.seg_y)

    def time_to_px(self, t):
        return (abs(t) / self.time_window) * self.width

    def update(self):
        # self._trim_sprites(self.lines)
        # self._trim_sprites(self.dots)
            
        t_now = time.monotonic()
        scroll_x =  math.floor(self.time_to_px(t_now - self.last_update))
        if scroll_x < self.min_scroll:
            print_dbg("Wanted to scroll {}px. We passed instead.".format(scroll_x))
            return
        print_dbg("Scrolling {} ({}s)".format(scroll_x, t_now - self.last_update))
        for s in self.lines:
            s.x -= scroll_x
            if s.x < 0:
                # print("Removed line at {}x{}".format(s.x, s.y))
                self.lines.remove(s)
        for s in self.dots:
            s.x -= scroll_x
            if s.x < 0:
                print_dbg("Removed dot at {}x{}".format(s.x, s.y))
                self.dots.remove(s)
        self.last_x -= scroll_x
        if t_now - self.latest_tstamp > self.dot_every:
            new_pairs = self.ts.since(self.latest_tstamp)
            if len(new_pairs) > 0:
                print_dbg("Collected {} values over {} seconds".format(len(new_pairs), t_now - self.latest_tstamp))
                uprofile.start_segment('line_graph', 'new_dots_n_lines')
                total = 0
                for i, v in enumerate(new_pairs):
                    if v[0] > self.latest_tstamp:
                        self.latest_tstamp = v[0]
                    total += v[1]
                avg = total / len(new_pairs)

                x = self.latest_x
                y = self.pick_y(avg)
                # print_dbg("{} -> {}".format(v, y))
                # print_dbg("Drawing {}, {} to {}x{}".format(i, v[1], x, y))
                graph_pixel = displayio.TileGrid(bitmap=self.sprite, height=1, width=1, pixel_shader=self.palette, x=x, y=y)
                self.dots.append(graph_pixel)
                # print_dbg("Connecting {}, {} to {}, {}".format(self.last_x, self.last_y, x, y))
                line_conn = line.Line(x0=self.last_x, y0=self.last_y, x1=x, y1=y, color=self.palette[0])
                self.lines.append(line_conn)

                self.text_right.text = self.options['fmt_string'].format(avg, self.ts.stream_spec.units['suffix']) 
                new_avg = (self.text_right.anchored_position[0], y)
                self.text_right.anchored_position = new_avg

                self.last_x = x
                self.last_y = y

                uprofile.end_segment('line_graph', 'new_dots_n_lines')
        uprofile.start_segment('line_graph', 'the_rest')

        min_y = self.pick_y(self.ts.min_val)
        max_y = self.pick_y(self.ts.max_val)
        if self.min_y != min_y or self.max_y != max_y:
            
            self.bottom_line.y = min_y
            self.text_bottom.text = self.options['fmt_string'].format(self.ts.min_val, self.ts.stream_spec.units['suffix'])
            new_min = (self.text_bottom.anchored_position[0], min_y)
            self.text_bottom.anchored_position = new_min

            self.top_line.y = max_y
            self.text_top.text = self.options['fmt_string'].format(self.ts.max_val, self.ts.stream_spec.units['suffix'])
            new_max = (self.text_top.anchored_position[0], max_y)
            self.text_top.anchored_position = new_max

            self.min_y = min_y
            self.max_y = max_y
        self.last_update = t_now
        uprofile.end_segment('line_graph', 'the_rest')
