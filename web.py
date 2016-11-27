from flask import Flask, jsonify, request, Response
from functools import wraps
from gateway.coinbase import CoinbaseGateway
import requests
import datetime
import hashlib


# from: http://flask.pocoo.org/snippets/8/
def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'admin' and password == ''

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

gateway = CoinbaseGateway()
app = Flask(__name__, static_url_path='/static', static_folder='static')

def getOrderbook():
	#r = requests.get('http://api.exchange.coinbase.com/products/BTC-EUR/book?level=2')
	#orderbook = r.json()
	orderbook = gateway.getOrderbookAggregated()
	orders = gateway.getAllOrders()
	for order in orders:
		#print order
		if order["side"] == "buy":
			for i in range(len(orderbook["bids"])):
				if int(float(order["price"])*100) == int(float(orderbook["bids"][i][0])*100):
					if len(orderbook["bids"][i]) == 3:
						orderbook["bids"][i].append(float(order["size"]) - float(order["filled_size"]))
					else:
						orderbook["bids"][i][3] = float(orderbook["bids"][i][3]) + float(order["size"]) - float(order["filled_size"])
		if order["side"] == "sell":
			for i in range(len(orderbook["asks"])):
				if int(float(order["price"])*100) == int(float(orderbook["asks"][i][0])*100):
					if len(orderbook["asks"][i]) == 3:
						orderbook["asks"][i].append(order["size"])
					else:
						orderbook["asks"][i][3] = float(orderbook["asks"][i][3]) + float(order["size"])
	return orderbook

@app.route('/')
@requires_auth
def index():
	return app.send_static_file('index.html')

@app.route('/account')
@requires_auth
def account():
	orderbook = gateway.getOrderbookAggregated(level=1)

	btc, eur = gateway.getAvailableFunds()
	total_eur = eur + btc*float(orderbook["bids"][0][0])
	total_btc = btc + eur/float(orderbook["asks"][0][0])

	return jsonify({"btc": btc, "total_btc": total_btc, "eur": eur, "total_eur": total_eur})

@app.route('/orderbook')
@requires_auth
def orderbook():
	return jsonify(getOrderbook())

@app.route('/trades')
@requires_auth
def trades():
	orderbook = gateway.getOrderbookAggregated(level=1)

	volume_eur = 0.0
	volume_btc = 0.0
	balance_eur = 0.0
	balance_btc = 0.0

	volume_eur_day = 0.0
	volume_btc_day = 0.0
	balance_eur_day = 0.0
	balance_btc_day = 0.0

	today = datetime.datetime.now().strftime("%Y-%m-%d")

	trades = gateway.getTrades(86400)
	trades_count_day = 0

	for trade in trades:
		volume_eur += float(trade["size"])*float(trade["price"])
		volume_btc += float(trade["size"])
		if trade["created_at"][:10] == today:
			trades_count_day += 1
			volume_eur_day += float(trade["size"])*float(trade["price"])
			volume_btc_day += float(trade["size"])
		if trade["side"] == "buy":
			balance_btc += float(trade["size"])
			balance_eur -= float(trade["size"])*float(trade["price"])
			if trade["created_at"][:10] == today:
				balance_btc_day += float(trade["size"])
				balance_eur_day -= float(trade["size"])*float(trade["price"])
		else:
			balance_btc -= float(trade["size"])
			balance_eur += float(trade["size"])*float(trade["price"])
			if trade["created_at"][:10] == today:
				balance_btc_day -= float(trade["size"])
				balance_eur_day += float(trade["size"])*float(trade["price"])


	#print balance_eur
	#print balance_btc
	balance_eur_tmp = balance_eur
	balance_eur += balance_btc*float(orderbook["bids"][0][0])
	balance_btc += balance_eur_tmp/float(orderbook["asks"][0][0])

	balance_eur_tmp_day = balance_eur_day
	balance_eur_day += balance_btc_day*float(orderbook["bids"][0][0])
	balance_btc_day += balance_eur_tmp_day/float(orderbook["asks"][0][0])

	return jsonify({"trades": trades, "volume_eur": volume_eur, "volume_btc": volume_btc, "balance_eur": balance_eur, "balance_btc": balance_btc, "volume_btc_day": volume_btc_day, "volume_eur_day": volume_eur_day, "balance_btc_day": balance_btc_day, "balance_eur_day": balance_eur_day, "trades_count_day": trades_count_day})

@app.route('/orders')
@requires_auth
def orders():
	#print gateway.getAllOrders()
	return jsonify({"orders": gateway.getAllOrders()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)