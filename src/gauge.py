class Gauge():
    def __init__(self, options, data) -> None:
        pass

    def subscribed_streams(self):
        return set()
    
    def wants_updates(self):
        return True
        
    def stream_updated(self, field_spec):
        return None
    
    def update(self):
        return None
    