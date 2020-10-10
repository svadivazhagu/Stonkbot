import discord, finnhub, datetime
import sqlite3
from decouple import config


class MyClient(discord.Client):
    # setting up finnhub client

    def __init__(self):
        super().__init__()
        self.dbconn = sqlite3.connect('sexystonks.db')
        self.finhubClient = finnhub.Client(api_key=config('API_TOKEN'))
        self.initBalance = 10000

    def confirmUser(self, user):
        if(self.dbconn.cursor().execute('SELECT * FROM UserData WHERE userid=?', (user,)).fetchone()):
            return True
        else:
            return False

    def buy(self, user, ticker, shares):
        try:
            shares = int(shares)
            currPrice = self.finhubClient.quote(ticker)['c']
            if(~currPrice):
                return False
            
            amount = currPrice*shares
            balance = self.dbconn.cursor().execute('SELECT balance FROM UserData WHERE userid=?', (user,)).fetchone()[0]
            newBalance = balance-amount

            self.dbconn.cursor().execute('UPDATE UserData SET balance=? WHERE userid=?', (newBalance,user))
            currShares = self.dbconn.cursor().execute('SELECT shares FROM Portfolios WHERE userid=? AND ticker=?',(user, ticker)).fetchone()

            if(currShares):
                self.dbconn.cursor().execute('UPDATE Portfolios SET shares=? WHERE userid=? AND ticker=?', (currShares[0]+shares, user, ticker))
            else:
                self.dbconn.cursor().execute('INSERT INTO Portfolios VALUES (?, ?, ?)', (user, ticker, shares))

            self.dbconn.commit()
            return True

        except (ValueError, IndexError):
            return False

    def sell(self, user, ticker, shares):
        try:
            shares = int(shares)
            currPrice = self.finhubClient.quote(ticker)['c']
            if(~currPrice):
                return False
            
            amount = currPrice*shares
            balance = self.dbconn.cursor().execute('SELECT balance FROM UserData WHERE userid=?', (user,)).fetchone()[0]
            newBalance = balance+amount
            currShares = self.dbconn.cursor().execute('SELECT * FROM Portfolios WHERE userid=? AND ticker=?',(user, ticker)).fetchone()

            if(currShares[2]<shares):
                return False
            elif(currShares[2] == shares):
                self.dbconn.cursor().execute('DELETE FROM Portfolios WHERE userid=? AND ticker=?', (user, ticker))
            else:
                self.dbconn.cursor().execute('UPDATE Portfolios SET shares=? WHERE userid=? AND ticker=?', (currShares[2]-shares, user, ticker))

            self.dbconn.cursor().execute('UPDATE UserData SET balance=? WHERE userid=?', (newBalance,user))
            self.dbconn.commit()
            return True

        except (ValueError, IndexError):
            return False

    def portfolio(self, user):
        return

    def quote(self, ticker):
        return

    async def on_ready(self):
        print('Logged on as', self.user)

    async def on_message(self, message):
        # don't respond to ourselves
        if message.author == self.user:
            return

        if message.content == '$new':
            await message.channel.send('Creating new Stock Market Game')

        if message.content.startswith('$register'):
            if(self.confirmUser(message.author.id)):
                await message.channel.send('already exist')
            else:
                self.dbconn.cursor().execute('INSERT INTO UserData VALUES (?, ?)', (message.author.id, self.initBalance))
                self.dbconn.commit()
                await message.channel.send('created')

        if message.content.startswith('$buy'):
            if(self.confirmUser(message.author.id)):
                params = message.content.split(' ')
                #figure out error handling
                if(len(params) != 3):
                    await message.channel.send('Bad format: submit buy orders with \"$buy TICKER NUMSHARES\"')

                buySuccess = self.buy(message.author.id, params[1], params[2])
                if(buySuccess):
                    await message.channel.send('Buy Successful!')
                else:
                    await message.channel.send('Buy Unsuccessful :(')
            else:
                await message.channel.send('You don\'t exist, say \"$register\" to join')

        if message.content.startswith('$sell'):
            if(self.confirmUser(message.author.id)):
                params = message.content.split(' ')
                #figure out error handling
                if(len(params) != 3):
                    await message.channel.send('Bad format: submit buy orders with \"$sell TICKER NUMSHARES\"')
                
                buySuccess = self.sell(message.author.id, params[1], params[2])
                if(buySuccess):
                    await message.channel.send('Sell Successful!')
                else:
                    await message.channel.send('Sell Unsuccessful :(')
            else:
                await message.channel.send('You don\'t exist, say \"$register\" to join')
            

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
            company_profile = self.finhubClient.company_profile2(symbol=ticker)
            try:
                company_name = company_profile['name'].split(' ')[0]
            except KeyError:
                print(ticker)
                await message.channel.send('Ticker not found. Try again.')


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
