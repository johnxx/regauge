import time
import logging

stats = {}

def profile(name='default'):
    def profile_real(func):
        def wrap(*args, **kwargs):
            started_at = time.time()
            result = func(*args, **kwargs)
            logging.info(time.time() - started_at)
            return result

        return wrap
    return profile_real

@profile
def foo():
    pass

