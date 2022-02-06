import time

class TimeSeries():
    def __init__(self, stream_spec, upto_vals=1, retain_for_s=0) -> None:
        self.upto_vals = upto_vals
        self.retain_for_s = retain_for_s

        self.stream_spec = stream_spec
        self.min_val = self.max_val = self.stream_spec.min_val
        self.data = [(time.monotonic(), self.stream_spec.min_val)]

    @property
    def subscribed_streams(self):
        return [self.stream_spec.field_spec]

    def stream_updated(self, updates):
        tstamp = time.monotonic()
        for topic, value in updates:
            (prefix, field_spec) = topic.split(".")
            if prefix == 'data' and self.stream_spec.field_spec == field_spec:
                val = int(value * self.stream_spec.units['conversion_factor'])
                self.latest = (tstamp, val)

    @property
    def value(self):
        print("Will return: {}".format(self.data[-1][1]))
        return self.data[-1][1]
    
    @property
    def latest(self):
        return self.data[-1]

    @latest.setter
    def latest(self, tstamp_val):
        if tstamp_val[1] > self.stream_spec.max_val:
            tstamp_val = (tstamp_val[0], self.stream_spec.max_val)
        elif tstamp_val[1] < self.stream_spec.min_val:
            tstamp_val = (tstamp_val[0], self.stream_spec.min_val)
        self.data.append(tstamp_val)
        self.trim()
        self.update_aggregates(tstamp_val[1])
                
    def trim(self):
        cur_time = time.monotonic()
        if len(self.data) > self.upto_vals:
            del self.data[:-self.upto_vals]
        if self.retain_for_s > 0:
            for n, v in enumerate(self.data):
                if v[0] < cur_time - self.retain_for_s:
                    del self.data[n]
                else:
                    break

    def update_aggregates(self, value):
        if value < self.min_value:
            self.min_value = value
        elif value > self.max_value:
            self.max_value = value

                
    def since(self, tstamp):
        return [self.data[i] for i, _ in enumerate(self.data) if self.data[i][0] > tstamp]