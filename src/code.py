import asynccp
import asynccp.time as Duration
import board
import displayio
import json
import neopixel_slice
import os
import time
import uprofile
#from data import data
from adafruit_bitmap_font import bitmap_font
from adafruit_display_shapes import line
from adafruit_display_text.label import Label
from passy import Passy

uprofile.enabled = False
instrumentation = False
debug = False
def print_dbg(some_string, **kwargs):
    if debug:
        return print(some_string, **kwargs)

def initialize_gauges(gauges, resources):
    gauge_tasks = []
    for gauge_name, block in gauges.items():
        # @TODO: Deprecated settings. May return in another form at some point in the future
        block['type'] = 'simple'
        block['sub_type'] = 'SimpleGauge'

        gauge_resources = {}
        for resource_config in block['resources']:
            if resource_config['type'] == 'neopixel_slice':
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
                    
                gauge_resource = neopixel_slice.NeoPixelSlice(resources['leds'], keys)
                gauge_resources['leds'] = gauge_resource
            elif resource_config['type'] == 'display_group':
                gauge_resource = displayio.Group(x=int(resource_config['x_offset']), y=int(resource_config['y_offset']))
                resources['lcd']['main_context'].append(gauge_resource)
                gauge_resources['display_group'] = gauge_resource
                gauge_resources['lcd'] = resources['lcd']
            else:
                print("Couldn't figure out resource type for gauge")
                break


        gauge_module = __import__('gauges.' + block['type'], None, None, [block['sub_type']])
        gauge_class = getattr(gauge_module, block['sub_type'])
        gauge = gauge_class(gauge_name, block, gauge_resources)
        if 'config_bus' in resources:
            print("{} subscribed to config.gauges.{}".format(gauge_name, gauge_name))
            resources['config_bus'].sub(gauge.config_updated, "config.gauges.{}".format(gauge_name))
        if 'data_bus' in resources:
            for field_spec in gauge.subscribed_streams:
                print("{} wants to subscribe to {}".format(gauge_name, field_spec))
                resources['data_bus'].sub(gauge.stream_updated, "data.{}".format(field_spec))
        print("{}: {}Hz".format(gauge_name, gauge.update_freq))
        gauge_tasks.append(asynccp.schedule(frequency=int(gauge.update_freq), coroutine_function=gauge.update))
    return gauge_tasks
            
def setup_tasks(config, resources):
    tasks = {
        'data_sources': {},
        'gauges': [],
    }
    msg_bus = None
    for data_source, options in config['data_sources'].items():
        if 'type' not in options:
            print("Failed to infer type for {}".format(data_source))
            raise Exception
        if 'enabled' not in options:
            print("Automatically enabled {}".format(data_source))
            options['enabled'] = True
        if options['enabled']:
            options.pop('enabled')
            print("Loading: {}".format('sources.' + options['type']))
            data_source_module = __import__('sources.' + options['type'])
            if 'config_source' in options and options['config_source']:
                data_source_class = getattr(data_source_module, options['type']).ConfigSource
                del options['type']
                options.pop('config_source')
                if 'config_bus' not in resources: 
                    if not msg_bus:
                        msg_bus = Passy(task_manager=asynccp)
                    resources['config_bus'] = msg_bus
                data_source_obj = data_source_class(data_source, resources, config, **options)
            else:
                data_source_class = getattr(data_source_module, options['type']).DataSource
                del options['type']
                if 'data_bus' not in resources:
                    if not msg_bus:
                        msg_bus = Passy(task_manager=asynccp)
                    resources['data_bus'] = msg_bus
                data_source_obj = data_source_class(data_source, resources, **options)
            tasks['data_sources'][data_source] = asynccp.schedule(frequency=data_source_obj.poll_freq, coroutine_function=data_source_obj.poll)
    tasks['gauges'] = initialize_gauges(config['gauges'], resources)
    return tasks
        
def setup_hardware(hardware):
    resources = {}

    if 'can' in hardware and hardware['can']['enabled']:
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
        
    if 'i2c' in hardware and hardware['i2c']['enabled']:
        import busio
        i2c_cfg = hardware['i2c']
        scl_pin = getattr(board, i2c_cfg['pins']['scl'])
        sda_pin = getattr(board, i2c_cfg['pins']['sda'])
        resources['i2c'] = busio.I2C(scl_pin, sda_pin, frequency=100000)

    if 'wifi' in hardware and hardware['wifi']['enabled']:
        wifi_cfg = hardware['wifi']
        import wifi
        import socketpool

        print("Connecting to {}".format(wifi_cfg['ssid']))
        wifi.radio.connect(wifi_cfg['ssid'], wifi_cfg['passphrase'])
        print("Connected! IP: {}".format(wifi.radio.ipv4_address))

        resources['socket_pool'] = socketpool.SocketPool(wifi.radio)
        
    if 'lcd' in hardware and hardware['lcd']['enabled']:
        lcd_cfg = hardware['lcd']
        import displayio
        import gc9a01

        spi = board.SPI()
        while not spi.try_lock():
            pass
        desired_baudrate = 80_000_000
        spi.configure(baudrate=desired_baudrate) # Configure SPI for 80MHz
        print("Asked for {}Hz. Got {}Hz".format(desired_baudrate, spi.frequency))
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
        main_context = displayio.Group()
        resources['lcd'] = {
            'hardware': lcd,
            'main_context': main_context,
            'width': lcd_cfg['width'],
            'height': lcd_cfg['height'],
            'dirty': False
        }
        @uprofile.profile('lcd', 'update')
        async def lcd_update():
            if instrumentation:
                start_time = time.monotonic()
            lcd.refresh()
            if instrumentation:
                end_time = time.monotonic()
                total = end_time - start_time
                if resources['lcd']['dirty'] == False:
                    print("{} wasted {}s".format('lcd refresh', total))
                else:
                    pass
                    # print("{} took {}s".format('lcd refresh', total))
            resources['lcd']['dirty'] = False


        if not lcd.auto_refresh:
            global_framerate = 15
            display_update = asynccp.schedule(frequency=global_framerate, coroutine_function=lcd_update)
        lcd.show(main_context)

        
    if 'leds' in hardware and hardware['leds']['enabled']:
        led_cfg = hardware['leds']
        import neopixel

        if 'order' in led_cfg and led_cfg['order'] == 'GRBW':
            order = neopixel.GRBW
        else:
            order = neopixel.GRB
        
        resources['leds'] = neopixel.NeoPixel(
            getattr(board, led_cfg['pins']['data']),
            led_cfg['number'],
            brightness=led_cfg['brightness'],
            pixel_order=order
        )

    return resources

def load_config(config_path='/config.d'):
    config = {}
    config_files = os.listdir(config_path)
    for section in ['hardware', 'data_sources', 'gauges']:
        config[section] = {}

        section_filename = section + ".json"
        if section_filename in config_files:
            section_path = '/'.join([config_path, section_filename])
            try:
                with open(section_path) as f:
                    print_dbg("Loaded {}".format(section_path))
                    config[section] = json.load(f)
            except:
                print_dbg(str(e))

        section_dir = section + ".d"
        if section_dir in config_files:
            section_path = '/'.join([config_path, section_dir])
            try:
                for file_name in os.listdir(section_path):
                    if not file_name.endswith('.json') or len(file_name) < 6:
                        continue
                    config_name = file_name.rsplit('.json', 1)[0]
                    with open('/'.join([section_path, file_name])) as f:
                        try:
                            config[section][config_name] = json.load(f)
                        except Exception as e:
                            print("Failed to load {}".format())
                            print_dbg(str(e))
            except:
                print_dbg(str(e))
    print_dbg(json.dumps(config))
    return config
    

if __name__ == '__main__':
    # Load the config
    config = load_config()
    # Setup hardware and return configured resources
    resources = setup_hardware(config['hardware'])
    # Schedule tasks like data_sources and gauges
    tasks = setup_tasks(config, resources)
    # Run the scheduled tasks in a loop
    asynccp.run()
