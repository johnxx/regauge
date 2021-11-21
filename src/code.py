import asynccp

data_sources = {
    'http_msgpack': True,
    'tcp_msgpack': True
}

gauges = [
    {
        'stream_spec': {
            'field_spec': 'cputemp_cel',
            'min_val': 0,
            'max_val': 100
        },
        'gauge_face': {
            'type': 'led',
            'pixels': [0, 8],
            'order': 'reverse',
            'normal_level': 60,
            'warning_level': 80,
            'critical_level': 95
        }
    }
]