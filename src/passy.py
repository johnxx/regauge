#!/usr/bin/env python3

class Passy():
    def __init__(self) -> None:
        self.subscriptions = {}
        self.subscribers = {}
        self.outbox = {}
        
    def sub(self, subscriber, topic_pref):
        sub_id = str(id(subscriber))
        self.subscribers[sub_id] = subscriber
        if sub_id not in self.subscriptions:
            self.subscriptions[sub_id] = set()
        self.subscriptions[sub_id].add(topic_pref)
        return (sub_id, topic_pref)

    def pub(self, topic, msg, auto_send=True):
        for sub_id, topic_prefs in self.subscriptions.items():
            for topic_pref in topic_prefs:
                if topic.startswith(topic_pref):
                    if sub_id not in self.outbox:
                        self.outbox[sub_id] = []
                    self.outbox[sub_id].append((topic, msg))
                    if auto_send:
                        self.send(sub_id)

    def send(self, sub_id):
        if sub_id in self.outbox and self.outbox[sub_id]:
            print("Sending {} messages to {}".format(len(self.outbox[sub_id]), sub_id))
            self.subscribers[sub_id](self.outbox[sub_id])
            self.outbox[sub_id] = []

    def send_all(self):
        print("Sending all events!")
        for sub_id in self.outbox:
            self.send(sub_id)

    def unsub(self, sub_id, topic_pref):
        # sub_id = str(id(subscriber))
        print("{} wants to unsubscribe from {}".format(sub_id, topic_pref))
        # print(self.subscribers)
        if sub_id in self.subscriptions:
            if topic_pref in self.subscriptions[sub_id]:
                print("{} unsubsribed from {}".format(sub_id, topic_pref))
                self.subscriptions[sub_id].remove(topic_pref)
                if not self.subscriptions[sub_id]:
                    print("{} has no more subscriptions".format(sub_id))
                    del(self.subscriptions[sub_id])

class ExampleSub():
    suffixes = ['licious', 'ahol', 'tank']


    def __init__(self, name, subscriptions) -> None:
        self.name = name
        self.subs = []
        for sub in subscriptions:
           self.subs.append(p.sub(self.receive, sub))
    
    def receive(self, events):
        print("Got {} events".format(len(events)))
        for event in events:
            (topic, msg) = event
            print("{} received {}: {}".format(self.name, topic, msg))

    def unsub_all(self):
        for s in self.subs:
            p.unsub(*s)

    def honk(self, auto=True):
        for suf in self.suffixes:
            p.pub(self.name + suf, 'honk', auto)

    def __del__(self):
        pass

if __name__ == '__main__':
    p = Passy()
    objs = [
        ExampleSub('foo', ['bar', 'baz']),
        ExampleSub('bar', ['foolicious', 'baz']),
        ExampleSub('baz', ['barahol', 'footank'])
    ]

    # Send immediately (auto-by-default)
    for obj in objs:
        obj.honk()

    # Publish with the intent to batch-send later
    for obj in objs:
        obj.honk(auto=False)
    # Unsubscribe
    for obj in objs:
        obj.unsub_all()
    # We'll send out notifications for any event that happened before unsub
    p.send_all()