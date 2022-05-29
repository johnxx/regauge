hardware = {
    'wifi': {
        'enabled': True,
        'ssid': 'SomethingClever',
        'passphrase': '<redacted>'
    },
    'lcd': {
        'enabled': True,
        'width': 240,
        'height': 240,
        'pins': {
            'cs': 'D20',
            'dc': 'D21',
            'rst': 'D10',
            'bl': 'D11',
        }
    },
    'leds': {
        'enabled': True,
        'number': 16,
        'brightness': 0.01,
        'pins': {
            'data': 'D16'
        }
    }
    
}

data_sources = {
    'config_listener': {
        'type': 'http_json',
        'enabled': True,
        'bind_addr': '0.0.0.0',
        'listen_port': 80,
        'config_source': True

    },
    'data_listener': {
        'type': 'tcp_msgpack',
        'enabled': False,
        'bind_addr': '0.0.0.0',
        'listen_port': 4557,
        'poll_freq': 10
    },
    'data_mock': {
        'type': 'mock',
        'poll_freq': 30,
        'send_frame_ids': [0x999],
        'enabled': True,
    },
}

gauges = {
    "fan_speed_leds": {
        'type': 'simple',
        'sub_type': 'SimpleGauge',
        'update_freq': 5,
        'resources': {
            'leds': 'right_leds_ccw'
        },
        'stream_spec': {
            'field_spec': 'fan_rpm',
            'min_val': 0,
            'max_val': 6000
        },
        'gauge_face': {
            'type': 'multi_led',
            'normal_color': 0x0000ff,
            'warning_level': 9999,
            'critical_level': 9999
        }

    },
    "cpu_temp_leds": {
        'type': 'simple',
        'sub_type': 'SimpleGauge',
        'update_freq': 5,
        'resources': {
            'leds': 'left_leds_cw'
        },
        'stream_spec': {
            'field_spec': 'cputemp_cel',
            'min_val': 0,
            'max_val': 100
        },
        'gauge_face': {
            'type': 'multi_led',
            'normal_color': 0xff0000,
            'warning_level': 999,
            'critical_level': 999
        }

    },
    "mem_graph": {
        'type': 'simple',
        'sub_type': 'SimpleGauge',
        'update_freq': 3,
        'resources': {
            'display_group': 'lcd_bottom'
        },
        'stream_spec': {
            'field_spec': 'mem_pct',
            'min_val': 0,
            'max_val': 100
        },
        'gauge_face': {
            'type': 'text'
        }
    },
    "cpu_lcd": {
        'type': 'simple',
        'sub_type': 'SimpleGauge',
        'update_freq': 30,
        'resources': {
            'display_group': 'lcd_top'
        },
        'stream_spec': {
            'field_spec': 'cpu_pct',
            'min_val': 0,
            'max_val': 199
        },
        'gauge_face': {
            'type': 'line_graph'
        }
    }
}

layout = {
    'lcd_top': {
        'type': 'display_group',
        'hw_resource': 'lcd',
        'x_offset': 0,
        'y_offset': 0
    },
    'lcd_bottom': {
        'type': 'display_group',
        'hw_resource': 'lcd', 
        'x_offset': 0,
        'y_offset': 120
    },
    'left_leds_cw': {
        'type': 'neopixel_slice',
        'hw_resource': 'leds',
        'start': 8,
        'end': 16,
        'reverse': True
    },
    'right_leds_ccw': {
        'type': 'neopixel_slice',
        'hw_resource': 'leds',
        'start': 0,
        'end': 8,
    }
}

config = {
    'hardware': hardware,
    'data_sources': data_sources,
    'gauges': gauges,
    'layout': layout
}

resources = {}
data = {}
