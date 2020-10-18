import discord
from Stonks import Stonks
from StonkErrors import *
from decouple import config
from pytz import timezone

guildID = '765387846680313857'


class MyClient(discord.Client):
    # setting up finnhub client

    def __init__(self):
        super().__init__()

        self.stonkState = Stonks()

    async def on_ready(self):
        for guild in client.guilds:
            if guild.id == guildID:
                break
        print(f'{client.user} is connected to {guild.name}')

    #----------------------------core body of reactivity, create commands, etc here
    async def on_message(self, message):
        #don't respond to ourselves
        #be careful about awaiting everything and not returning, might evaluate more than one expects
        if message.author == self.user:
            return

        #-----------------------------new channel test---------------------------------------
        if message.content.startswith('$testies'):
            await self.stonkState.printPort(message)
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
                await message.channel.send(embed=discord.Embed.from_dict(embed))
            except UnrecognizedPlayerError:
                await message.channel.send('You don\'t exist, type $register to join')
            

        #--------------Functionality for if they want a ticker price. Embed message to look pretty.---------
        #get that quote
        if message.content.startswith('$quote'):
            # Get the current date/time
            params = message.content.split(' ')
            if(len(params)!=2):
                await message.channel.send('Bad format: request quotes with \"$quote TICKER\"')
                return
            ticker = params[1]
            try:
                embedDict = self.stonkState.quote(ticker)
            except KeyError:
                await message.channel.send('Invalid ticker')
                return

            await message.channel.send(embed=discord.Embed.from_dict(embedDict))


client = MyClient()
client.run(config('SECRET'))
