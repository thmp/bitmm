import datetime, time
import os

class FileLogger(object):

    def __init__(self, filename):
        if not os.path.exists("./logs"):
            os.makedirs("./logs")

        self.day = datetime.date.today().day
        self.f = open(self.getFilename(filename), "a")
        self.filename = filename

    def getFilename(self, filename):
        return "./logs/" + filename + "-" + datetime.date.today().isoformat() + ".log"

    def refreshFile(self):
        self.f.close()
        self.day = datetime.date.today().day
        self.f = open(self.getFilename(self.filename), "a")

    def log(self, message):
        if datetime.date.today().day != self.day:
            self.refreshFile()
        self.f.write(message+"\n")
        self.buffer = []

    def __del__(self):
        self.f.flush()
        self.f.close()

if __name__ == '__main__':

    logger = FileLogger("test")
    c = 0
    while True:
        logger.log(str(c))
        c += 1
        time.sleep(1)