import json
class Face:
    
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
        self.options = options
        for key, val in self.default_options.items():
            if key not in self.options:
                self.options[key] = val
        self.resources = resources

        self._value = self.stream_spec.min_val

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value <= self.stream_spec.max_val and value >= self.stream_spec.min_val:
            self._value = value

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
