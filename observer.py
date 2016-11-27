from gateway.hitbtc import HitbtcGateway
from adapter.storage import HitbtcDbStorage

adapter = HitbtcDbStorage()

gateway = HitbtcGateway()
gateway.setMessageCallback(adapter.processMessage)

gateway.run()