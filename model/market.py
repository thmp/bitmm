import math
import time, requests

class MarketModel(object):

    def __init__(self, book):
        self.width = 0.75
        self.size = 5

        self.orderbook = book

        self.own_bid_id = ""
        self.own_ask_id = ""

        self.own_bid = 0
        self.own_ask = 0

        self.own_bid_size = 0
        self.own_ask_size = 0

        self.balance_btc = 1.0
        self.balance_eur = 100.0 # in full euro units

        self.max_size = 0.03 # in BTC

        self.output = ""

        self._usd_in_eur_lastupdate = 0

    def get_in_euro(self, price):
        if time.time() - self._usd_in_eur_lastupdate > 120:

            print "Updating FX rate"

            res = requests.get('http://finance.yahoo.com/webservice/v1/symbols/allcurrencies/quote?format=json') # &view=detail

            for resource in res.json()['list']['resources']:
                if resource['resource']['fields']['symbol'] == 'EUR=X':
                    self._rate = float(resource['resource']['fields']['price'])
                    self._usd_in_eur_lastupdate = time.time()

        return price * self._rate

    def reset(self):
        self.own_bid = 0
        self.own_ask = 0
        self.own_bid_id = ""
        self.own_ask_id = ""
        self.own_bid_size = 0
        self.own_ask_size = 0

    def calculateFairValueOld(self, book):
        """ Calculate the fair value based on the current asks and bids w/o own asks and bids """
        #best_ask, best_bid, spread = book.calculateSpread()
        if self.own_ask == float(book.asks[0]["price"]) and int(book.asks[0]["size"]) == self.own_ask_size:
            best_ask = float(book.asks[1]["price"])
        else:
            best_ask = float(book.asks[0]["price"])

        if self.own_bid == float(book.bids[0]["price"]) and int(book.bids[0]["size"]) == self.own_bid_size:
            best_bid = float(book.bids[1]["price"])
        else:
            best_bid = float(book.bids[0]["price"])

        return (best_bid + best_ask) / 2.0, best_ask, best_bid, best_ask - best_bid

    def calculateFairValue(self, book):

        best_bid = 0
        best_ask = 100000
        for i in range(len(book.bids)):
            if float(book.bids[i][0]) > best_bid and str(book.bids[i][2]) != str(self.own_bid_id):
                best_bid = float(book.bids[i][0])
        for i in range(len(book.asks)):
            if float(book.asks[i][0]) < best_ask and str(book.asks[i][2]) != str(self.own_ask_id):
                best_ask = float(book.asks[i][0])

        #print (best_bid + best_ask) / 2.0, best_ask, best_bid, best_ask - best_bid

        return (best_bid + best_ask) / 2.0, best_ask, best_bid, best_ask - best_bid

    def adjustOrders(self, book, book_usd=None):



        # get maximum size
        self.max_size = math.floor(self.getTotalBTCBalance() * 0.40 *10000.0)/10000.0 # 20 % of assets maximum order size
        # calculation should be changed, use available funds and %

        # max ask size, sell: we need to have at least 20% BTC
        #if self.balance_btc < self.getTotalBTCBalance()*0.2:
        #	max_ask_size = 0.0
        #else:
        #	max_ask_size = self.balance_btc - self.getTotalBTCBalance()*0.4

        # max bid size, buy: we can maximum have 80% BTC
        #if self.balance_btc > self.getTotalBTCBalance()*0.8:
        #max_bid_size = 0.0
        #else:
        #max_bid_size = self.getTotalBTCBalance()*0.8 - self.balance_btc

        max_ask_size = self.balance_btc #- self.getTotalBTCBalance()
        max_bid_size = self.getTotalBTCBalance() - self.balance_btc

        fair_value_euro, ask, bid, spread = self.calculateFairValue(book)
        #fair_value, _, _, _ = self.calculateFairValue(book_usd)
        fair_value = fair_value_euro

        #print "Adjust..."
        #print fair_value, ask, bid, spread, self.own_ask, self.own_bid

        if spread < 0 or spread > 25:
            print "WARNING"
            #book.printTopOfBook()
            return False, False

        if fair_value > 10000:
            fair_value = fair_value_euro
        #fair_value = self.get_in_euro(fair_value)

        own_ask = fair_value + self.width / 2.0
        own_bid = fair_value - self.width / 2.0

        if False: # set strategy to not be agressive
            if own_bid > bid:
                own_bid = bid + 0.01 if ask != (bid + 0.01) else bid

            if own_ask < ask:
                own_ask = ask - 0.01 if bid != (ask - 0.01) else ask

        if False:
            if own_bid >= ask:
                own_bid /= (1+.0025)
                #own_bid = bid + 0.01 if ask != (bid + 0.01) else bid

            if own_ask <= bid:
                own_ask /= (1-.0025)
                #own_ask = ask - 0.01 if bid != (ask - 0.01) else ask

        if True:
            INHERENT_SPREAD = 0.4
            #if spread > 0.05:
                # if we have more btc, sell high
            if self.balance_btc > self.getTotalBTCBalance()*0.5:
                own_ask = ask - 0.01
                own_bid = own_ask - INHERENT_SPREAD
            else:
                own_bid = bid + 0.01
                own_ask = own_bid + INHERENT_SPREAD

        # JOIN:
        #if spread < self.width:
        #	own_ask = fair_value + self.width / 2.0
        #	own_bid = fair_value - self.width / 2.0
        #else:
        #	own_ask = ask - 0.01
        #	own_bid = bid + 0.01

        if False:
        # jump up the sell order book until total ask size > 0.25
            val = 0.0
            i = 0
            last_ask = ask
            while val < 0.25 and i < 20:
                val += book.totalsize("ask", last_ask)
                if val > 0.25:
                    break
                own_ask, devnull = book.bbo(last_ask)
                last_ask = own_ask
                own_ask = float(own_ask) - 0.01
                i+=1
            # jump down the buy order book until total bid size > 0.25
            val = 0.0
            i = 0
            last_bid = bid
            while val < 0.25 and i < 20:
                val += book.totalsize("bid", last_bid)
                if val > 0.25:
                    break
                devnull, own_bid = book.bbo(0.0, last_bid)
                last_bid = own_bid
                own_bid = float(own_bid) + 0.01
                i+=1

        new_ask = round(own_ask*100.0)/100.0
        new_bid = round(own_bid*100.0)/100.0

        # ASK
        #if self.balance_btc < self.max_size:
        #	new_ask_size = math.floor(self.balance_btc*100.0)/100.0
        #else:
        #	new_ask_size = self.max_size

        # BID
        #if self.balance_eur < self.max_size*new_bid:
        #	new_bid_size = math.floor(self.balance_eur/new_bid*100.0)/100.0
        #else:
        #	new_bid_size = self.max_size

        new_bid_size = round(max_bid_size/2.0*10000.0)/10000.0 # by dividing by two we can try to stick around 50/50 BTC EUR
        if new_bid_size < 0.01:
            new_bid_size = 0.0 # coinbase does not accept less than 0.01
        new_ask_size = round(max_ask_size/2.0*10000.0)/10000.0
        if new_ask_size < 0.01:
            new_ask_size = 0.0

        ask_changed = self.own_ask != new_ask or self.own_ask_size != new_ask_size
        bid_changed = self.own_bid != new_bid or self.own_bid_size != new_bid_size

        self.own_ask = new_ask
        self.own_ask_size = new_ask_size

        self.own_bid = new_bid
        self.own_bid_size = new_bid_size

        # Information output

        btc = round((self.balance_btc + self.balance_eur/ask)*10000)/10000.0
        eur = round((self.balance_eur + self.balance_btc*bid)*100)/100.0

        output = str(fair_value) + " | " + str(bid) + " - " + str(spread) + " - " + str(ask) + " | " + str(new_bid) + " - " + str(new_ask) + " | BTC " + str(btc) + ", EUR " + str(eur)

        if output != self.output:
            self.output = output
            print output

            if book_usd is not None:
                fair_value, ask, bid, spread = self.calculateFairValue(book_usd)

        return ask_changed, bid_changed, new_ask, new_ask_size, new_bid, new_bid_size

        #if new_ask != self.own_ask:
        #	self.own_ask = new_ask
        #	print "LIMIT ORDER SELL: " + str(new_ask)

        #if new_bid != self.own_bid:
        #	self.own_bid = new_bid
        #	print "LIMIT ORDER BUY:  " + str(new_bid)

    def getTotalBTCBalance(self):
        return self.balance_btc + self.balance_eur/float(self.orderbook.bids[0][0])

    def simulateTrade(self, trade):
        """ [{u'timestamp': 1439235882742, u'price': u'250.01', u'side': u'buy', u'tradeId': 3377007, u'size': 1}] - side:buy:taken from ask orderbook, side:sell:taken from bid orderbook """

        price = float(trade["price"])
        size = float(trade["size"])

        if trade["side"] == "buy":
            # maximum size is my number of bitcoins
            if size/100.0 > self.balance_btc:
                prev_size = size
                size = self.balance_btc*100.0
                print "Partial execution " + str(size) + " of " + str(prev_size)
            if self.own_ask <= price:
                self.balance_btc -= size/100.0
                self.balance_eur += size/100.0 * price
                print "=> Sold BTC " + str(size/100.0) + " for EUR " + str(size/100.0 * price)
            else:
                print "=> Not participated in trade"
        elif trade["side"] == "sell":
            if size/100.0*price > self.balance_eur:
                prev_size = size
                size = self.balance_eur/price*100.0
                print "Partial execution " + str(size) + " of " + str(prev_size)
            if self.own_bid >= price:
                self.balance_btc += size/100.0
                self.balance_eur -= size/100.0 * price
                print "=> Bought BTC " + str(size/100.0) + " for EUR " + str(size/100.0 * price)
            else:
                print "=> Not participated in trade"

        assert self.balance_btc >= 0
        assert self.balance_eur >= 0

    def printFunds(self):
        print "BALANCE BTC " + str(self.balance_btc)
        print "BALANCE EUR " + str(self.balance_eur)
        print "  TOTAL BTC " + str(self.getTotalBTCBalance())