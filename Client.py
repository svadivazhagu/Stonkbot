import discord
from Stonks import Stonks
from StonkErrors import *
from decouple import config
from pytz import timezone


class MyClient(discord.Client):
    # setting up finnhub client

    def __init__(self):
        super().__init__()

        self.stonkState = Stonks()

    async def on_ready(self):
        print('Logged on as', self.user)

    #----------------------------core body of reactivity, create commands, etc here
    async def on_message(self, message):
        #don't respond to ourselves
        #be careful about awaiting everything and not returning, might evaluate more than one expects
        if message.author == self.user:
            return

        #-----------------------------new channel test---------------------------------------
        if message.content.startswith('$testies'):
            return

        #--------------------------------create a new stock market game------------------------------
        #reset amounts, create new tables, etc
        if message.content == '$new':
            await message.channel.send('Creating new Stock Market Game')

        #-----------------------------------------register a new player------------------------------
        #create an entry in the UserData table, allows them to play the game
        if message.content.startswith('$register'):
            await message.channel.send(self.stonkState.register(message.author.id))

        #------------------------------------------buy shares in a stock---------------------------
        #pulls stock cost and buys X number
        if message.content.startswith('$buy'):
            params = message.content.split(' ')
            if(len(params) != 3):
                await message.channel.send('Bad format: submit buy orders with \"$buy TICKER NUMSHARES\"')
                return
            try:
                await message.channel.send(self.stonkState.buy(message.author.id, params[1], int(params[2])))
            except ValueError:
                await message.channel.send('Bad format: submit buy orders with \"$buy TICKER NUMSHARES\"')


        #----------------------------------------sell shares of a stock-------------------------------
        #pulls stock cost and sells X number
        if message.content.startswith('$sell'):
            params = message.content.split(' ')
            if(len(params) != 3):
                await message.channel.send('Bad format: submit buy orders with \"$buy TICKER NUMSHARES\"')
                return
            try:
                await message.channel.send(self.stonkState.sell(message.author.id, params[1], int(params[2])))
            except ValueError:
                await message.channel.send('Bad format: submit buy orders with \"$buy TICKER NUMSHARES\"')

        #--------------------------------return the value of all assets---------------------------
        # prints liquid money and all stocks 
        if message.content.startswith('$balance'):
            try:
                embed = self.stonkState.balance(message.author)
                await message.channel.send(embed=embed)
            except UnrecognizedPlayerError:
                await message.channel.send('You don\'t exist, type $register to join')
            

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
