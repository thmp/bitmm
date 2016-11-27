import json, hmac, hashlib, time, requests, base64, uuid
from requests.auth import AuthBase

import datetime, time

from twisted.internet import reactor
from autobahn.twisted.websocket import WebSocketClientFactory, WebSocketClientProtocol, connectWS

from utilities.logger import FileLogger

# Create custom authentication for Exchange
class CoinbaseExchangeAuth(AuthBase):
    def __init__(self, api_key, secret_key, passphrase):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase

    def __call__(self, request):
        timestamp = str(time.time())
        message = timestamp + request.method + request.path_url + (request.body or '')
        hmac_key = base64.b64decode(self.secret_key)
        signature = hmac.new(hmac_key, message, hashlib.sha256)
        signature_b64 = signature.digest().encode('base64').rstrip('\n')

        request.headers.update({
            'CB-ACCESS-SIGN': signature_b64,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-PASSPHRASE': self.passphrase,
        })
        return request

class CoinbaseGateway(object):

    def __init__(self):

        self.buyorder = None
        self.sellorder = None

        self.endpoint = "https://api.exchange.coinbase.com"
        #self.endpoint = "http://demo-api.hitbtc.com"

        # Live Keys
        self.api_key = ""
        self.secret = ""
        self.passphrase = ""

        self.auth = CoinbaseExchangeAuth(self.api_key, self.secret, self.passphrase)

        self.logger = FileLogger("coinbase-orderbook")

    def setMessageCallback(self, callback):
        self.callback = callback

    def nonce(self):
        return str(uuid.uuid4())

    def sendSignedGetRequest(self, uri, raw=False):
        r = requests.get(self.endpoint + uri, auth=self.auth)

        if raw:
            return r.json(), r
        else:
            return r.json()

    def sendSignedDeleteRequest(self, uri):
        r = requests.delete(self.endpoint + uri, auth=self.auth)

    def sendSignedPostRequest(self, uri, data):
        r = requests.post(self.endpoint + uri, json=data, auth=self.auth)
        return r.json()

    def getAvailableFunds(self):
        accounts = self.sendSignedGetRequest("/accounts")
        #print accounts
        for account in accounts:
            if account["currency"] == "BTC":
                btc = float(account["balance"]) # balance, available, hold
            if account["currency"] == "EUR":
                eur = float(account["balance"])
        return btc, eur

    def getOrderbook(self, product_id="BTC-EUR"):
        orderbook = self.sendSignedGetRequest("/products/"+product_id+"/book?level=3")
        self.logger.log(json.dumps(orderbook))
        return orderbook

    def getOrderbookAggregated(self, level=2):
        return self.sendSignedGetRequest("/products/BTC-EUR/book?level="+str(level))

    def parseTime(self, trade):
        #print trade
        t = datetime.datetime.strptime(trade["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ")
        return time.mktime(t.timetuple())

    def getTrades(self, timeframe=86400):
        trades = []

        ntrades, response = self.sendSignedGetRequest("/fills", raw=True)
        newest = self.parseTime(ntrades[0])

        for trade in ntrades:
            if newest - self.parseTime(trade) < timeframe:
                trades.append(trade)

        while newest - self.parseTime(trades[len(trades)-1]) < timeframe and "cb-after" in response.headers:
            #print "while"
            ntrades, response = self.sendSignedGetRequest("/fills?after="+response.headers["cb-after"], raw=True)
            for trade in ntrades:
                if newest - self.parseTime(trade) < timeframe:
                    trades.append(trade)

        return trades

    def placeOrder(self, side, size, price):
        print "Placing order ", side, size, price

        idx = self.nonce()
        order = {
            "side": side,
            "product_id": "BTC-EUR",
            "client_oid": self.nonce(),
            "price": price, # per bitcoin
            "size": size, # in bitcoin!!
            "post_only": True # prevent liquidity taking orders
        }
        data = self.sendSignedPostRequest("/orders", order)
        #print data

        if not data["id"]:
            print "ERROR PLACING ORDER", data
            return None

        if side == "sell":
            self.sellorder = data['id']
        else:
            self.buyorder = data['id']
        #print "Created " + data['id']
        return data['id']

    def cancelOrder(self, orderId):
        #print "Cancelling " + orderId
        return self.sendSignedDeleteRequest("/orders/" + orderId)

    def cancelSellOrder(self):
        if self.sellorder != None:
            self.cancelOrder(self.sellorder)

    def cancelBuyOrder(self):
        if self.buyorder != None:
            self.cancelOrder(self.buyorder)

    def getAllOrders(self):
        return self.sendSignedGetRequest("/orders")

    def cancelAllOrders(self):
        orders = self.getAllOrders()
        for order in orders:
            self.cancelOrder(order['id'])

    def reconnect(self):
        print "Reconnecting to websocket..."
        factory = WebSocketClientFactory("wss://ws-feed.exchange.coinbase.com")
        TradingDataProtocol.setMessageCallback(self.callback)
        TradingDataProtocol.setCloseCallback(self.reconnect)
        factory.protocol = TradingDataProtocol
        connectWS(factory)

    def run(self):
        print "Connecting to websocket..."
        factory = WebSocketClientFactory("wss://ws-feed.exchange.coinbase.com")
        TradingDataProtocol.setMessageCallback(self.callback)
        TradingDataProtocol.setCloseCallback(self.reconnect)
        factory.protocol = TradingDataProtocol
        connectWS(factory)
        reactor.run()

class TradingDataProtocol(WebSocketClientProtocol):

    @staticmethod
    def setMessageCallback(callback):
        TradingDataProtocol.callback = callback

    @staticmethod
    def setCloseCallback(callback):
        TradingDataProtocol.close_callback = callback

    def processMessage(self, message):
        TradingDataProtocol.callback(message)

    def logMessage(self, message):
        self.logger.log(message)

    def onOpen(self):
        print "Start reading stream..."
        self.logger = FileLogger("coinbase-messages")
        self.sendMessage(json.dumps({"type":"subscribe","product_id":"BTC-EUR"}))
        #self.sendMessage(json.dumps({"type":"subscribe","product_id":"BTC-USD"}))

    def onPing(self):
        print "Send pong"
        self.sendPong()

    def onClose(self, wasClean, code, reason):
        print "Warning: websocket connection closed"
        print code
        print reason
        if not wasClean:
            print "no clean close"
        TradingDataProtocol.close_callback()

    def onMessage(self, msg, binary):
        reactor.callLater(0, self.processMessage, msg)
        reactor.callLater(0, self.logMessage, msg)

if __name__ == '__main__':

    gateway = CoinbaseGateway()

    print "Funds"
    print gateway.getAvailableFunds()

    idx = gateway.placeOrder("sell", 0.01, 249.0)
    print "Created " + idx

    gateway.cancelAllOrders()

    print gateway.getAllOrders()

    gateway.setMessageCallback(lambda x: x)
    gateway.run()


