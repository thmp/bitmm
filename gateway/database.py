import MySQLdb

class DatabaseGateway(object):

    def __init__(self):
        self.conn = MySQLdb.connect(host="", user="", passwd="", db="")
        self.cur = self.conn.cursor()

    def setMessageCallback(self, callback):
        self.callback = callback

    def run(self):
        c = 0
        self.cur.execute("""SELECT * FROM messages ORDER BY id ASC""")
        for (idx, timestamp, message) in self.cur:
            self.callback(message)
            c += 1
        print "Simulated " + str(c) + " messages"

if __name__ == '__main__':
    gateway = DatabaseGateway()

    def printout(msg):
        print msg

    gateway.setMessageCallback(printout)
    gateway.run()