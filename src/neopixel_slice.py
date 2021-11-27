class NeoPixelSlice():
    def __init__(self, real_pixels, virtual_subset=None):
        if virtual_subset:
            self.virtual_subset = virtual_subset
        else:
            self.virtual_subset = list(range(real_pixels.n))

        try:
            real_pixels.__references += 1
        except AttributeError:
            real_pixels.__references = 1

        self.real_pixels = real_pixels

    def deinit(self):
        self.real_pixels.__references -= 1
        self.fill(0)
        if self.real_pixels.__references == 0:
            return self.real_pixels.deinit()

    def fill(self, color):
        for n in self.virtual_subset:
            self.real_pixels[n] = color
        
    def __setitem__(self, idx, val):
        self.real_pixels[self.virtual_subset[idx]] = val
        
    def __getitem__(self, idx):
        return self.real_pixels[self.virtual_subset[idx]]
    
    def n(self):
        return len(self.virtual_subset)
    
    def show(self):
        self.real_pixels.show()
        
    @property
    def brightness(self):
        return self.real_pixels.brightness

    @brightness.setter
    def brightness(self, val):
        self.real_pixels.brightness = val