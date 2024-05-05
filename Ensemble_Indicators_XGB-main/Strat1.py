import yfinance as yf
import pandas as pd

stock = yf.Ticker("AAPL")
data = stock.history(interval="1d", period="70d")

# 12 days EMA
data['EMA12'] = data['Close'].ewm(span=12, adjust=False).mean()
# 26 days EMA
data['EMA26'] = data['Close'].ewm(span=26, adjust=False).mean()
# MACD line
data['MACD'] = data['EMA12'] - data['EMA26']
# 9 days moving average of MACD
data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()

initial_balance = 10000
balance = initial_balance
stocks_held = 0
buy_price = 0
total_profit_loss = 0
signal = 0

for i in range(1, len(data)):
    # Update MACD Signal
    if data['MACD'].iloc[i - 1] < data['Signal'].iloc[i - 1] and data['MACD'].iloc[i] > data['Signal'].iloc[i]:
        signal = 1  # Buy
    elif data['MACD'].iloc[i - 1] > data['Signal'].iloc[i - 1] and data['MACD'].iloc[i] < data['Signal'].iloc[i]:
        signal = -1  # Sell
    else:
        signal = 0  # Hold

    # Buy signal
    if signal == 1 and balance > 0:
        balance -= data['Close'].iloc[i]
        stocks_held += 1
        buy_price = data['Close'].iloc[i]
        print(f"At {data.index[i]}, Bought 1 stock. Balance: {balance}, Stocks held: {stocks_held}")

    # Sell signal
    elif signal == -1 and stocks_held > 0:
        balance += data['Close'].iloc[i]
        stocks_held -= 1
        profit_loss = data['Close'].iloc[i] - buy_price
        total_profit_loss += profit_loss
        print(f"At {data.index[i]}, Sold 1 stock. Balance: {balance}, Stocks held: {stocks_held}, Profit/Loss: {profit_loss}")

final_balance = balance + (stocks_held * data['Close'].iloc[-1])
print(f"Initial Balance: {initial_balance}, Final Balance: {final_balance}, Profit/Loss: {final_balance - initial_balance}")
