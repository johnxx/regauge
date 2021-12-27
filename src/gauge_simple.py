from gauge import Gauge
from stream_spec import StreamSpec
import time

instrumentation = True

class SimpleGauge(Gauge):
    def __init__(self, options, resources) -> None:
        self.stream_spec = StreamSpec(**options['stream_spec'])
        self.options = options

        gauge_face_module = __import__('gauge_face_' + options['gauge_face']['type'])
        gauge_face_class = getattr(gauge_face_module, 'Face')
        self.face = gauge_face_class(self.stream_spec, options['gauge_face'], resources)
        
    def subscribed_streams(self):
        print("Will subscribe to {}".format(self.face.subscribed_streams))
        return self.face.subscribed_streams
    
    def stream_updated(self, updates):
        for topic, value in updates:
            (prefix, field_spec) = topic.split(".")
            if prefix == 'data' and self.stream_spec.field_spec == field_spec:
                self.face.value = int(value * self.stream_spec.units['conversion_factor'])

    async def update(self):
        if instrumentation:
            start_time = time.monotonic()
        self.face.update()
        if instrumentation:
            end_time = time.monotonic()
            total = end_time - start_time
            print("{} took {}s".format(self.options['name'], total))
        
    def config_updated(self, messages):
        try:
            self.face.config_updated(self.options['gauge_face'])
        except NotImplementedError as e:
            pass