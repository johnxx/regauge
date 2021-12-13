from gauge import Gauge
from stream_spec import StreamSpec

class SimpleGauge(Gauge):
    def __init__(self, options, resources, data) -> None:
        self.stream_spec = StreamSpec(**options['stream_spec'])
        self.options = options

        gauge_face_module = __import__('gauge_face_' + options['gauge_face']['type'])
        gauge_face_class = getattr(gauge_face_module, 'Face')
        self.face = gauge_face_class(self.stream_spec, options['gauge_face'], resources)

        self.data = data
        
    def subscribed_streams(self):
        return [self.stream_spec.field_spec]
    
    def stream_updated(self, updates):
        for topic, value in updates:
            (prefix, field_spec) = topic.split(".")
            if prefix == 'data' and self.stream_spec.field_spec == field_spec:
                self.face.value = int(value * self.stream_spec.units['conversion_factor'])

    async def update(self):
        self.face.update()
        
    def config_updated(self, messages):
        try:
            self.face.config_updated(self.options['gauge_face'])
        except NotImplementedError as e:
            pass