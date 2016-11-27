import MySQLdb
import json

class HitbtcDbStorage(object):

    def __init__(self):
        self.conn = MySQLdb.connect(host= "", user="", passwd="", db="")
        self.cur = self.conn.cursor()
        self.count = 0

    def processMessage(self, msg):
        msg = json.loads(msg)
        if "MarketDataSnapshotFullRefresh" in msg.keys():
            if msg["MarketDataSnapshotFullRefresh"]["symbol"] == "BTCEUR":
                print "Message " + str(self.count) + " stored"
                self.count += 1
                self.cur.execute("""INSERT INTO messages (message) VALUES (%s)""", [json.dumps(msg)])
        else:
            if msg["MarketDataIncrementalRefresh"]["symbol"] == "BTCEUR":
                print "Message " + str(self.count) + " stored"
                self.count += 1
                self.cur.execute("""INSERT INTO messages (message) VALUES (%s)""", [json.dumps(msg)])