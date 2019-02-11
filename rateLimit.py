import time

class rateLimit():


    def __init__(self, RATE, getFunction):

        self.rate = RATE    #calls per 1sec
        self.resource = getFunction
        self.time = None


    def __call__(self, *args):

        if self.time:

            s = time.time()

            timedelta = s - self.time

            wait = 1.0 / self.rate - timedelta

            if wait > 0:
                time.sleep(wait)

        result = self.resource(*args)

        self.time = time.time()

        return result

