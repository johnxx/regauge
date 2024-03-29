class Gauge():
    def __init__(self, name, options, resources) -> None:
        self.name = name
        self.options = options
        self.resources = resources

    def subscribed_streams(self):
        return set()
    
    def wants_updates(self):
        return True
        
    def stream_updated(self, field_spec):
        return None
    
    async def update(self):
        return None
    
    @property
    def update_freq(self):
        return self.options['update_freq']
    
    def config_updated(self):
        pass