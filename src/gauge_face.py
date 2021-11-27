class GaugeFace:
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value <= self.stream_spec.max_val and value >= self.stream_spec.min_val:
            self._value = value

    def _apply_defaults(self, options):
        for key, val in self.default_options.items():
            if key not in options:
                options[key] = val
        return options

    def config_updated():
        pass