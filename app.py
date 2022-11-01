from flask import Flask, request
from binance.client import Client
import config
import json
import math
import time


app = Flask(__name__)
client1 = Client(api_key=config.api_key, api_secret=config.api_secret)
reduce_qty = 0
reduce_direction = ""
stopQty = 0
entryPrice = 0
@app.route("/", methods =['POST'])
def webhook():
    global reduce_qty
    global reduce_direction
    global stopQty
    global entryPrice

    data = json.loads(request.data)
    sym = "DOTUSDT"
    signal = data["signal"]
    price = data["price"]
    signal = str(signal).upper()


    # -----Trade logic -----#

    # if signal == partial, close reduce_qty
    if signal == "PARTIAL":
        partial_exit = client1.futures_create_order(symbol=sym, side=reduce_direction,type='MARKET',quantity=reduce_qty,
                                                    reduceOnly='true')
        close_all = client1.futures_cancel_all_open_orders(symbol=sym)
        exitBE = client1.futures_create_order(symbol=sym, side="SELL", type='STOP_MARKET', quantity=stopQty,
                                          stopPrice=entryPrice, closePosition=True)

    elif signal == "BUY":
        try:
            close_all = client1.futures_cancel_all_open_orders(symbol=sym)
        except:
            print('no open orders')
        try:
            closePos = client1.futures_create_order(symbol=sym, side=signal, type='MARKET', quantity=10000,
                                                    reduceOnly='true')
        except:
            print("No positions")
        # Max Quantity of coin, --calculate after closing all positions
        price = client1.futures_symbol_ticker(symbol=sym)
        price = float(price["price"])
        balance_dict = client1.futures_account_balance()
        balance = [float(lst['balance']) for lst in balance_dict]
        balance = max(balance)
        qty = int(balance / price)
        qty = (qty * 2) - 30  # 2x leverage
        sl_price = price - 0.00033
        sl_price = math.floor(sl_price * 100000) / 100000

        order = client1.futures_create_order(symbol=sym, side="BUY", type='MARKET', quantity=qty)
        sl = client1.futures_create_order(symbol=sym, side="SELL", type='STOP_MARKET', quantity=qty,
                                          stopPrice=sl_price, closePosition=True)
        stopQty = qty
        reduce_qty = qty // 10
        reduce_direction = "SELL"
        entryPrice = price
        entryPrice = math.floor(entryPrice * 100000) / 100000

    elif signal == "SELL":
        try:
            close_all = client1.futures_cancel_all_open_orders(symbol=sym)
        except:
            print('no open orders')
        try:
            closePos = client1.futures_create_order(symbol=sym, side=signal, type='MARKET', quantity=10000, reduceOnly='true')
        except:
            print("No positions")
        # Max Quantity of coin, --calculate after closing all positions
        price = client1.futures_symbol_ticker(symbol=sym)
        price = float(price["price"])
        balance_dict = client1.futures_account_balance()
        balance = [float(lst['balance']) for lst in balance_dict]
        balance = max(balance)
        qty = int(balance / price)
        qty = (qty * 2) - 30  # 2x leverage
        sl_price = price + 0.00033
        sl_price = math.floor(sl_price * 100000) / 100000

        order = client1.futures_create_order(symbol=sym, side="SELL", type='MARKET', quantity=qty)
        sl = client1.futures_create_order(symbol=sym, side="BUY", type='STOP_MARKET', quantity=qty,
                                          stopPrice=sl_price, closePosition=True)
        stopQty = qty
        reduce_qty = qty // 10
        reduce_direction = "BUY"
        entryPrice = price
        entryPrice = math.floor(entryPrice * 100000) / 100000

    end = time.time()
    print(f'{signal} at {price}')
    return "Order placed"
