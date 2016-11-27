class OhlcData:

    def __init__(self, data): # 0.time, 1.open, 2.high, 3.low, 4.close, 5.volume
        self.data = data
        self.convertToPrices()

    def convertToPrices(self):
        self.prices = []
        for point in self.data:
            self.prices.append((point[2]+point[3])/2.0)

    def ema(self, alpha=0.1):
        ema = [self.prices[0]]
        for point in self.prices[1:]:
            ema.append( alpha*point + (1-alpha)*ema[len(ema)-1] )
        return ema