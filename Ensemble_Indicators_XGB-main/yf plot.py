import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# Symbol and TP
symbol = "AAPL" 
start_date = "2022-01-01"
end_date = "2022-12-31"

# prep data
data = yf.download(symbol, start=start_date, end=end_date)

# calculating Bollinger Bands
data['SMA'] = data['Close'].rolling(window=20).mean()   # 20-day Simple Moving Average
data['Std'] = data['Close'].rolling(window=20).std()    # 20-day Standard Deviation
data['Upper'] = data['SMA'] + (data['Std'] * 2)         # Upper Bollinger Band
data['Lower'] = data['SMA'] - (data['Std'] * 2)         # Lower Bollinger Band

# calculating RSI
def calculate_rsi(data, period=14):
    delta = data['Close'].diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

data['RSI'] = calculate_rsi(data)


data['Buy_Signal'] = 0
data['Sell_Signal'] = 0
position = 0


for i in range(26, len(data)):
    if (
        data['Close'][i] > data['Upper'][i] and
        data['Close'][i - 1] <= data['Upper'][i - 1] and
        data['RSI'][i] > 70 and
        position == 0
    ):
        data['Sell_Signal'][i] = data['Close'][i]
        position = 1
    elif (
        data['Close'][i] < data['Lower'][i] and
        data['Close'][i - 1] >= data['Lower'][i - 1] and
        data['RSI'][i] < 30 and
        position == 1
    ):
        data['Buy_Signal'][i] = data['Close'][i]
        position = 0

# Bollinger Bands, RSI, and buy/sell signals
plt.figure(figsize=(12, 6))
plt.plot(data.index, data['Close'], label=f'{symbol} Close Price', color='blue')
plt.plot(data.index, data['SMA'], label='20-day SMA', color='orange')
plt.plot(data.index, data['Upper'], label='Upper Bollinger Band', color='red', linestyle='--')
plt.plot(data.index, data['Lower'], label='Lower Bollinger Band', color='green', linestyle='--')
plt.scatter(data.index, data['Buy_Signal'], label='Buy Signal', marker='^', color='green', alpha=1)
plt.scatter(data.index, data['Sell_Signal'], label='Sell Signal', marker='v', color='red', alpha=1)
plt.xlabel("Date")
plt.ylabel("Price")
plt.title(f'{symbol} Stock Price with Bollinger Bands, RSI, and Buy/Sell Signals')
plt.legend()
plt.grid(True)

# RSI 2 axis
ax2 = plt.gca().twinx()
ax2.plot(data.index, data['RSI'], label='RSI', color='purple')
ax2.set_ylabel('RSI')
ax2.legend(loc='upper left')

# Show the plot
plt.show()
