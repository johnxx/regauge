from typing import Coroutine
import asynccp
import asynccp.time.Duration as Duration

debug = True
def print_dbg(**kwargs):
    if debug:
        return print(**kwargs)

hardware = {
    'wifi': {
        'enabled': True,
        'ssid': 'Pequod',
        'passphrase': 'Call me Ishy.'
    }
}
data_sources = {
    'http_msgpack': {
        'enabled': False,
        'bind_to': '0.0.0.0',
        'port': 80
    },
    'tcp_msgpack': {
        'enabled': True,
        'bind_to': '0.0.0.0',
        'port': 4557,
    }
}

gauges = [
    {
        'type': 'simple',
        'stream_spec': {
            'field_spec': 'cputemp_cel',
            'min_val': 0,
            'max_val': 100
        },
        'gauge_face': {
            'type': 'single_led',
            'pixel': 0
        }
    }
]

config = {
    'hardware': hardware,
    'data_sources': data_sources,
    'gauges': gauges
}

data = {}

def initialize_gauges(gauges, data):
    gauge_tasks = []
    for gauge_options in gauges:
        gauge_class = __import__('gauge_' + gauge_options['type'])
        gauge = gauge_class(gauge_options, data)
        for field_spec in gauge.subscribed_streams():
            if field_spec not in data:
                data[field_spec] = {
                    'subs': []
                }
            data[field_spec]['subs'].append(gauge.stream_updated)
        gauge_tasks.append(asynccp.schedule(frequency=gauge.update_freq, coroutine_function=gauge.update))
    return gauge_tasks
            
def setup_tasks(config, data):
    tasks = {
        'data_sources': {},
        'gauges': []
    }
    for data_source, options in config['data_sources'].items:
        if options['enabled']:
            data_source_class = __import__('source_' + data_source)
            data_source_obj = data_source_class(options, data)
            tasks['data_sources'][data_source] = asynccp.schedule(frequency=data_source_obj.receive_freq, coroutine_function=data_source_obj.receive)
    tasks['gauges'] = initialize_gauges(config['gauges'], data)
        
def setup_hardware(hardware):
    if hardware['wifi']['enabled']:
        wifi_cfg = hardware['wifi']
        import wifi
        print_dbg("Connecting to {}".format(wifi_cfg['ssid']))
        wifi.radio.connect(wifi_cfg['ssid'], wifi_cfg['passphrase'])
        print_dbg("Connected! IP: {}".format(wifi.radio.ipv4_address))

setup_hardware(config['hardware'])
tasks = setup_tasks(config, data)
asynccp.run()

