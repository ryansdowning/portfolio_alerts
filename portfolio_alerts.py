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
        self.last_notification = datetime.datetime.now() - datetime.timedelta(minutes=60)

    def pfolio_check(self):
        self.change = self.portfolio.check_change()
        current_time = datetime.datetime.now()
        time_change = (current_time - self.last_notification).seconds
        if (self.portfolio.old_change + User.NOTIFY_SIZE <= self.change or self.change <= self.portfolio.old_change - User.NOTIFY_SIZE) and time_change >= 1800:
            self.last_notification = current_time
            self.send_notification()
            self.portfolio.old_change = self.change

    def send_notification(self):
        profit = self.portfolio.new_total - self.portfolio.open_total()
        self.portfolio.old_change = self.change
        buy_total = np.sum(np.array(self.portfolio.buy_prices)*self.portfolio.amounts)
        total_gain = self.portfolio.new_total - buy_total
        total_change = (self.portfolio.new_total - buy_total) / buy_total * 100
        message = '{}\nHey {},\nNet Assets: {}\nDay\'s {}: {} ({}%)\nTotal Gain: {} ({}%)'.format(
            self.last_notification.time().strftime('%I:%M:%S%p'),
            self.name,
            round(self.portfolio.new_total, 2),
            'Gain' if profit >= 0 else 'Loss',
            round(profit, 2),
            round(self.change, 2),
            round(total_gain, 2),
            round(total_change, 2))
        print('Sent from your Twilio trial account -\n' + message)
        client.messages.create(from_=twilio_number, body=message, to=self.phone_number)


class Portfolio:
    def __init__(self, tickers, buy_prices, amounts):
        self.tickers = [Stock(ticker) for ticker in tickers]
        self.buy_prices = buy_prices
        self.amounts = amounts
        self.current_prices = []
        self.update_all_prices()
        self.weights = np.array(self.current_prices) * np.array(self.amounts) / self.get_total()
        self.todays_open = self.open_total()
        self.old_change = 0
        self.new_total = self.todays_open

    def get_current_price(self, ticker):
        return ticker.get_price()

    def get_all_prices(self):
        return self.current_prices

    def update_all_prices(self):
        self.current_prices = [self.get_current_price(ticker) for ticker in self.tickers]

    def get_total(self):
        return np.sum(self.current_prices * np.array(self.amounts))

    def check_change(self):
        self.update_all_prices()
        self.new_total = self.get_total()
        change = self.new_total - self.todays_open
        percent = change / self.todays_open * 100
        print('{}: {}'.format(self.old_change, percent))
        return percent

    def get_todays_open(self):
        return [ticker.get_previous()['close'] for ticker in self.tickers]

    def open_total(self):
        return np.sum(self.get_todays_open() * np.array(self.amounts))
        
test_user = User('Bob', '1235556789', ['AMZN', 'AAPL', 'NFLX', 'SPY', 'KO'],
            [1926.42, 218.37, 366.96, 291.22, 45.96],
            [25, 150, 200, 100, 250])

if __name__ == '__main__':
    while True:
        test_user.pfolio_check()
        print(datetime.datetime.now().time().strftime('%I:%M:%S%p'))
        time.sleep(60)
