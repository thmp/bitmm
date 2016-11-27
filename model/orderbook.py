class CoinbaseOrderbook(object):

    def __init__(self, asks=[], bids=[]):
        self.asks = asks
        self.bids = bids

        self.last_sequence = 0
        self.start_sequence = 0

        self.updates = []
        self.update_requested = False

    def updateOrderbookFull(self, asks, bids, sequence = 0):
        self.asks = asks
        self.bids = bids
        self.start_sequence = sequence
        print "Orderbook at", sequence

        # update arrived
        #self.update_requested = False

    def totalsize(self, side, val):
        total = 0.0
        if side == "ask":
            for i in range(len(self.asks)):
                if float(self.asks[i][0] == val):
                    total += float(self.asks[i][1])
        else:
            for i in range(len(self.bids)):
                if float(self.bids[i][0] == val):
                    total += float(self.bids[i][1])
        return total

    def bbo(self, best_ask_above=0.0, best_bid_below=100000.0):
        best_ask = 100000.0
        best_bid = 0.0

        for i in range(len(self.asks)):
            if float(self.asks[i][0]) < float(best_ask) and float(self.asks[i][0]) > float(best_ask_above):
                best_ask = self.asks[i][0]
        for i in range(len(self.bids)):
            if float(self.bids[i][0]) > float(best_bid) and float(self.bids[i][0]) < float(best_bid_below):
                best_bid = self.bids[i][0]
        return best_ask, best_bid

    def updateOrderbookIncremental(self, msg):
        self.updates.append(msg)

    def applyOrderbookUpdates(self):
        # check if the first elements sequence number is lower or equal to the
        # sequence we got from the orderbook
        #print "Update queue length: ", len(self.updates)
        if len(self.updates) == 0:
            return True

        if len(self.updates) > 1:
            print "WARNING QUEUE FILLING UP", len(self.updates)
            print "Orderbook at", self.start_sequence
            print "First message in queue", self.updates[0]["sequence"]

        msg = self.updates[0]

        # our we require our first message to be below the sequence of the orderbook
        if msg["sequence"] > self.start_sequence+1:
            if not self.update_requested:
                self.update_requested = True
                return False
            return True

        while len(self.updates) > 0 and msg["sequence"] <= self.start_sequence:
            msg = self.updates.pop(0) # take and remove first element

        while len(self.updates) > 0:
            msg = self.updates.pop(0)

            #print "Orderbook at ", self.start_sequence
            #print "Applying update ", msg["sequence"]
            self.start_sequence = msg["sequence"]

            if msg["side"] == "buy":
                if msg["type"] == "open": # order now on the book
                    self.bids.append([msg['price'], msg['remaining_size'], msg['order_id']])
                elif msg["type"] == "done":
                    # delete
                    for i in range(len(self.bids)):
                        if self.bids[i][2] == msg["order_id"]:
                            del self.bids[i]
                            break
                elif msg["type"] == "match":
                    #maker: buy, taker: not in book
                    for i in range(len(self.bids)):
                        if self.bids[i][2] == msg["maker_order_id"]:
                            self.bids[i][0] = msg["price"]
                            self.bids[i][1] = float(self.bids[i][1]) - float(msg["size"])
                            if self.bids[i][1] <= 0.0:
                                del self.bids[i]
                            break
            else: # sell
                if msg["type"] == "open": # order now on the book
                    self.asks.append([msg['price'], msg['remaining_size'], msg['order_id']])
                elif msg["type"] == "done":
                    for i in range(len(self.asks)):
                        if self.asks[i][2] == msg["order_id"]:
                            del self.asks[i]
                            break
                elif msg["type"] == "match":
                    #maker: sell, taker: not in book
                    for i in range(len(self.asks)):
                        if self.asks[i][2] == msg["maker_order_id"]:
                            self.asks[i][0] = msg["price"]
                            self.asks[i][1] = float(self.asks[i][1]) - float(msg["size"])
                            if self.asks[i][1] <= 0.0:
                                del self.asks[i]
                            break

        return True

class Orderbook(object):

    def __init__(self, asks=[], bids=[]):
        self.asks = asks
        self.bids = bids

    def updateOrderbookFull(self, asks, bids):
        """ Perform a full update of the orderbook, asks and bids are expected to be
        in ascending and descending order respectively """
        self.asks = asks
        self.bids = bids

    def updateOrderbookIncremental(self, asks, bids):
        for ask in asks:
            key = self.findKeyByPrice(ask["price"], self.asks)
            # case 0: update size
            if key != None and ask["size"] > 0:
                self.asks[key]["size"] = ask["size"]
            # case 1: remove node
            elif key != None and ask["size"] == 0:
                del self.asks[key]
            # case 2: add new node
            elif key == None:
                inserted = False
                for i in range(len(self.asks)):
                    if float(ask["price"]) < float(self.asks[i]["price"]):
                        self.asks.insert(i, ask)
                        inserted = True
                        break
                if not inserted:
                    self.asks.append(ask)

        for bid in bids:
            key = self.findKeyByPrice(bid["price"], self.bids)
            # case 0: update size
            if key != None and bid["size"] > 0:
                self.bids[key]["size"] = bid["size"]
            # case 1: remove node
            elif key != None and bid["size"] == 0:
                del self.bids[key]
            # case 2: add new node
            elif key == None:
                inserted = False
                for i in range(len(self.bids)):
                    if float(bid["price"]) > float(self.bids[i]["price"]):
                        self.bids.insert(i, bid)
                        inserted = True
                        break
                if not inserted:
                    self.bids.append(bid)

    def findKeyByPrice(self, price, plist):
        for i in range(len(plist)):
            item = plist[i]
            if item["price"] == price:
                return i
        return None

    def calculateSpread(self):
        ask = float(self.asks[0]["price"])
        bid = float(self.bids[0]["price"])
        spread = ask - bid
        return ask, bid, spread

    def printSummary(self):
        ask, bid, spread = self.calculateSpread()
        print "   ASK: " + str(ask)
        print "   BID: " + str(bid)
        print "SPREAD: " + str(spread)

    def printTopOfBook(self):
        print "ASK: " + self.asks[0]["price"] + " (" + str(self.asks[0]["size"]) + "), " + self.asks[1]["price"] + " (" + str(self.asks[1]["size"]) + "), " + str(self.asks[2]["price"]) + " (" + str(self.asks[2]["size"]) + ")"
        print "BID: " + self.bids[0]["price"] + " (" + str(self.bids[0]["size"]) + "), " + self.bids[1]["price"] + " (" + str(self.bids[1]["size"]) + "), " + str(self.bids[2]["price"]) + " (" + str(self.bids[2]["size"]) + ")"

    def __str__(self):
        return "ASKS\n" + str(self.asks) + "\nBIDS\n" + str(self.bids)

if __name__ == '__main__':

    print "Running Orderbook tests..."

    asks = [
        {
            "price": 101.42,
            "size": 7
        },
        {
            "price": 101.85,
            "size": 5
        },
        {
            "price": 102.59,
            "size": 1
        },
        {
            "price": 114.53,
            "size": 3
        },
        {
            "price": 114.54,
            "size": 6
        },
        {
            "price": 114.55,
            "size": 19
        }
    ]
    bids = [
        {
            "price": 89.72,
            "size": 79
        },
        {
            "price": 89.71,
            "size": 158
        },
        {
            "price": 89.7,
            "size": 166
        },
        {
            "price": 89.69,
            "size": 231
        },
        {
            "price": 89.68,
            "size": 169
        },
        {
            "price": 89.67,
            "size": 186
        },
        {
            "price": 89.66,
            "size": 178
        }
    ]
    book = Orderbook(asks, bids)
    assert book.asks == [{'price': 101.42, 'size': 7}, {'price': 101.85, 'size': 5}, {'price': 102.59, 'size': 1}, {'price': 114.53, 'size': 3}, {'price': 114.54, 'size': 6}, {'price': 114.55, 'size': 19}]
    assert book.bids == [{'price': 89.72, 'size': 79}, {'price': 89.71, 'size': 158}, {'price': 89.7, 'size': 166}, {'price': 89.69, 'size': 231}, {'price': 89.68, 'size': 169}, {'price': 89.67, 'size': 186}, {'price': 89.66, 'size': 178}]
    book.updateOrderbookIncremental([], [
        {
            "price": 89.98,
            "size": 3
        }
    ])
    assert book.asks == [{'price': 101.42, 'size': 7}, {'price': 101.85, 'size': 5}, {'price': 102.59, 'size': 1}, {'price': 114.53, 'size': 3}, {'price': 114.54, 'size': 6}, {'price': 114.55, 'size': 19}]
    assert book.bids == [{'price': 89.98, 'size': 3}, {'price': 89.72, 'size': 79}, {'price': 89.71, 'size': 158}, {'price': 89.7, 'size': 166}, {'price': 89.69, 'size': 231}, {'price': 89.68, 'size': 169}, {'price': 89.67, 'size': 186}, {'price': 89.66, 'size': 178}]
    book.updateOrderbookIncremental([
        {
            "price": 101.98,
            "size": 3
        }
    ], [])
    assert book.asks == [{'price': 101.42, 'size': 7}, {'price': 101.85, 'size': 5}, {'price': 101.98, 'size': 3}, {'price': 102.59, 'size': 1}, {'price': 114.53, 'size': 3}, {'price': 114.54, 'size': 6}, {'price': 114.55, 'size': 19}]
    assert book.bids == [{'price': 89.98, 'size': 3}, {'price': 89.72, 'size': 79}, {'price': 89.71, 'size': 158}, {'price': 89.7, 'size': 166}, {'price': 89.69, 'size': 231}, {'price': 89.68, 'size': 169}, {'price': 89.67, 'size': 186}, {'price': 89.66, 'size': 178}]
    book.updateOrderbookIncremental([
        {
            "price": 101.42,
            "size": 9
        },
        {
            "price": 114.53,
            "size": 0
        },
    ], [
        {
            "price": 89.71,
            "size": 140
        },
        {
            "price": 89.69,
            "size": 0
        }
    ])
    assert book.asks == [{'price': 101.42, 'size': 9}, {'price': 101.85, 'size': 5}, {'price': 101.98, 'size': 3}, {'price': 102.59, 'size': 1}, {'price': 114.54, 'size': 6}, {'price': 114.55, 'size': 19}]
    assert book.bids == [{'price': 89.98, 'size': 3}, {'price': 89.72, 'size': 79}, {'price': 89.71, 'size': 140}, {'price': 89.7, 'size': 166}, {'price': 89.68, 'size': 169}, {'price': 89.67, 'size': 186}, {'price': 89.66, 'size': 178}]
    print "All test completed"


