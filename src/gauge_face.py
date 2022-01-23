from my_globals import data
class GaugeFace:

    @property
    def subscribed_streams(self):
        return []

    @property
    def value(self):
        if hasattr(self, '_value'):
            return self._value
        elif self.stream_spec.field_spec in data:
            cf = self.stream_spec.units['conversion_factor']
            v = data[self.stream_spec.field_spec]['value'] * cf
            # print("Converting {}:{} with {}".format(self.stream_spec.field_spec, v, cf))
            if v > self.stream_spec.min_val and v < self.stream_spec.max_val:
                return v
        return self.stream_spec.min_val

    @value.setter
    def value(self, value):
        if value == None:
            del self._value
        elif value <= self.stream_spec.max_val and value >= self.stream_spec.min_val:
            # print("Set to {}".format(value))
            self._value = value

    def _apply_defaults(self, options):
        for key, val in self.default_options.items():
            if key not in options:
                options[key] = val
        return options

    def config_updated():
        pass
    
    def update():
        pass