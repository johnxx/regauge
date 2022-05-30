from gauge import Gauge
from stream_spec import StreamSpec
from timeseries import TimeSeries
import json
import time

LINE_GRAPH = "0"
TEXT = "1"
MULTI_LED = "2"

instrumentation = False
instrumentation_ts = False

class SimpleGauge(Gauge):
    def __init__(self, options, resources) -> None:
        self.stream_spec = StreamSpec(**options['stream_spec'])
        self.ts = TimeSeries(stream_spec=self.stream_spec, **options['time_series'])
        self.options = options
        # @TODO: Looks like we're not setting 'type' 
        if 'type' not in options['gauge_face']:
            if options['gauge_face']['ofType'] == LINE_GRAPH:
                options['gauge_face']['type'] = 'line_graph'
            elif options['gauge_face']['ofType'] == TEXT:
                options['gauge_face']['type'] = 'text'
            elif options['gauge_face']['ofType'] == MULTI_LED:
                options['gauge_face']['type'] = 'multi_led'
        gauge_face_module = __import__('gauges.faces.' + options['gauge_face']['type'])
        gauge_face_class = getattr(gauge_face_module.faces, options['gauge_face']['type']).Face
        self.face = gauge_face_class(self.ts, options['gauge_face'], resources)
        
    @property
    def subscribed_streams(self):
        return self.ts.subscribed_streams
    
    def stream_updated(self, updates):
        if instrumentation_ts and instrumentation_ts == self.options['name']:
            start_time = time.monotonic()
        self.ts.stream_updated(updates)
        if instrumentation_ts and instrumentation_ts == self.options['name']:
            end_time = time.monotonic()
            total = end_time - start_time
            print("{} took {}s".format(self.options['name'], total))

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