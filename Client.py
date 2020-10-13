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
        output = self.dbh.retrieveStocks(user)
        print(output)

    def quote(self, ticker):
        return

    async def on_ready(self):
        print('Logged on as', self.user)

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
            await userChan.send(k.upper()+'\nnum: '+str(v)+' spent: '+'200'+' worth: '+'300'+' gains: '+'100\n---')
        

    #----------------------------core body of reactivity, create commands, etc here
    async def on_message(self, message):
        #don't respond to ourselves
        #be careful about awaiting everything and not returning, might evaluate more than one expects
        if message.author == self.user:
            return

        #-----------------------------new channel test---------------------------------------
        if message.content.startswith('$testies'):
            await self.printPort(message)
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

        #--------------------------------return the value of all assets---------------------------
        # prints liquid money and all stocks 
        if message.content.startswith('$balance'):
            if(not self.dbh.confirmUser(message.author.id)):
                await message.channel.send('You don\'t exist, say \"$register\" to join')
                return
            stonks = self.dbh.retrieveStocks(message.author.id)
            balance = self.dbh.retrieveBalance(message.author.id)
            total = 0
            bigK = 'AAAA'
            bigV = 0
            for k, v in stonks.items():
                price = self.finhubClient.quote(k)['c']
                total += price*v
                if(price*v>bigV):
                    bigK = k
                    bigV = price*v

            embed = discord.Embed.from_dict(
                {
                'title':'Balance of '+str(message.author.name),
                'description': 'Total value of assets: $' + '{:.2f}'.format(round(balance+total, 2)),
                'thumbnail':{
                    'url':str(message.author.avatar_url)
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
            )

            await message.channel.send(embed=embed)
            

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
