from gauge_face import GaugeFace
import displayio
import math

class Face(GaugeFace):
    default_options = {}

    def __init__(self, stream_spec, options, resources) -> None:
        self.stream_spec = stream_spec
        self.options = self._apply_defaults(options)
        self.resources = resources
        display_group = resources['display_group']

        self.seg_x_y = 4
        self.seg_margin = 2
        self.seg_total = self.seg_x_y + self.seg_margin
        self.num_segments = 24
        self.display_group_width = 240
        fg_display_group = displayio.Group()
        bg_display_group = displayio.Group()
        display_group.append(bg_display_group)
        display_group.append(fg_display_group)
        self.stream_spec = stream_spec
        self.display_group = fg_display_group
        self._values = bytearray(math.floor(self.display_group_width/self.seg_total))
        self.idx = 0
        self.value = stream_spec.min_val

        point_palette = displayio.Palette(4)
        point_palette[0] = 0x000000
        # Really nice blue
        point_palette[1] = 0x0099DD
        point_palette[2] = 0xCCCC33
        point_palette[3] = 0x222222
        self.palette = point_palette

        cell_bg = displayio.Bitmap(self.seg_x_y, self.seg_x_y, 3)
        cell_bg.fill(3)
        self.sprite_bg = displayio.Bitmap(self.seg_total, self.seg_total, 3)
        self.sprite_bg.blit(1, 1, cell_bg, x1=0, y1=0, x2=3, y2=3)

        cell_fg = displayio.Bitmap(self.seg_x_y, self.seg_x_y, 3)
        self.sprite = displayio.Bitmap(self.seg_total, self.seg_total, 3)
        cell_fg.fill(1)
        self.sprite.blit(1, 1, cell_fg, x1=0, y1=0, x2=3, y2=3)

        cell_top = displayio.Bitmap(self.seg_x_y, self.seg_x_y, 3)
        cell_top.fill(2)
        self.sprite_top = displayio.Bitmap(self.seg_total, self.seg_total, 3)
        self.sprite_top.blit(1, 1, cell_top, x1=0, y1=0, x2=3, y2=3)

        for n in range(0, len(self._values)):
            bg = displayio.TileGrid(bitmap=self.sprite_bg, height=self.num_segments, pixel_shader=self.palette, x=n*self.seg_total, y=0)
            bg_display_group.append(bg)

            zero_pixel = displayio.TileGrid(bitmap=self.sprite_top, height=self.num_segments, pixel_shader=self.palette, x=0, y=0)
            self.display_group.append(zero_pixel)

        self.update()
    
    def calc_bounding_box(self):
        return ((0,0), (240, 120))

    @property
    def value(self):
        return self._values[self.idx]

    @value.setter
    def value(self, value):
        self.idx += 1
        if self.idx > len(self._values)-1:
            self.idx = 0
        if value <= self.stream_spec.max_val and value >= self.stream_spec.min_val:
            self._values[self.idx] = value
        

    @staticmethod
    def format_value(fmt, val):
        return fmt.format(val)
    
    def vert_map(self, idx):
        return self.num_segments - math.floor(((self._values[idx] - self.stream_spec.min_val) / self.stream_spec.max_val) * self.num_segments)

    def update(self):
        # Hack to make this scroll when it's always getting the same value
        self.value = self._values[self.idx]

        for n in range(0, len(self._values)):
            idx = self.idx - n
            if idx < 0:
                idx = len(self._values) + idx
            seg_num = self.vert_map(idx)
            y = seg_num*self.seg_total
            graph_pixel = displayio.TileGrid(bitmap=self.sprite, height=self.num_segments-seg_num, width=1, pixel_shader=self.palette, x=self.display_group_width-self.seg_total*n, y=y)
            # print("Displaying value: {} as {} at {}x{}".format(self._values[idx], seg_num, graph_pixel.x, graph_pixel.y))
            self.display_group[n] = graph_pixel