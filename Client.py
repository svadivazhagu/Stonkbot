import discord, finnhub, datetime, sqlite3
from decouple import config

LOGO_API = 'https://logo.clearbit.com/'

class MyClient(discord.Client):
    # setting up finnhub client
    async def on_ready(self):
        print('Logged on as', self.user)

    def is_current_user(name, message):
        conn = sqlite3.connect(name)
        c = conn.cursor()
        userID = message.author.id
        c.execute('SELECT * FROM UserData WHERE id =' + str(userID))
        if c.fetchone() == None:
            return False, c
        return True, c


    async def on_message(self, message):
        finnhub_client = finnhub.Client(api_key=config('API_TOKEN'))
        # don't respond to ourselves
        if message.author == self.user:
            return

        # Functionality for if they want a ticker price. Embed message to look pretty.
        if message.content.startswith('$quote'):
            try:
                # Get the current date/time
                now = datetime.datetime.now()

                month, day, hour, minute = '{:02d}'.format(now.month), \
                                        '{:02d}'.format(now.day), \
                                        '{:02d}'.format(now.hour), \
                                        '{:02d}'.format(now.minute)

                hour_min = str(hour) + ':' + str(minute)
                date = str(month) + '/' + str(day)

                ticker = message.content.split(' ')[1].upper()
                company_profile = finnhub_client.company_profile2(symbol=ticker)

                company_name = company_profile['name'].split(' ')[0]

                color = 0x00ff00

                quote = finnhub_client.quote(ticker)

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
            except (KeyError, UnboundLocalError):
                await message.channel.send("Cannot find the ticker, please check your syntax and try again.")
        
        if message.content.startswith('$register'):
            if is_current_user('StonkbotDB.db', message)[0] is False:
                cash = 10000
                c.execute('INSERT INTO UserData VALUES (' + str(userID) + ',' + str(cash)+ ')')
                conn.commit()
                conn.close()
                await message.channel.send('You have successfully registered. Your current balance is: $'+str(cash)+'.')
            else:
                await message.channel.send('You are already registered.')

        if message.content.startswith('$balance'):
            isUser = is_current_user('StonkbotDB.db', message)
            if isUser[0]:
                isUser[1].execute('SELECT * FROM UserData WHERE id =' + str(message.author.id))
                balance = c.fetchone()
                await message.channel.send('Your current balance is $' + balance + '.')
            else:
                await message.channel.send('You are not yet registered. Please try registering.')

        # if message.content.startswith('$buy'):



        # if message.content.startswith('$sell'):



    


client = MyClient()
client.run(config('SECRET'))
