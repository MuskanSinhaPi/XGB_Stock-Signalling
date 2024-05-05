import time
import yfinance as yf
import pandas as pd
import xgboost as xgb
import numpy as np
import tkinter as tk
from tkinter import scrolledtext


def update_gui():
    # Check if there are messages in the queue
    global i
    if message_queue:
        # Update the text area with the latest messages
        message = message_queue.pop(0)
        if(message == "" or message == "\n"):
            time.sleep(100000)
        output_text.insert(tk.END, message + '\n')
        output_text.see(tk.END)  # Scroll to the end

    current_price.set(f"Current Price: {data['Close'].iloc[i]:.2f}")
    # Schedule the update function to run again after 1000 milliseconds (1 second)
    window.after(1000, update_gui)

def add_message(message):
    message_queue.append(message)

# Fetch historical stock data
stock = yf.Ticker("AAPL")
data = stock.history(interval="1d", period="70d")

# Calculating EMA, MACD, Signal, SMA, sd, UB, LB, and RSI

# 12 days EMA
data['EMA12'] = data['Close'].ewm(span=12, adjust=False).mean()
# 26 days EMA
data['EMA26'] = data['Close'].ewm(span=26, adjust=False).mean()
# MACD line
data['MACD'] = data['EMA12'] - data['EMA26']
# 9 days moving average of MACD
data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
# 20 days moving average
data['SMA20'] = data['Close'].rolling(window=20).mean()
# 50 days moving average
data['SMA50'] = data['Close'].rolling(window=50).mean()
# 200 days moving average
data['SMA200'] = data['Close'].rolling(window=200).mean()
# 20 days standard deviation
data['sd'] = data['Close'].rolling(window=20).std()
# upper Band
data['UB'] = data['SMA20'] + 2 * data['sd']
# lower Band
data['LB'] = data['SMA20'] - 2 * data['sd']

# Calculate RSI
rsi_period = 14
delta = data['Close'].diff(1)
gain = delta.where(delta > 0, 0)
loss = -delta.where(delta < 0, 0)
average_gain = gain.rolling(window=rsi_period, min_periods=1).mean()
average_loss = loss.rolling(window=rsi_period, min_periods=1).mean()
relative_strength = average_gain / average_loss
rsi = 100 - (100 / (1 + relative_strength))

# Add RSI to the dataframe
data['RSI'] = rsi


initial_balance = 1000
balance = initial_balance
stocks_held = 0
buy_price = 0

# Initialize an array for signals
signals_array = [0, 0, 0, 0, 0]  # [MACD Signal, Bollinger Bands Signal, SMA200 Signal, RSI Signal, SMA50 Signal]

# Creating features for the ensemble
xgb_features = pd.DataFrame({
        'MACD_Signal': signals_array[0],
        'Bollinger_Signal': signals_array[1],
        'SMA200_Signal': signals_array[2],
        'RSI_Signal': signals_array[3],
        'SMA50_Signal': signals_array[4]
    }, index=[0])

# Labels (Buy=1, Sell=-1, Hold=0)
labels = np.array([1 if (sum(row) >= 2) else (-1 if (sum(row) <= -2) else 0) for row in xgb_features.values])

# Train an XGBoost model using existing signals
xgb_model = xgb.XGBClassifier(random_state=42)
xgb_model.fit(xgb_features, labels)

# Create GUI window
window = tk.Tk()
window.title("Trading Strategy Output")

# Create a scrolled text widget to display the output
output_text = scrolledtext.ScrolledText(window, width=80, height=20)
output_text.pack(padx=10, pady=10)

# Create a label for the current stock price
current_price = tk.StringVar()
current_price_label = tk.Label(window, textvariable=current_price, font=('Helvetica', 12))
current_price_label.pack()

# Initialize message queue
message_queue = []

# Loop through the data to determine Buy/Sell signals
for i in range(1, len(data)):
    # Update MACD Signal
    if data['MACD'].iloc[i - 1] < data['Signal'].iloc[i - 1] and data['MACD'].iloc[i] > data['Signal'].iloc[i]:
        signals_array[0] = 1  # Buy
    elif data['MACD'].iloc[i - 1] > data['Signal'].iloc[i - 1] and data['MACD'].iloc[i] < data['Signal'].iloc[i]:
        signals_array[0] = -1  # Sell
    else:
        signals_array[0] = 0  # Hold

    # Update Bollinger Bands Signal
    if (
        data['Close'].iloc[i] < data['LB'].iloc[i]
        and data['Close'].iloc[i - 1] >= data['LB'].iloc[i - 1]
        and data['Close'].iloc[i] < data['SMA20'].iloc[i]
    ):
        signals_array[1] = -1  # Sell
    elif (
        data['Close'].iloc[i] > data['UB'].iloc[i]
        and data['Close'].iloc[i - 1] <= data['UB'].iloc[i - 1]
        and data['Close'].iloc[i] > data['SMA20'].iloc[i]
    ):
        signals_array[1] = 1  # Buy
    else:
        signals_array[1] = 0  # Hold

    # Update SMA200 Signal
    if data['Close'].iloc[i] > data['SMA200'].iloc[i] and data['Close'].iloc[i - 1] <= data['SMA200'].iloc[i - 1]:
        signals_array[2] = 1  # Buy
    elif data['Close'].iloc[i] < data['SMA200'].iloc[i] and data['Close'].iloc[i - 1] >= data['SMA200'].iloc[i - 1]:
        signals_array[2] = -1  # Sell
    else:
        signals_array[2] = 0  # Hold

    # Update RSI Signal
    if data['RSI'].iloc[i] < 30:  # Buy when RSI is below 30
        signals_array[3] = 1  # Buy
    elif data['RSI'].iloc[i] > 70:  # Sell when RSI is above 70
        signals_array[3] = -1  # Sell
    else:
        signals_array[3] = 0  # Hold

    # Update SMA50 Signal
    if data['Close'].iloc[i] > data['SMA50'].iloc[i] and data['Close'].iloc[i - 1] <= data['SMA50'].iloc[i - 1]:
        signals_array[4] = 1  # Buy
    elif data['Close'].iloc[i] < data['SMA50'].iloc[i] and data['Close'].iloc[i - 1] >= data['SMA50'].iloc[i - 1]:
        signals_array[4] = -1  # Sell
    else:
        signals_array[4] = 0  # Hold
    # Update XGBoost Signal
    xgb_signal = xgb_model.predict(xgb_features)

    # Buy signal
    if signals_array.count(1) >= 2 and balance > 0:
        balance -= data['Close'].iloc[i]
        stocks_held += 1
        buy_price = data['Close'].iloc[i]
        add_message(f"At {data['Close'].iloc[i]}, Bought 1 stock. Balance: {balance}, Stocks held: {stocks_held}")

    # Sell signal
    elif signals_array.count(-1) >= 2 and stocks_held > 0:
        balance += stocks_held * data['Close'].iloc[i]
        stocks_held = 0
        profit_loss = data['Close'].iloc[i] - buy_price
        add_message(f"At {data['Close'].iloc[i]}, Sold all stocks. Balance: {balance}, Stocks held: {stocks_held}, Profit/Loss: {profit_loss}")

final_balance = balance + stocks_held * data['Close'].iloc[-1]
add_message(f"\nInitial Balance: {initial_balance}, Final Balance: {final_balance}, Profit/Loss: {final_balance - initial_balance}")

window.after(1000, update_gui)
window.mainloop()