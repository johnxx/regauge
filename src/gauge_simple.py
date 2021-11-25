from gauge import Gauge
from stream_spec import StreamSpec

class SimpleGauge(Gauge):
    def __init__(self, options, data) -> None:
        self.stream_spec = StreamSpec(**options['stream_spec'])

        gauge_face_class = __import__(options['gauge_face']['type'])
        options['gauge_face']['stream_spec'] = self.stream_spec
        self.face = gauge_face_class(options['gauge_face'])

        self.data = data
        
    def subscribed_streams(self):
        return set(self.stream_spec.field_spec)
    
    def stream_updated(self, field_spec):
        if self.stream_spec.field_spec == field_spec:
            self.face.value = int(self.data['field_spec'] * self.stream_spec.units['conversion_factor'])

    def update(self):
        self.face.update()