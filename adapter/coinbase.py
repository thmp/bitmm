import json
import MySQLdb
import time

SYMBOL = "BTCEUR"
TRADING = True
INTERVAL = 2.0

class CoinbaseAdapter(object):

    def __init__(self, orderbook, model, gateway, storage=False, orderbook_usd = None):
        self.orderbook_initialized = False

        self.orderbook = orderbook
        self.orderbook_usd = orderbook_usd

        self.model = model
        self.gateway = gateway

        self.received_full = False

        self.storage = storage
        if storage:
            self.conn = MySQLdb.connect(host="", user="", passwd="", db="")
            self.cur = self.conn.cursor()
            self.count = 0

        self.updateBalance()

        self.processed = 0

        self.ask_set = 0
        self.bid_set = 0

        self.lastOldOrderRemoval = time.time()

    def initializeOrderbook(self, product_id=None):
        init_usd = product_id != "BTC-EUR"
        init_eur = product_id != "BTC-USD"

        if init_eur:

            print "Initialize orderbook (EUR)... "
            self.gateway.cancelAllOrders()
            self.model.reset()

            book = self.gateway.getOrderbook()
            self.orderbook.updateOrderbookFull(book['asks'], book['bids'], book["sequence"])
            self.orderbook.applyOrderbookUpdates()
            self.adjustOrders()
            self.model.printFunds()


        if init_usd and self.orderbook_usd is not None:

            print "Initialize orderbook (USD)... "
            book = self.gateway.getOrderbook(product_id="BTC-USD")
            self.orderbook_usd.updateOrderbookFull(book['asks'], book['bids'], book["sequence"])
            self.orderbook_usd.applyOrderbookUpdates()

    def processMessage(self, message):
        #print "Message" + message[:50]
        # only start processing messages once orderbook has been initialized, start with first sequence no.
        msg = json.loads(message)

        if msg["type"] == "match" and msg["product_id"] == "BTC-EUR":
            print " => TRADE at", msg["price"], "(", msg["size"], ")"
            btc, eur = self.gateway.getAvailableFunds()
            self.model.balance_btc = btc
            self.model.balance_eur = eur

            # if a trade occured where we were involved, cancel current orders and set new ones
            # we should always be the maker, if we were the taker, do not cancel the order and
            # create a new one, but send a warning message
            if msg["maker_order_id"] == self.gateway.buyorder or msg["maker_order_id"] == self.gateway.sellorder:
                self.gateway.cancelAllOrders()
                self.model.reset()


        if msg["product_id"] == "BTC-EUR":
            self.orderbook.updateOrderbookIncremental(msg)
            if not self.orderbook.applyOrderbookUpdates():
                # wrong sequence number
                self.initializeOrderbook()
                self.orderbook.update_requested = False
                #print "WARNING INIT AGAIN"

        elif msg["product_id"] == "BTC-USD":
            self.orderbook_usd.updateOrderbookIncremental(msg)
            if not self.orderbook_usd.applyOrderbookUpdates():
                # wrong sequence number
                self.initializeOrderbook()
                self.orderbook.update_requested = False
                #print "WARNING INIT AGAIN"

        self.adjustOrders()

        if time.time() - self.lastOldOrderRemoval > 30:
            self.removeOldOrders()
            self.lastOldOrderRemoval = time.time()

        #self.processed += 1
        #if self.processed > 200:
        #	self.processed = 0
        #	self.initializeOrderbook()

    def storeMessage(self, msg):
        print "Message " + str(self.count) + " stored"
        self.count += 1
        self.cur.execute("""INSERT INTO messages (message) VALUES (%s)""", [msg])

    def updateBalance(self):
        btc, eur = self.gateway.getAvailableFunds()
        self.model.balance_btc = btc
        self.model.balance_eur = eur

    def removeOldOrders(self):
        """ Due to the high frequency of trades some orders can stay in the book and are not cancelled by the algorithm (possibly bug?), these are purged every 30s """
        orders = self.gateway.getAllOrders()
        for order in orders:
            if order["side"] == "buy":
                if order["id"] != self.model.own_bid_id:
                    print "OLD ORDER FOUND, CANCELLING"
                    self.gateway.cancelOrder(order["id"])
            if order["side"] == "sell":
                if order["id"] != self.model.own_ask_id:
                    print "OLD ORDER FOUND, CANCELLING"
                    self.gateway.cancelOrder(order["id"])

    def adjustOrders(self):
        ask_changed, bid_changed, new_ask, new_ask_size, new_bid, new_bid_size = self.model.adjustOrders(self.orderbook, book_usd=self.orderbook_usd)

        if ask_changed:
            if new_ask_size > 0:
                #self.orderbook.printTopOfBook()
                #print "LIMIT ORDER SELL: " + str(new_ask) + " (" + str(new_ask_size) + ")"
                if TRADING and time.time() - self.ask_set > INTERVAL:
                    print "LIMIT ORDER SELL: " + str(new_ask) + " (" + str(new_ask_size) + ")"
                    self.ask_set = time.time()
                    self.gateway.cancelSellOrder()
                    idx = self.gateway.placeOrder("sell", new_ask_size, new_ask)
                    self.model.own_ask = new_ask
                    self.model.own_ask_size = new_ask_size
                    self.model.own_ask_id = idx
                else:
                    pass
                    #print "PAUSING FOR TRADE UPDATE"

        if bid_changed:
            if new_bid_size > 0:
                #self.orderbook.printTopOfBook()
                #print "LIMIT ORDER BUY:  " + str(new_bid) + " (" + str(new_bid_size) + ")"
                if TRADING and time.time() - self.bid_set > INTERVAL:
                    print "LIMIT ORDER BUY:  " + str(new_bid) + " (" + str(new_bid_size) + ")"
                    self.bid_set = time.time()
                    self.gateway.cancelBuyOrder()
                    idx = self.gateway.placeOrder("buy", new_bid_size, new_bid)
                    self.model.own_bid = new_bid
                    self.model.own_bid_size = new_bid_size
                    self.model.own_bid_id = idx
                else:
                    pass
                    #print "PAUSING FOR TRADE UPDATE"


