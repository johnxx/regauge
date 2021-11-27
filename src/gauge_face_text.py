from adafruit_display_text.label import Label
from adafruit_bitmap_font import bitmap_font
from gauge_face import GaugeFace

class Face(GaugeFace):

    default_options = {
        'font': 'LanterosySansSerif-liter-100.pcf',
        'font_color':0xCCCCCC, 
        'fmt_string': "{:>3.0f}", 
        'offset_x': 180, 
        'offset_y': 80, 
        'effects': []
        
    }

    def __init__(self, stream_spec, options, resources) -> None:
        # print(resources)
        # print(stream_spec)
        # if not stream_spec or not resources['display_group']:
        #     raise ValueError("stream_spec is required")

        self.options = self._apply_defaults(options)
        self.resources = resources
        self.stream_spec = stream_spec
        self._setup_display(options)
        self._value = self.stream_spec.min_val

        self.update()
    
    # @TODO: Next time!
    def config_updated(self, options):
        self.options = self._apply_defaults(options)
        self._setup_display()
    
    def _setup_display(self, options):
        font = bitmap_font.load_font("/share/fonts/" + self.options['font'])
        if 'lcd_bg' in self.options['effects']:
            if self.options['fmt_string'] == self.default_options['fmt_string']:
                self.options['fmt_string'] = "{:!>3.0f}"
            str_width = len(self.options.fmt_string.format(0))
            bg_str = '~' * str_width
            bg_text_area = Label(font, text=bg_str, color=0x222222, 
                                anchor_point=(1.0, 0.5), anchored_position=(self.options['offset_x'], self.options['offset_y']))
            self.resources['display_group'].append(bg_text_area)

        self.text_area = Label(font, text='', color=self.options['font_color'],
                                anchor_point=(1.0, 0.5), anchored_position=(self.options['offset_x'], self.options['offset_y']))
        self.resources['display_group'].append(self.text_area)
    
    def update(self):
        self.text_area.text = self.options['fmt_string'].format(self.value)