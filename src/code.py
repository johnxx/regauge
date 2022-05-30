import asynccp
import asynccp.time as Duration
import board
import displayio
import json
import neopixel_slice
import time
#from data import data
from adafruit_bitmap_font import bitmap_font
from adafruit_display_shapes import line
from adafruit_display_text.label import Label
from passy import Passy

DISPLAY_GROUP = 0
NEOPIXEL_SLICE = 1

LINE_GRAPH = 0
TEXT = 1
MULTI_LED = 2

instrumentation = False
debug = False
def print_dbg(some_string, **kwargs):
    if debug:
        return print(some_string, **kwargs)

def initialize_gauges(layout, resources):
    gauge_tasks = []
    for block in layout:
        # @TODO: Deprecated settings. May return in another form at some point in the future
        block['type'] = 'simple'
        block['sub_type'] = 'SimpleGauge'

        resource_config = block['resource']
        gauge_resources = {}
        if resource_config['ofType'] == NEOPIXEL_SLICE:
            if 'step' in resource_config and resource_config['step']:
                keys = range(
                    resource_config['start'],
                    resource_config['end'],
                    resource_config['step']
                )
            else:
                keys = range(
                    resource_config['start'],
                    resource_config['end']
                )
            if 'reverse' in resource_config and resource_config['reverse']:
                keys = list(reversed(keys))
                
            gauge_resource = neopixel_slice.NeoPixelSlice(
                resources[resource_config['hw_resource']], 
                keys
            )
            gauge_resources['leds]'] = gauge_resource
        elif resource_config['ofType'] == DISPLAY_GROUP:
            gauge_resource = displayio.Group(x=resource_config['x_offset'], y=resource_config['y_offset'])
            resources[resource_config['hw_resource']]['main_context'].append(gauge_resource)
            gauge_resources['display_group]'] = gauge_resource


        gauge_module = __import__('gauges.' + block['type'], None, None, [block['sub_type']])
        gauge_class = getattr(gauge_module, block['sub_type'])
        # gauge = gauge_class(gauge_options, resources, data)
        gauge = gauge_class(block, gauge_resources)
        if 'config_bus' in resources:
            resources['config_bus'].sub(gauge.config_updated, "config.gauges.{}".format(block['name']))
        if 'data_bus' in resources:
            for field_spec in gauge.subscribed_streams:
                resources['data_bus'].sub(gauge.stream_updated, "data.{}".format(field_spec))
        print("{}: {}Hz".format(block['name'], gauge.update_freq))
        gauge_tasks.append(asynccp.schedule(frequency=gauge.update_freq, coroutine_function=gauge.update))
    return gauge_tasks
            
def setup_tasks(config, resources):
    tasks = {
        'data_sources': {},
        'gauges': [],
    }
    for data_source, options in config['data_sources'].items():
        if 'type' not in options:
            if data_source == 'config_listener':
                options['type'] = 'http_ampule'
                options['config_source'] = True
            elif data_source == 'data_listener':
                options['type'] = 'tcp_msgpack'
            elif data_source == 'data_can':
                options['type'] = 'canbus'
            else:
                print("Failed to infer type for {}".format(data_source))
        if 'enabled' not in options:
            options['enabled'] = True
        if options['enabled']:
            options.pop('enabled')
            print("Loading: {}".format('sources.' + options['type']))
            data_source_module = __import__('sources.' + options['type'])
            if 'config_source' in options and options['config_source']:
                data_source_class = getattr(data_source_module, options['type']).ConfigSource
                del options['type']
                options.pop('config_source')
                resources['config_bus'] = Passy(task_manager=asynccp)
                data_source_obj = data_source_class(data_source, resources, config, **options)
            else:
                data_source_class = getattr(data_source_module, options['type']).DataSource
                del options['type']
                resources['data_bus'] = Passy(task_manager=asynccp)
                data_source_obj = data_source_class(data_source, resources, **options)
            tasks['data_sources'][data_source] = asynccp.schedule(frequency=data_source_obj.poll_freq, coroutine_function=data_source_obj.poll)
    tasks['gauges'] = initialize_gauges(config['layout'], resources)
    return tasks
        
def setup_hardware(hardware):
    resources = {}

    if hardware['can']['enabled']:
        can_cfg = hardware['can']
        import canio
        import digitalio
        if hasattr(board, 'CAN_STANDBY'):
            standby = digitalio.DigitalInOut(board.CAN_STANDBY)
            standby.switch_to_output(False)
         
        # If the CAN transceiver is powered by a boost converter, turn on its supply
        if hasattr(board, 'BOOST_ENABLE'):
            boost_enable = digitalio.DigitalInOut(board.BOOST_ENABLE)
            boost_enable.switch_to_output(True)
         
        rx_pin = getattr(board, can_cfg['pins']['rx'])
        tx_pin = getattr(board, can_cfg['pins']['tx'])
        resources['can'] = canio.CAN(rx=rx_pin, tx=tx_pin, baudrate=can_cfg['bit_rate'], auto_restart=True)

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

        spi = board.SPI()
        while not spi.try_lock():
            pass
        # spi.configure(baudrate=24000000) # Configure SPI for 24MHz
        spi.configure(baudrate=80000000) # Configure SPI for 24MHz
        spi.unlock()

        # Release any currently in-use displays for good measure
        displayio.release_displays()

        display_bus = displayio.FourWire(
            spi,
            command=getattr(board, lcd_cfg['pins']['dc']),
            chip_select=getattr(board, lcd_cfg['pins']['cs']),
            reset=getattr(board, lcd_cfg['pins']['rst'])
        )
        lcd = gc9a01.GC9A01(
            display_bus,
            width=lcd_cfg['width'],
            height=lcd_cfg['height'],
            auto_refresh=False,
            backlight_pin=getattr(board, lcd_cfg['pins']['bl'])
        )
        async def lcd_update():
            if instrumentation:
                start_time = time.monotonic()
            lcd.refresh()
            if instrumentation:
                end_time = time.monotonic()
                total = end_time - start_time
                print("{} took {}s".format('lcd refresh', total))


        if not lcd.auto_refresh:
            global_framerate = 30
            display_update = asynccp.schedule(frequency=global_framerate, coroutine_function=lcd_update)
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

        if 'order' in led_cfg and led_cfg['order'] == 'GRBW':
            order = neopixel.GRBW
        else:
            order = neopixel.GRB
        
        leds = neopixel.NeoPixel(
            getattr(board, led_cfg['pins']['data']),
            led_cfg['number'],
            brightness=led_cfg['brightness'],
            pixel_order=order
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

    # @TODO: Overlay HACK!
    # overlay_color = 0x0099FF

    # overlay = displayio.Group()
    # resources[config['hw_resource']]['main_context'].append(overlay)
    # mid_line = line.Line(x0=0, y0=120, x1=240, y1=120, color=overlay_color)
    # overlay.append(mid_line)

    # font_name = 'Cloude_Regular_Bold_1.02-32.bdf'
    # font = bitmap_font.load_font("/share/fonts/" + font_name)

    # text_top = Label(font, text='Coolant', color=overlay_color, scale=1, anchor_point=(0, 1), anchored_position=(10, 120))
    # overlay.append(text_top)

    # text_bottom = Label(font, text='Oil Pressure', color=overlay_color, scale=1, anchor_point=(1, 0), anchored_position=(230, 120))
    # overlay.append(text_bottom)

    # bottom_line = line.Line(x0=0, y0=225, x1=240, y1=225, color=overlay_color)
    # overlay.append(bottom_line)

    # leds_text_bottom = Label(font, text='RPM', color=overlay_color, scale=1, anchor_point=(0.5, 1), anchored_position=(120, 235))
    # overlay.append(leds_text_bottom)

    # top_line = line.Line(x0=0, y0=15, x1=240, y1=15, color=overlay_color)
    # overlay.append(top_line)

    # leds_text_top = Label(font, text='AFR', color=overlay_color, scale=1, anchor_point=(0.5, 0), anchored_position=(120, 5))
    # overlay.append(leds_text_top)

    return resources
            
    

if __name__ == '__main__':
    fp = open('config.json', 'r')
    config = json.load(fp)
    # config = j['config']
    resources = setup_hardware(config['hardware'])
    # resources = allocate_resources(config['layout'], resources)
    tasks = setup_tasks(config, resources)
    asynccp.run()