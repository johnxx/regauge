import asynccp
import asynccp.time as Duration
import board
import displayio
import neopixel_slice
from my_globals import config, data, resources
from passy import Passy

debug = True
def print_dbg(some_string, **kwargs):
    if debug:
        return print(some_string, **kwargs)

def initialize_gauges(gauges, resources):
    gauge_tasks = []
    for gauge_name, gauge_options in gauges.items():
        gauge_options['name'] = gauge_name
        gauge_module = __import__('gauge_' + gauge_options['type'], None, None, [gauge_options['sub_type']])
        gauge_class = getattr(gauge_module, gauge_options['sub_type'])
        # gauge = gauge_class(gauge_options, resources, data)
        gauge_resources = {}
        for type, name in gauge_options['resources'].items():
            print_dbg("Assigned {} to Gauge {} as {}".format(name, gauge_options['sub_type'], type))
            gauge_resources[type] = resources[name]
        gauge = gauge_class(gauge_options, gauge_resources)
        if 'config_bus' in resources:
            resources['config_bus'].sub(gauge.config_updated, "config.gauges.{}".format(gauge_name))
        if 'data_bus' in resources:
            for field_spec in gauge.subscribed_streams():
                resources['data_bus'].sub(gauge.stream_updated, "data.{}".format(field_spec))
        gauge_tasks.append(asynccp.schedule(frequency=gauge.update_freq, coroutine_function=gauge.update))
    return gauge_tasks
            
def setup_tasks(config, resources, data):
    tasks = {
        'data_sources': {},
        'gauges': []
    }
    for data_source, options in config['data_sources'].items():
        if options['enabled']:
            options.pop('enabled')
            data_source_module = __import__('source_' + options['type'])
            del options['type']
            if 'config_source' in options and options['config_source']:
                data_source_class = getattr(data_source_module, 'ConfigSource')
                options.pop('config_source')
                resources['config_bus'] = Passy(task_manager=asynccp)
                data_source_obj = data_source_class(data_source, resources, config, **options)
            else:
                data_source_class = getattr(data_source_module, 'DataSource')
                resources['data_bus'] = Passy(task_manager=asynccp)
                data_source_obj = data_source_class(data_source, resources, data, **options)
            tasks['data_sources'][data_source] = asynccp.schedule(frequency=data_source_obj.poll_freq, coroutine_function=data_source_obj.poll)
    tasks['gauges'] = initialize_gauges(config['gauges'], resources)
    return tasks
        
def setup_hardware(hardware):
    resources = {}

    if hardware['wifi']['enabled']:
        wifi_cfg = hardware['wifi']
        import wifi
        import socketpool

        print_dbg("Connecting to {}".format(wifi_cfg['ssid']))
        wifi.radio.connect(wifi_cfg['ssid'], wifi_cfg['passphrase'])
        print_dbg("Connected! IP: {}".format(wifi.radio.ipv4_address))

        resources['socket_pool'] = socketpool.SocketPool(wifi.radio)
        
    if hardware['lcd']['enabled']:
        lcd_cfg = hardware['lcd']
        import displayio
        import gc9a01

        # Release any currently in-use displays for good measure
        displayio.release_displays()

        display_bus = displayio.FourWire(
            board.SPI(),
            command=getattr(board, lcd_cfg['pins']['dc']),
            chip_select=getattr(board, lcd_cfg['pins']['cs']),
            reset=getattr(board, lcd_cfg['pins']['rst'])
        )
        lcd = gc9a01.GC9A01(
            display_bus,
            width=lcd_cfg['width'],
            height=lcd_cfg['height'],
            backlight_pin=getattr(board, lcd_cfg['pins']['bl'])
        )
        main_context = displayio.Group()
        lcd.show(main_context)

        resources['lcd'] = {
            'hardware': lcd,
            'main_context': main_context,
            'width': lcd_cfg['width'],
            'height': lcd_cfg['height']
        }
        
    if hardware['leds']['enabled']:
        led_cfg = hardware['leds']
        import neopixel

        leds = neopixel.NeoPixel(
            getattr(board, led_cfg['pins']['data']),
            led_cfg['number'],
            brightness=led_cfg['brightness']
        )

        resources['leds'] = leds

    return resources


def allocate_resources(layout, resources):
    for name, config in layout.items():
        if config['type'] == 'neopixel_slice':
            if 'step' in config and config['step']:
                keys = range(
                    config['start'],
                    config['end'],
                    config['step']
                )
            else:
                keys = range(
                    config['start'],
                    config['end']
                )
            if 'reverse' in config and config['reverse']:
                keys = list(reversed(keys))
                
            resources[name] = neopixel_slice.NeoPixelSlice(
                resources[config['hw_resource']], 
                keys
            )
        elif config['type'] == 'display_group':
            resources[name] = displayio.Group(x=config['x_offset'], y=config['y_offset'])
            resources[config['hw_resource']]['main_context'].append(resources[name])
    return resources
            
    

if __name__ == '__main__':
    resources = setup_hardware(config['hardware'])
    resources = allocate_resources(config['layout'], resources)
    tasks = setup_tasks(config, resources, data)
    asynccp.run()