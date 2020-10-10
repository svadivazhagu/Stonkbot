import discord, finnhub, datetime
import sqlite3
import DBHandler
from decouple import config
from pytz import timezone


class MyClient(discord.Client):
    # setting up finnhub client

    def __init__(self):
        super().__init__()
        self.dbh = DBHandler.DBHandler('sexystonks.db')
        self.finhubClient = finnhub.Client(api_key=config('API_TOKEN'))
        self.initBalance = 10000

    def isBuyingOpen(self):
        ttime = datetime.datetime.now(tz=datetime.timezone.utc)
        openTime = datetime.datetime(year=ttime.year, month=ttime.month, day=ttime.day, hour=9, minute=30, tzinfo=timezone('US/Eastern'))
        closeTime = datetime.datetime(year=ttime.year, month=ttime.month, day=ttime.day, hour=16, tzinfo=timezone('US/Eastern'))
        if((ttime > openTime) & (ttime < closeTime)):
            return True
        else:
            return False

    def buy(self, user, ticker, shares):
        try:
            shares = int(shares)
            currPrice = self.finhubClient.quote(ticker)['c']

            if(currPrice==0):
                return False
            
            amount = currPrice*shares
            self.dbh.updateBuySell(user, ticker, amount, shares, 'buy')
            return True

        except (ValueError, IndexError):
            return False

    def sell(self, user, ticker, shares):
        try:
            shares = int(shares)
            currPrice = self.finhubClient.quote(ticker)['c']
            if(currPrice==0):
                return False
            
            amount = currPrice*shares
            self.dbh.updateBuySell(user, ticker, amount, shares, 'sell')
            return True

        except (ValueError, IndexError):
            return False

    def accSummary(self, user):
        return

    def portfolio(self, user):
        output = {}
        output['title'] = 'Account Summary for ' + str(user)
        output['description'] = 'Total Value'
        field1 = {'name':'Liquid', 'value':balance}
        field2 = {'name':'Assets', 'value': monetaryStockVal}
        field3 = {'name':'Top Stock', 'value':ticker}

        return output

    def quote(self, ticker):
        return

    async def on_ready(self):
        print('Logged on as', self.user)

    #----------------------------core body of reactivity, create commands, etc here
    async def on_message(self, message):
        #don't respond to ourselves
        #be careful about awaiting everything and not returning, might evaluate more than one expects
        if message.author == self.user:
            return

        #--------------------------------create a new stock market game------------------------------
        #reset amounts, create new tables, etc
        if message.content == '$new':
            await message.channel.send('Creating new Stock Market Game')

        #-----------------------------------------register a new player------------------------------
        #create an entry in the UserData table, allows them to play the game
        if message.content.startswith('$register'):
            if(self.dbh.confirmUser(message.author.id)):
                await message.channel.send('already exist')
            else:
                self.dbh.createUser(message.author.id, self.initBalance)

        #------------------------------------------buy shares in a stock---------------------------
        #pulls stock cost and buys X number
        if message.content.startswith('$buy'):
            if(not self.isBuyingOpen()):
                await message.channel.send('It\'s too late! Try again tomorrow')
                return
            if(self.dbh.confirmUser(message.author.id)):
                params = message.content.split(' ')
                #figure out error handling
                if(len(params) != 3):
                    await message.channel.send('Bad format: submit buy orders with \"$buy TICKER NUMSHARES\"')
                    return

                buySuccess = self.buy(message.author.id, params[1], params[2])
                if(buySuccess):
                    await message.channel.send('Buy Successful!')
                else:
                    await message.channel.send('Buy Unsuccessful :(')
            else:
                await message.channel.send('You don\'t exist, say \"$register\" to join')

        #----------------------------------------sell shares of a stock-------------------------------
        #pulls stock cost and sells X number
        if message.content.startswith('$sell'):
            if(not self.isBuyingOpen()):
                await message.channel.send('It\'s too late! Try again tomorrow')
                return
            if(self.dbh.confirmUser(message.author.id)):
                params = message.content.split(' ')
                #figure out error handling
                if(len(params) != 3):
                    await message.channel.send('Bad format: submit buy orders with \"$sell TICKER NUMSHARES\"')
                    return
                
                buySuccess = self.sell(message.author.id, params[1], params[2])
                if(buySuccess):
                    await message.channel.send('Sell Successful!')
                else:
                    await message.channel.send('Sell Unsuccessful :(')
            else:
                await message.channel.send('You don\'t exist, say \"$register\" to join')


        if message.content.startswith('$balance'):
            #get current money
            await message.channel.send('You have ')
            

        #--------------Functionality for if they want a ticker price. Embed message to look pretty.---------
        #get that quote
        if message.content.startswith('$quote'):
            # Get the current date/time
            now = datetime.datetime.now()

            month, day, hour, minute = '{:02d}'.format(now.month), \
                                       '{:02d}'.format(now.day), \
                                       '{:02d}'.format(now.hour), \
                                       '{:02d}'.format(now.minute)

            hour_min = str(hour) + ':' + str(minute)
            date = str(month) + '/' + str(day)

            ticker = message.content.split(' ')[1].upper()
            company_profile = self.finhubClient.company_profile2(symbol=ticker)
            try:
                company_name = company_profile['name'].split(' ')[0]
            except KeyError:
                print(ticker)
                await message.channel.send('Ticker not found. Try again.')
                return


            color = 0x00ff00

            quote = self.finhubClient.quote(ticker)

            if quote['c'] >= quote['pc']:
                color = 0x00ff00
            else:
                color = 0xff0000

            embed = discord.Embed(title='Stock Ticker Quote',
                                  description='USD Quote for ' + company_name + ' on ' + date +
                                              ' at '
                                              + hour_min, color=color)


            embed.set_thumbnail(url=company_profile['logo'])
            embed.add_field(name='Current', value='$' + str(quote['c']))
            embed.add_field(name='Open', value='$' + str(quote['o']))
            embed.add_field(name='High', value='$' + str(quote['h']))
            embed.add_field(name='Low', value='$' + str(quote['l']))
            embed.add_field(name='Previous Close', value='$' + str(quote['pc']))


            await message.channel.send(embed=embed)


client = MyClient()
client.run(config('SECRET'))
