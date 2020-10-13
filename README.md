# Stonkbot
## A Discord bot for a Stock Market trading game

### Requirements
- Python (v3+)
     - Requests module
- Discord.py module
- SQLite python module
- Finnhub python module (alternative - use Finnhub API)

### Features

- Create a Game instance of the stock market trading game  
    - Get some money to start investing
    - Lookup the price of a current ticker
    - In a given stock trading window, buy/sell shares
    - Examine current portfolio/distribution of shares
    - Track portfolio worth over time
- End a game instance
    - Track player vs. player performance over the duration of the game period.
    
    
### TODO

- db related (Surya)
    - Separate database buy/sell functions
    - change sql queries to use global variables instead of hardcoded table names
    - database implementing (un)realized gains

- client refactor (Gordon)
    - separate out client

- :(
    