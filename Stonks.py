import finnhub, datetime
import sqlite3
import DBHandler
from decouple import config
from pytz import timezone

class Error(Exception):
    pass

class BuyOverspendError(Error):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message

class NegativeSharesError(Error):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message

class SellTooManySharesError(Error):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message




class Stonks:
    def __init__(self):
        self.dbh = DBHandler.DBHandler('sexystonks.db')
        self.finhubClient = finnhub.Client(api_key=config('API_TOKEN'))

        self.initBalance = config('INITIAL_BALANCE')

        if(not self.dbh.checkTable('config')):
            utn = config('USER_TABLENAME')
            urs = config('USER_ROWSTRING')
            ttn = config('TRANSACTION_TABLENAME')
            trs = config('TRANSACTION_ROWSTRING')
            ptn = config('PORTFOLIO_TABLENAME')
            prs = config('PORTFOLIO_ROWSTRING')
            ctn = config('CONFIG_TABLENAME')
            crs = config('CONFIG_ROWSTRING')
            self.dbh.createTable(utn, urs)
            self.dbh.createTable(ptn, prs)
            self.dbh.createTable(ttn, trs)
            self.dbh.createTable(ctn, crs)

    #---------------------------client-callable functions------------------

    def tryBuy(self, order):
        return

    def trySell(self, order):
        return

    #----------------------------------------------------------------------

    #----------------------------helper functions--------------------------

    def buy(self, order):
        return

    def sell(self, order):
        return

    def isBuyingOpen(self):
        return True
        ctime = datetime.datetime.now(tz=datetime.timezone.utc)
        weekday = ctime.weekday()
        openTime = datetime.datetime(year=ctime.year, month=ctime.month, day=ctime.day, hour=9, minute=30, tzinfo=timezone('US/Eastern'))
        closeTime = datetime.datetime(year=ctime.year, month=ctime.month, day=ctime.day, hour=16, tzinfo=timezone('US/Eastern'))
        if((ctime > openTime) & (ctime < closeTime) & (weekday!=5) & (weekday!=6)):
            return True
        else:
            return False

    #----------------------------------------------------------------------

    
