from model.orderbook import Orderbook, CoinbaseOrderbook
from model.market import MarketModel

#from gateway.database import DatabaseGateway
from gateway.coinbase import CoinbaseGateway
from adapter.coinbase import CoinbaseAdapter

orderbook = CoinbaseOrderbook()
#orderbook_usd = CoinbaseOrderbook()

model = MarketModel(orderbook)

gateway = CoinbaseGateway()

#adapter = CoinbaseAdapter(orderbook, model, gateway, storage=False, orderbook_usd=orderbook_usd)
adapter = CoinbaseAdapter(orderbook, model, gateway, storage=False)

gateway.setMessageCallback(adapter.processMessage)

adapter.initializeOrderbook()

gateway.run()