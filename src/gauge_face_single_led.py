from gauge_face import GaugeFace
class Face(GaugeFace):
    
    default_options = {
        'warning_level': 0.75, 
        'critical_level': 0.95, 
        'normal_color': 0x00ff00,
        'warning_color': 0xffff00, 
        'critical_color': 0xff0000
    }

    def __init__(self, stream_spec, options, resources) -> None:
        if not stream_spec or not resources['leds']:
            raise ValueError("stream_spec is required")
        if not resources['leds'] or resources['leds'].n() != 1:
            raise ValueError("We need exactly 1 NeoPixel")

        self.stream_spec = stream_spec
        self.options = self._apply_defaults(options)
        self.resources = resources

        self._value = self.stream_spec.min_val

    def _pick_color(self):
        if self.value > self.options['critical_level']:
            return self.options['critical_color']
        elif self.value > self.options['warning_level']:
            return self.options['warning_color']
        else:
            return self.options['normal_color']

    def update(self):
        # print("Updating to show new value: {}".format(self.value))
        # print(self.options)
        self.resources['leds'][0] = self._pick_color()