import json
import MySQLdb

SYMBOL = "BTCEUR"

class HitbtcAdapter(object):

    def __init__(self, orderbook, model, gateway, storage=False):
        self.orderbook = orderbook
        self.model = model
        self.gateway = gateway

        self.received_full = False

        self.storage = storage
        if storage:
            self.conn = MySQLdb.connect(host= "", user="", passwd="", db="")
            self.cur = self.conn.cursor()
            self.count = 0

        self.updateBalance()

    def processMessage(self, message):
        msg = json.loads(message)

        if "MarketDataSnapshotFullRefresh" in msg.keys():
            self.received_full = True
            self.processFullRefresh(msg["MarketDataSnapshotFullRefresh"])
            if self.storage and msg["MarketDataSnapshotFullRefresh"]["symbol"] == SYMBOL:
                self.storeMessage(message)
        elif self.received_full:
            self.processIncrementalRefresh(msg["MarketDataIncrementalRefresh"])
            if self.storage and msg["MarketDataIncrementalRefresh"]["symbol"] == SYMBOL:
                self.storeMessage(message)

    def processFullRefresh(self, msg):
        if msg["symbol"] == SYMBOL:
            self.orderbook.updateOrderbookFull(msg["ask"], msg["bid"])
            #self.adjustOrders()
        else:
            pass

    def processIncrementalRefresh(self, msg):
        if msg["symbol"] == SYMBOL:
            self.processTrade(msg)
            self.orderbook.updateOrderbookIncremental(msg["ask"], msg["bid"])
            self.adjustOrders()
        else:
            pass

    def processTrade(self, msg):
        if len(msg["trade"]) > 0:
            print " "
            print "Trade..."
            print msg["trade"]
            self.orderbook.printTopOfBook()
            #for trade in msg["trade"]:
                #self.model.simulateTrade(trade)
            self.updateBalance()
            self.adjustOrders()
            self.model.printFunds()

    def storeMessage(self, msg):
        print "Message " + str(self.count) + " stored"
        self.count += 1
        self.cur.execute("""INSERT INTO messages (message) VALUES (%s)""", [msg])

    def updateBalance(self):
        btc, eur = self.gateway.getAvailableFunds()
        self.model.balance_btc = btc
        self.model.balance_eur = eur

    def adjustOrders(self):
        ask_changed, bid_changed = self.model.adjustOrders(self.orderbook)

        if ask_changed:
            self.gateway.cancelSellOrder()
            if self.model.own_ask_size > 0:
                self.orderbook.printTopOfBook()
                print "LIMIT ORDER SELL: " + str(self.model.own_ask) + " (" + str(self.model.own_ask_size) + ")"
                self.gateway.placeOrder("sell", self.model.own_ask_size, self.model.own_ask)

        if bid_changed:
            self.gateway.cancelBuyOrder()
            if self.model.own_bid_size > 0:
                self.orderbook.printTopOfBook()
                print "LIMIT ORDER BUY:  " + str(self.model.own_bid) + " (" + str(self.model.own_bid_size) + ")"
                self.gateway.placeOrder("buy", self.model.own_bid_size, self.model.own_bid)



