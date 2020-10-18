import sqlite3
from decouple import config
import datetime

class DBHandler:
    def __init__(self, name):
        self.dbconn = sqlite3.connect(name)

    def initializeTables(self, initBalance):
        self.dbconn.execute('CREATE table UserData (userid integer, balance real)')
        self.dbconn.execute('CREATE table Transactions (transactionnumber integer, userid integer, ticker text, shares integer, spent real, transactiondate text)')
        self.dbconn.execute('CREATE table Portfolios (userid integer, ticker text, shares integer, spent real)')
        self.dbconn.execute('CREATE table config (startBalance real, transactionCount integer)')
        self.dbconn.execute('INSERT INTO config VALUES (?, 0)', (initBalance, ))
        self.dbconn.commit()

    def incrementTransactions(self):
        transNumber = self.dbconn.execute('SELECT transactionCount FROM config').fetchone()[0]+1
        self.dbconn.execute('UPDATE config SET transactionCount=?', (transNumber,))
        self.dbconn.commit()
        return transNumber

    def buy(self, user, ticker, cost, shares):
        balance = self.retrieveBalance(user)
        currShares = self.dbconn.execute('SELECT shares FROM Portfolios WHERE userid=? AND ticker=?',(user, ticker)).fetchone()
        transNumber = self.incrementTransactions()
        rn = datetime.datetime.now(datetime.timezone.utc)

        if(currShares):
            currShares = currShares[0]
            preSpent = self.dbconn.execute('SELECT spent FROM Portfolios WHERE userid=? AND ticker=?',(user, ticker)).fetchone()[0]
            self.dbconn.execute('UPDATE Portfolios SET shares=? AND spent=? WHERE userid=? AND ticker=?', (currShares+shares, preSpent+cost, user, ticker))
        else:
            self.dbconn.execute('INSERT INTO Portfolios VALUES (?,?,?,?)', (user,ticker,shares,cost))
        
        self.dbconn.execute('UPDATE UserData SET balance=? WHERE userid=?',(balance-cost, user))
        self.dbconn.execute('INSERT INTO Transactions VALUES (?, ?, ?, ?, ?, ?)', (transNumber, user, ticker, shares, cost, rn.ctime()))
        self.dbconn.commit()

        return

    def sell(self, user, ticker, cost, shares):
        balance = self.retrieveBalance(user)
        currShares = self.dbconn.execute('SELECT shares FROM Portfolios WHERE userid=? AND ticker=?',(user, ticker)).fetchone()
        transNumber = self.incrementTransactions()
        rn = datetime.datetime.now(datetime.timezone.utc)
        currShares = currShares[0]

        if(currShares==shares):
            self.dbconn.execute('DELETE FROM Portfolios WHERE userid=? AND ticker=?', (user, ticker))
        else:
            preSpent = self.dbconn.execute('SELECT spent FROM Portfolios WHERE userid=? AND ticker=?',(user, ticker)).fetchone()[0]
            self.dbconn.execute('UPDATE Portfolios SET shares=?, spent=? WHERE userid=? AND ticker=?', (currShares-shares,preSpent-cost,user,ticker))
        
        self.dbconn.execute('UPDATE UserData SET balance=? WHERE userid=?',(balance+cost, user))
        self.dbconn.execute('INSERT INTO Transactions VALUES (?, ?, ?, ?, ?, ?)', (transNumber, user, ticker, -shares, -cost, rn.ctime()))
        self.dbconn.commit()

        return

    def confirmUser(self, user):
        if(self.dbconn.execute('SELECT * FROM UserData WHERE userid=?', (user,)).fetchone()):
            return True
        else:
            return False

    def createUser(self, user, balance):
        self.dbconn.execute('INSERT INTO UserData VALUES (?, ?)', (user, balance))
        self.dbconn.commit()
        return True

    def retrieveStocks(self, user):
        stonks = self.dbconn.execute('SELECT * FROM Portfolios WHERE userid=?', (user, )).fetchall()
        output = {}
        for row in stonks:
            output[row[1]] = row[2]
        return output

    def retrieveBalance(self, user):
        output = self.dbconn.execute('SELECT balance FROM UserData WHERE userid=?', (user, )).fetchone()[0]
        return output

    def checkTable(self, tablename):
        return self.dbconn.execute('SELECT count(name) FROM sqlite_master WHERE type=\'table\' AND name=?', (tablename,)).fetchone()[0]==1

    def createTable(self, tablename, rowString):
        self.dbconn.execute('CREATE table ? ?', (tablename, rowString))
        self.dbconn.commit()



    