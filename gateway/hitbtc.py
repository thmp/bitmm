from twisted.internet import reactor
from autobahn.twisted.websocket import WebSocketClientFactory, WebSocketClientProtocol, connectWS
import json
import hmac, hashlib, base64
import time
import requests
import MySQLdb

SYMBOL = "BTCEUR"

class HitbtcGateway(object):

    def __init__(self):

        self.buyorder = None
        self.sellorder = None

        self.endpoint = "http://api.hitbtc.com"
        #self.endpoint = "http://demo-api.hitbtc.com"

        # Live Keys
        self.api_key = ""
        self.secret = ""

        # Demo Keys
        #self.api_key = ""
        #self.secret = ""

        print "Funds BTC/EUR: ", self.getAvailableFunds()
        #self.placeOrder("sell", 1, 270.0)

        self.cancelAllOrders()

    def setMessageCallback(self, callback):
        self.callback = callback

    def nonce(self):
        return int(time.time()*100000)

    def info(self):
        return "apikey=" + self.api_key + "&nonce=" + str(self.nonce())

    def getAvailableFunds(self):
        balance = self.getBalance()
        btc = 0
        eur = 0
        for item in balance['balance']:
            if item['currency_code'] == 'BTC':
                btc = item['cash'] + item['reserved']
            if item['currency_code'] == 'EUR' and SYMBOL == "BTCEUR":
                eur = item['cash'] + item['reserved']
            if item['currency_code'] == 'USD' and SYMBOL == "BTCUSD":
                eur = item['cash'] + item['reserved']
        return btc, eur

    def getBalance(self):
        return self.sendSignedGetRequest("/api/1/trading/balance?" + self.info())


    def placeOrder(self, side, size, price):
        self.placeOrderStreaming(side, size, price)

    def placeOrderRest(self, side, size, price):
        idx = self.nonce()
        self.sendSignedPostRequest("/api/1/trading/new_order?" + self.info(),
            "clientOrderId=" + str(idx) + "&timeInForce=GTC&symbol="+SYMBOL+"&type=limit&side=" + side + "&quantity=" + str(size) + "&price=" + str(price)
            )
        #print "Placing order with idx " + str(idx)
        print "Placing: clientOrderId=" + str(idx) + "&timeInForce=GTC&symbol="+SYMBOL+"&type=limit&side=" + side + "&quantity=" + str(size) + "&price=" + str(price)
        if side == "buy":
            self.buyorder = idx
        else:
            self.sellorder = idx
        return idx

    def placeOrderStreaming(self, side, size, price):
        idx = self.nonce()
        print side, size, price
        HitbtcGateway.trading_protocol.sendSignedMessage({
            "NewOrder": {
                "clientOrderId": str(idx),
                "symbol": SYMBOL,
                "side": side,
                "quantity": size,
                "type": "limit",
                "price": price,
                "timeInForce": "GTC"
            }
            })
        if side == "buy":
            self.buyorder = idx
        else:
            self.sellorder = idx
        return idx

    def getAllOrders(self):
        orders = self.sendSignedGetRequest("/api/1/trading/orders/active?" + self.info())
        #print "All orders", orders
        return orders["orders"]

    def cancelAllOrders(self):
        orders = self.getAllOrders()
        for order in orders:
            self.cancelOrderRest(order["clientOrderId"], order["side"])


    def cancelSellOrder(self):
        if self.sellorder != None:
            self.cancelOrder(self.sellorder, "sell")

    def cancelBuyOrder(self):
        if self.buyorder != None:
            self.cancelOrder(self.buyorder, "buy")

    def cancelOrder(self, clientOrderId, side):
        self.cancelOrderStreaming(clientOrderId, side)

    def cancelOrderRest(self, clientOrderId, side):
        idx = self.nonce()
        self.sendSignedPostRequest("/api/1/trading/cancel_order?" + self.info(),
            "clientOrderId=" + str(clientOrderId) + "&symbol="+SYMBOL+"&cancelRequestClientOrderId=" + str(idx) + "&side=" + side
            )
        #print "Cancelling order with idx " + str(clientOrderId)
        return idx

    def cancelOrderStreaming(self, clientOrderId, side):
        idx = self.nonce()
        HitbtcGateway.trading_protocol.sendSignedMessage({
            "OrderCancel": {
                "clientOrderId": str(clientOrderId),
                "cancelRequestClientOrderId":   str(idx),
                "symbol": SYMBOL,
                "side": side
            }
            })
        return idx

    def sendSignedGetRequest(self, uri):
        signature = hmac.new(self.secret, msg=uri, digestmod=hashlib.sha512).digest().encode("hex")
        r = requests.get(self.endpoint + uri, headers={"X-Signature": signature})
        #print r, r.text, r.raw
        return r.json()

    def sendSignedPostRequest(self, uri, postData):
        signature = hmac.new(self.secret, msg=uri+postData, digestmod=hashlib.sha512).digest().encode("hex")
        r = requests.post(self.endpoint + uri, headers={"X-Signature": signature}, data=postData)
        #print r, r.text, r.json()
        return r.json()

    def run(self):
        print "Starting up..."
        factory = WebSocketClientFactory("ws://api.hitbtc.com:80")
        #factory = WebSocketClientFactory("ws://demo-api.hitbtc.com:80")
        EchoClientProtocol.setMessageCallback(self.callback)
        factory.protocol = EchoClientProtocol
        connectWS(factory)
        #reactor.run()

        factory2 = WebSocketClientFactory("wss://api.hitbtc.com:8080")
        #factory2 = WebSocketClientFactory("ws://demo-api.hitbtc.com:8080")
        factory2.protocol = TradingProtocol
        connectWS(factory2)
        reactor.run()

class TradingProtocol(WebSocketClientProtocol):

    def __init__(self):
        self.nonce = 0
        self.api_key = ""
        self.secret = ""

        print "Set trading protocol"
        HitbtcGateway.trading_protocol = self

    def onConnect(self, response):
        print("Server connected: {0}".format(response.peer))

    def processMessage(self, message):
        print message

    def onOpen(self):
        print "Connected to trading api..."
        print "Logging in..."
        self.sendLogin()

    def sendLogin(self):
        self.sendSignedMessage({"Login": {}})

    def onMessage(self, msg, binary):
        reactor.callLater(0, self.processMessage, msg)

    def sendSignedMessage(self, payload):
        message = {
            "apikey": self.api_key,
            "signature": "",
            "message": {
                "nonce": self.nonce,
                "payload": payload
            }
        }

        message["signature"] = base64.b64encode(hmac.new(self.secret, msg=json.dumps(message["message"], separators=(',', ':')), digestmod=hashlib.sha512).digest())

        #print json.dumps(message, separators=(',', ':'))
        self.sendMessage(json.dumps(message, separators=(',', ':')))

        self.nonce += 1

class EchoClientProtocol(WebSocketClientProtocol):

    @staticmethod
    def setMessageCallback(callback):
        EchoClientProtocol.callback = callback

    def processMessage(self, message):
        EchoClientProtocol.callback(message)

    def processMessageOld(self, msg):

        msg = json.loads(msg)

        if "MarketDataSnapshotFullRefresh" in msg.keys():
            if msg["MarketDataSnapshotFullRefresh"]["symbol"] == SYMBOL:
                self.cur.execute("""INSERT INTO messages (message) VALUES (%s)""", [json.dumps(msg)])
            self.processFullRefresh(msg["MarketDataSnapshotFullRefresh"])
        else:
            self.processIncrementalRefresh(msg["MarketDataIncrementalRefresh"])
            if msg["MarketDataIncrementalRefresh"]["symbol"] == SYMBOL:
                self.cur.execute("""INSERT INTO messages (message) VALUES (%s)""", [json.dumps(msg)])

    def onOpen(self):
        print "Start reading stream..."

    def onMessage(self, msg, binary):
        #print "Got echo: " + msg
        reactor.callLater(0, self.processMessage, msg)

if __name__ == '__main__':
    factory = WebSocketClientFactory("ws://api.hitbtc.com:80")
    #EchoClientProtocol.setMessageCallback(self.callback)
    factory.protocol = EchoClientProtocol
    connectWS(factory)
    reactor.run()