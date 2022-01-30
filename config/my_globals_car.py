hardware = {
    'wifi': {
        'enabled': False,
        'ssid': 'SomethingClever',
        'passphrase': '<redacted>'
    },
    'lcd': {
        'enabled': True,
        'width': 240,
        'height': 240,
        'pins': {
            'cs': 'D9',
            'dc': 'D18',
            'rst': 'D19',
            'bl': 'D6',
        }
    },
    'leds': {
        'enabled': True,
        'number': 16,
        'order': 'GRBW',
        'brightness': 0.01,
        'pins': {
            'data': 'D20'
        }
    }
    
}

data_sources = {
    'config_listener': {
        'type': 'http_json',
        'enabled': False,
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
        'enabled': True,
    },
    'data_uart': {
        'type': 'uart',
        'poll_freq': 60,
        'enabled': False,
    }
}

gauges = {
    "afr_leds": {
        'type': 'simple',
        'sub_type': 'SimpleGauge',
        'update_freq': 15,
        'resources': {
            'leds': 'right_leds_ccw'
        },
        'stream_spec': {
            'field_spec': 'o2_lambda',
            'min_val': 0.7,
            'max_val': 1.3
        },
        'gauge_face': {
            'type': 'multi_led',
            'normal_color': 0x00FFFF,
            'warning_color': 0xFF00FF,
            'warning_level': 1.05,
            'critical_level': 1.1
        }

    },
    "rpm_leds": {
        'type': 'simple',
        'sub_type': 'SimpleGauge',
        'update_freq': 15,
        'resources': {
            'leds': 'left_leds_cw'
        },
        'stream_spec': {
            'field_spec': 'eng_rpm',
            'min_val': 0,
            'max_val': 7500
        },
        'gauge_face': {
            'type': 'multi_led',
            'warning_level': 6000,
            'critical_level': 7000
        }

    },
    "oil_graph": {
        'type': 'simple',
        'sub_type': 'SimpleGauge',
        'update_freq': 30,
        'resources': {
            'display_group': 'lcd_bottom'
        },
        'stream_spec': {
            'field_spec': 'oilpres_psi',
            'units': 'emu_oilpres',
            'min_val': 0,
            'max_val': 115
        },
        'gauge_face': {
            'type': 'line_graph'
        }
    },
    "clt_lcd": {
        'type': 'simple',
        'sub_type': 'SimpleGauge',
        'update_freq': 2,
        'resources': {
            'display_group': 'lcd_top'
        },
        'stream_spec': {
            'field_spec': 'clt_cel',
            'min_val': 0,
            'max_val': 160
        },
        'gauge_face': {
            'type': 'text'
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
        'start': 0,
        'end': 8,
    },
    'right_leds_ccw': {
        'type': 'neopixel_slice',
        'hw_resource': 'leds',
        'start': 8,
        'end': 16,
        'reverse': True
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
