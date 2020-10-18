class Error(Exception):
    pass

class BuyOverspendError(Error):
    pass

class NegativeSharesError(Error):
    pass

class SellTooManySharesError(Error):
    pass

class MarketCloseError(Error):
    pass

class UnrecognizedPlayerError(Error):
    pass

class UnfoundTickerError(Error):
    pass