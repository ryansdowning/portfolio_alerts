import datetime
import time
import numpy as np
from iexfinance import Stock
from twilio.rest import Client

account_sid =  # twilio account sid
auth_token =  # twilio auth_token
twilio_number =  # my twilio number
client = Client(account_sid, auth_token)


class User:
    NOTIFY_SIZE = 0.5

    def __init__(self, name, phone_number, tickers, buy_prices, amounts):
        self.name = name
        self.phone_number = '+1' + phone_number
        self.portfolio = Portfolio(tickers, buy_prices, amounts)
        self.change = 0
        self.last_notification = datetime.datetime.now()

    def pfolio_check(self):
        self.change = self.portfolio.check_change()
        if -User.NOTIFY_SIZE >= self.change >= User.NOTIFY_SIZE:
            self.send_notification()

    def send_notification(self):
        current_time = datetime.datetime.now()
        prices = self.portfolio.get_all_prices()
        profit = self.portfolio.todays_open - self.portfolio.last_total
        message = '\nHey {}\n{}\nNet Assets: {}\nDay\'s {}: {}\n\nCurrent Prices: {}'.format(
            self.name,
            current_time.time().strftime('%I:%M:%S%p'),
            self.portfolio.last_total,
            'Gain' if profit >= 0 else 'Loss',
            profit,
            '\n'.join('{}: {}'.format(ticker.get_company(), price) for ticker, price in zip(self.portfolio.tickers, prices)))
        print('Sent from your Twilio trial account -' + message)
        client.messages.create(from_=twilio_number, body=message, to=self.phone_number)


class Portfolio:
    def __init__(self, tickers, buy_prices, amounts):
        self.tickers = [Stock(ticker) for ticker in tickers]
        self.buy_prices = buy_prices
        self.amounts = amounts
        self.current_prices = []
        self.update_all_prices()
        self.weights = np.array(self.current_prices)*np.array(self.amounts)/self.get_total()
        self.last_total = self.get_total()
        self.todays_open = self.get_todays_open()

    def get_current_price(self, ticker):
        return ticker.get_price()

    def get_all_prices(self):
        return self.current_prices

    def update_all_prices(self):
        self.current_prices = [self.get_current_price(ticker) for ticker in self.tickers]

    def get_total(self):
        return np.sum(self.current_prices*np.array(self.amounts))

    def check_change(self):
        self.update_all_prices()
        new_total = self.get_total()
        change = new_total - self.last_total
        percent = change/self.last_total*100
        self.last_total = new_total
        return percent

    def get_todays_open(self):
        return [ticker.get_open() for ticker in self.tickers]

    def open_total(self):
        return np.sum(self.todays_open*np.array(self.amounts))
        
test_user = User('Bob', '1235556789', ['AMZN', 'AAPL', 'NFLX', 'SPY', 'KO'],
            [1926.42, 218.37, 366.96, 291.22, 45.96],
            [25, 150, 200, 100, 250])

if __name__ == '__main__':
    while True:
        test_user.pfolio_check()
        print(datetime.datetime.now().time().strftime('%I:%M:%S%p'))
        time.sleep(60)
