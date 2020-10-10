import sqlite3
from decouple import config

class DBHandler:
    def __init__(self, name):
        self.dbconn = sqlite3.connect(name)

    def updateBuySell(self, user, ticker, cost, shares, type):
        balance = self.dbconn.execute('SELECT balance FROM UserData WHERE userid=?', (user,)).fetchone()[0]
        currShares = self.dbconn.execute('SELECT shares FROM Portfolios WHERE userid=? AND ticker=?',(user, ticker)).fetchone()
        if(currShares):
            currShares = currShares[0]
        else:
            currShares = 0

        if(type == 'buy'):
            if(currShares):
                self.dbconn.execute('UPDATE Portfolios SET shares=? WHERE userid=? AND ticker=?', (currShares+shares, user, ticker))
            else:
                self.dbconn.execute('INSERT INTO Portfolios VALUES (?, ?, ?)', (user, ticker, shares))
        elif(type == 'sell'):
            cost = -cost
            if(currShares<shares):
                return False
            elif(currShares == shares):
                self.dbconn.execute('DELETE FROM Portfolios WHERE userid=? AND ticker=?', (user, ticker))
            else:
                self.dbconn.execute('UPDATE Portfolios SET shares=? WHERE userid=? AND ticker=?', (currShares-shares, user, ticker))
        else:
            #you can only buy or sell :thonking:
            return False

        self.dbconn.execute('UPDATE UserData SET balance=? WHERE userid=?', (balance-cost,user))
        self.dbconn.commit()

    def confirmUser(self, user):
        if(self.dbconn.execute('SELECT * FROM UserData WHERE userid=?', (user,)).fetchone()):
            return True
        else:
            return False

    def createUser(self, user, balance):
        self.dbconn.execute('INSERT INTO UserData VALUES (?, ?)', (user, balance))
        self.dbconn.commit()


    