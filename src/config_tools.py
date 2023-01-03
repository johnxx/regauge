def merge(a, b, path=None, notifier=None, debug_below=False):
    "merges b into a"
    if path is None: path = []
    # print_dbg("Merging: {}".format(json.dumps(path)))
    if debug_below: 
        print(json.dumps(a))
        print(json.dumps(b))
    for key in b:
        topic = "config." + ".".join(path + [key])
        print("Topic: {}".format(topic))
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                if debug_below: print("0")
                merge(a[key], b[key], path + [str(key)], notifier, debug_below=debug_below)
            elif a[key] == b[key]:
                if debug_below: print("1")
                pass # same leaf value
            elif isinstance(a[key], list) and isinstance(b[key], list):
                if debug_below: print("A")
                a_names = {}
                for idx_a, el_a in enumerate(a[key]):
                    if 'name' not in el_a:
                        continue
                    if debug_below: print("B-")
                    # print(str(idx_a))
                    # print(el_a)
                    print("We already have {}".format(el_a['name']))
                    # @TODO: We're not sending the right thing from the client
                    if debug_below: print("B")
                    a_names[el_a['name']] = idx_a
                    if debug_below: print("B+")
                for idx_b, el_b in enumerate(b[key]):
                    if debug_below: print("C")
                    if 'name' not in el_b:
                        continue
                    if el_b['name'] in a_names:
                        print("Got an update for  {}".format(el_b['name']))
                        idx_a = a_names[el_b['name']]
                        if debug_below: print("D")
                        # merge(el_a, el_b, path + [str(key)] + [str(el_a['name'])], notifier, debug_below=debug_below)
                        merge(a[key][idx_a], el_b, path + [str(key)] + [str(el_b['name'])], notifier, debug_below=debug_below)
                    else:
                        print("This is gonna break :(")
                        if debug_below: print("E")
                        a[key] + el_b
                        if debug_below: print("F")
                        if notifier:
                            print("Notify (A): {}.{}.{}: {}".format(path, str(key), str(el_a['name']), el_b))
                            notifier(path + [str(key)] + [str(el_a['name'])], el_b)
            else:
                if debug_below: print("2")
                a[key] = b[key]
                if notifier:
                    print("Notify (B): {}: {}".format(topic, a[key]))
                    notifier(topic, a[key])
        else:
            if debug_below: print("3")
            a[key] = b[key]
            if notifier:
                print("Notify (C): {}: {}".format(topic, a[key]))
                notifier(topic, a[key])
    if debug_below: print("Up!")
    return a
