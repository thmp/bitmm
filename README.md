# bitmm

Market making bot for bitcoin exchanges

<dl>
  <dt>IMPORTANT NOTE</dt>
  <dd>This is an early version and might not function as expected, do not use this with live accounts</dd>
</dl>

Bitmm is a market making bot for bitcoin exchanges. It continuously opens and updates buy and sell orders at a
bitcoin exchange, earning the spread once both orders are executed. The bot supports different exchanges (currently,
Coinbase and HitBTC are implemented) and various quotation strategies. 

The bot keeps an updated orderbook of the exchange, connecting to the exchange feed (via websocket). From the orderbook,
the current bid and ask quotes are analyzed and own orders are openend or updated. 

The quotation strategy supports jumping up the orderbook with a minimal spread or quoting according to a different 
exchange or exchange pair. 

The bot exposes are web interface, where orderbook, trades and orders can be monitored

## Setup

* Create venv `virtualenv venv`
* Activate `source venv/bin/activate`
* Install requirements `pip install -r requirements.txt`

## Server

* Connect to server `ssh -i ...pem user@host`
* Start a session with `screen` detach from screen with `Ctrl + a`, `d` 
* Reattach to screen with `screen -r`

* To start the web interface, create a new screen with `Ctrl + a`, `c`
* Run flask with `python web.py`

## Web interface

The web interface is made available on port 5000