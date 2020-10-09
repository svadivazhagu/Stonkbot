import discord, finnhub, datetime
from decouple import config


class MyClient(discord.Client):
    # setting up finnhub client
    async def on_ready(self):
        print('Logged on as', self.user)

    async def on_message(self, message):
        finnhub_client = finnhub.Client(api_key=config('API_TOKEN'))
        # don't respond to ourselves
        if message.author == self.user:
            return

        if message.content == '$new':
            await message.channel.send('Creating new Stock Market Game')

        # Functionality for if they want a ticker price. Embed message to look pretty.

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
            embed = discord.Embed(title='Stock Ticker Quote', description='USD Quote for ' + ticker + ' on ' + date +
                                                                          ' at '
                                                                          + hour_min, color=0x00ff00)
            quote = finnhub_client.quote(ticker)
            embed.add_field(name='Current', value='$' + str(quote['c']))
            embed.add_field(name='Open', value='$' + str(quote['o']))
            embed.add_field(name='High', value='$' + str(quote['h']))
            embed.add_field(name='Low', value='$' + str(quote['l']))
            embed.add_field(name='Previous Close', value='$' + str(quote['pc']))

            await message.channel.send(embed=embed)


client = MyClient()
client.run(config('SECRET'))
