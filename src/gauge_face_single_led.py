class Face:

    def __init__(self, stream_spec=None, pixel=None, warning_level=0.75, critical_level=0.95, normal_color=0x00ff00, warning_color=0xffff00, critical_color=0xff0000) -> None:
        if not stream_spec or not pixel:
            raise ValueError("stream_spec and pixel are required")
        if pixel.n > 1:
            raise ValueError("We only want 1 NeoPixel")
        self.stream_spec = stream_spec
        self.pixel = pixel
        self.warning_level = warning_level
        self.critical_level = critical_level
        self.normal_color = normal_color
        self.warning_color = warning_color
        self.critical_color = critical_color

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value <= self.stream_spec.max_val and value >= self.stream_spec.min_val:
            self._value = value

    def _pick_color(self):
        if self.value > self.critical_level:
            return self.critical_color
        elif self.value > self.warning_level:
            return self.warning_color
        else:
            return self.normal_color

    def update(self):
       self.pixel[0] = self._pick_color 