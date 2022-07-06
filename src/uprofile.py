import json
import math
import time

# Once at import time
enabled = False
stats = {}
time_ref = {
    'now': None
}

def print_stats(stats):
    for group_name, group_stats in stats.items():
        if group_stats['total_calls'] == 0:
            continue
        print("{}:".format(group_name))
        print("  Time: {}".format(group_stats['total_time']))
        print("  Calls: {}".format(group_stats['total_calls']))
        print("  Average: {}".format(group_stats['total_time'] / group_stats['total_calls']))
        for name_name, name_stats in group_stats['children'].items():
            if name_stats['total_calls'] == 0:
                continue
            print("  {}:".format(name_name))
            print("    Time: {}".format(name_stats['total_time']))
            print("    Calls: {}".format(name_stats['total_calls']))
            print("    Average: {}".format(name_stats['total_time'] / name_stats['total_calls']))
            
        stats[group_name]['total_time'] = 0
        stats[group_name]['total_calls'] = 0
        stats[group_name]['children'] = {}


def profile(group, name):
    # Once at the time the decorator is applied
    if enabled:
        if group not in stats:
            stats[group] = {
                "total_time": 0,
                "total_calls": 0,
                "children": {}
            }
        sample = {}
        def profile_real(func):
            def wrap(*args, **kwargs):
                # Every time the decorated function is called
                cur_sec = math.floor(time.monotonic())
                if not time_ref['now']:
                    time_ref['now'] = cur_sec
                if time_ref['now'] != cur_sec:
                    print(chr(27) + "[H" + chr(27) + "[J")
                    print("@{}".format(time_ref['now']))
                    print("=" * 40)
                    print_stats(stats)

                    time_ref['now'] = cur_sec
                started = time.monotonic()
                result = func(*args, **kwargs)
                total = time.monotonic() - started
                if name not in stats[group]['children']:
                    stats[group]['children'][name] = {
                        'total_time': total,
                        'total_calls': 1,
                        'average_time': total,
                    }
                else:
                    stats[group]['children'][name]['total_time'] += total
                    stats[group]['children'][name]['total_calls'] += 1
                stats[group]['total_time'] += total
                stats[group]['total_calls'] += 1
                return result
            return wrap
        return profile_real
    else:
        def profile_fake(func):
            return func
        return profile_fake
