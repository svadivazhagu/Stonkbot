import finnhub, datetime
import sqlite3
import DBHandler
from StonkErrors import *
from decouple import config
from pytz import timezone
import discord


class Stonks:
    def __init__(self):
        self.dbh = DBHandler.DBHandler('sexystonks.db')
        self.finhubClient = finnhub.Client(api_key=config('API_TOKEN'))

        self.initBalance = config('INITIAL_BALANCE')

        if(not self.dbh.checkTable('config')):
            self.dbh.initializeTables(self.initBalance)

    #---------------------------client-callable functions------------------

    def buy(self, userid, ticker, shares):
        try:
            self.isBuyingOpen()
            self.isRegisteredPlayer(userid)

            if(shares <= 0):
                raise NegativeSharesError
        
            price = self.finhubClient.quote(ticker)['c']
            balance = self.dbh.retrieveBalance(userid)
            cost = price*shares

            if(cost>balance):
                raise BuyOverspendError

            #this probably will become insert/update calls
            self.dbh.buy(userid, ticker, cost, shares)
            return 'Successful transaction!'

        except NegativeSharesError:
            return 'Shares must be a positive number'

        except BuyOverspendError:
            return 'You don\'t have enough money for this transaction'

        except MarketCloseError:
            return 'Market is closed; it\'s open weekdays from 9:30AM to 4:00PM Eastern'

        except UnrecognizedPlayerError:
            return 'You don\'t exist, type \"$register\" to join the game'

    def sell(self, userid, ticker, shares):
        try:
            self.isBuyingOpen()
            self.isRegisteredPlayer(userid)

            if(shares <= 0):
                raise NegativeSharesError
        
            price = self.finhubClient.quote(ticker)['c']
            stonks = self.dbh.retrieveStocks(userid)

            if(stonks[ticker] < shares):
                raise SellTooManySharesError

            sellPrice = price*shares

            #this probably will become insert/update calls
            self.dbh.sell(userid, ticker, sellPrice, shares)
            return 'Successful transaction!'

        except NegativeSharesError:
            return 'Shares must be a positive number'

        except SellTooManySharesError:
            return 'You don\'t have enough shares for this transaction'

        except MarketCloseError:
            return 'Market is closed; it\'s open weekdays from 9:30AM to 4:00PM Eastern'

        except UnrecognizedPlayerError:
            return 'You don\'t exist, type \"$register\" to join the game'


    def register(self, userid):
        if(self.dbh.confirmUser(userid)):
            return 'Already registered'
        else:
            self.dbh.createUser(userid, self.initBalance)
            return 'Registered! Enjoy!'

    def balance(self, user):
        self.isRegisteredPlayer(user.id)
        stonks = self.dbh.retrieveStocks(user.id)
        balance = self.dbh.retrieveBalance(user.id)
        total = 0
        bigK = 'AAAA'
        bigV = 0
        for k, v in stonks.items():
            price = self.finhubClient.quote(k)['c']
            numShares = v['shares']
            total += price*numShares
            if(price*numShares>bigV):
                bigK = k
                bigV = price*numShares

        embedDict = {
            'title':'Balance of '+str(user.name),
            'description': 'Total value of assets: $' + '{:.2f}'.format(round(balance+total, 2)),
            'thumbnail':{
                'url':str(user.avatar_url)
            },
            'fields':[
                {
                    'name':'Liquid Amount',
                    'value':'$'+'{:.2f}'.format(round(balance, 2))
                },
                {
                    'name':'Stock Amount',
                    'value':'$'+'{:.2f}'.format(round(total, 2))
                },
                {
                    'name':'Best Stock',
                    'value':bigK+': worth $'+'{:.2f}'.format(round(bigV, 2))
                },
            ]
        }

        return embedDict

    def quote(self, ticker):
        now = datetime.datetime.now()

        month, day, hour, minute = '{:02d}'.format(now.month), \
                                    '{:02d}'.format(now.day), \
                                    '{:02d}'.format(now.hour), \
                                    '{:02d}'.format(now.minute)

        hour_min = str(hour) + ':' + str(minute)
        date = str(month) + '/' + str(day)

        company_profile = self.finhubClient.company_profile2(symbol=ticker)
        company_name = company_profile['name'].split(' ')[0]

        color = 0x00ff00

        quote = self.finhubClient.quote(ticker)

        if quote['c'] >= quote['pc']:
            color = 0x00ff00
        else:
            color = 0xff0000

        output = {
            'title':'Stock Ticker Quote',
            'description':'USD Quote for '+company_name+' on '+date+' at '+hour_min,
            'color':color,
            'thumbnail':{
                'url':company_profile['logo']
            },
            'fields':[
                {
                    'name':'Current',
                    'value':'$'+str(quote['c'])
                },
                {
                    'name':'Open',
                    'value':'$'+str(quote['o'])
                },
                {
                    'name':'High',
                    'value':'$'+str(quote['h'])
                },
                {
                    'name':'Low',
                    'value':'$'+str(quote['l'])
                },
                {
                    'name':'Previous Close',
                    'value':'$'+str(quote['pc'])
                }
            ]
        }

        return output

    # #WIP
    async def printPort(self, message):
        currServer = message.channel.guild
        chanName = message.author.name.lower()+'-stocks'
        foundChan = False
        userChan = None
        for chan in currServer.text_channels:
            if(chan.name == chanName):
                foundChan = True
                userChan = chan
                break

        if(not foundChan):
            catChan = None
            for cat in currServer.categories:
                if(cat.name == 'stonks'):
                    catChan = cat
            overwrites = {
                currServer.default_role: discord.PermissionOverwrite(read_messages=False), 
                message.author: discord.PermissionOverwrite(read_messages=True)
                }
            newCh = await currServer.create_text_channel(name=chanName, overwrites=overwrites, category=catChan)
            userChan = newCh

        stonks = self.dbh.retrieveStocks(message.author.id)
        await userChan.send(embed=discord.Embed.from_dict({'title':'Current Stocks'}))
        for k, v in stonks.items():
            price = self.finhubClient.quote(k)['c']
            await userChan.send(k.upper()+'\nnum: '+str(v['shares'])+' spent: '+str(v['spent'])+' worth: '+str(v['shares']*price)+' gains: '+str(v['shares']*price-v['spent'])+'\n---')

    #----------------------------------------------------------------------

    #----------------------------helper functions--------------------------

    def isBuyingOpen(self):
        return True
        ctime = datetime.datetime.now(tz=datetime.timezone.utc)
        weekday = ctime.weekday()
        openTime = datetime.datetime(year=ctime.year, month=ctime.month, day=ctime.day, hour=9, minute=30, tzinfo=timezone('US/Eastern'))
        closeTime = datetime.datetime(year=ctime.year, month=ctime.month, day=ctime.day, hour=16, tzinfo=timezone('US/Eastern'))
        if((ctime > openTime) & (ctime < closeTime) & (weekday!=5) & (weekday!=6)):
            return True
        else:
            raise MarketCloseError

    def isRegisteredPlayer(self, userid):
        if(not self.dbh.confirmUser(userid)):
            raise UnrecognizedPlayerError

    #----------------------------------------------------------------------

    
