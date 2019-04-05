#  https://github.com/crossbario/autobahn-python/blob/master/examples/twisted/websocket/echo/server.py

from autobahn.twisted.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory, listenWS
import json
import zmq
import sys

from twisted.internet import reactor
from twisted.python import log

'''
remove class once broadcast is fixed and finishes 
'''
class MyServerProtocol(WebSocketServerProtocol):

    def onConnect(self, request):
        context = zmq.Context.instance()
        self.socket = context.socket(zmq.REP)
        print("Client connecting: {0}".format(request.peer))

    def onOpen(self):
        print("WebSocket connection open.")

    def onMessage(self, payload, isBinary):
        """
        Query ZMQ broker for  messages and send
        to frontend
        :return:
        """

        port = "5562"
        self.socket.connect("tcp://*:5562")

        message = self.socket.recv_json()
        print(f"Reading from workers quque {message}")
        params = json.dumps(message)

        self.sendMessage(params.encode('utf8'))


    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))


def setup_ws_zmq():
    """
    This process is the ZMQ REQ/REP broker

    :return:
    """

    try:
        context = zmq.Context()
        # Socket facing clients
        feed_in = context.socket(zmq.XPUB)
        feed_in.bind("ipc://ws_update_in")

        # Socket facing services
        feed_out = context.socket(zmq.XSUB)
        feed_out.bind("ipc://ws_update_out")

        zmq.proxy(feed_in, feed_out)
        #zmq.device(zmq.QUEUE, frontend, backend)
    except Exception as e:

        print(e)
        print("bringing down zmq device")
    finally:
        pass
        frontend.close()
        backend.close()
        context.term()


class BroadcastServerProtocol(WebSocketServerProtocol):

    def onOpen(self):
        self.factory.register(self)

    def onMessage(self, payload, isBinary):
        if not isBinary:
            msg = "{} from {}".format(payload.decode('utf8'), self.peer)
            self.factory.broadcast(msg)

    def connectionLost(self, reason):
        WebSocketServerProtocol.connectionLost(self, reason)
        self.factory.unregister(self)


class BroadcastServerFactory(WebSocketServerFactory):

    """
    Simple broadcast server broadcasting any message it receives to all
    currently connected clients.
    """

    def __init__(self, url):
        WebSocketServerFactory.__init__(self, url)
        self.clients = []
        self.tickcount = 0

        context = zmq.Context.instance()
        self.socket = context.socket(zmq.SUB)
        self.socket.connect("ipc://ws_update_in")

        self.tick()



    def tick(self):
        self.tickcount += 1
        '''
        message = self.socket.recv_json()

        print(f"Reading from workers quque {message}")
        params = json.dumps(message)
        message = {"id":"MN STATUS", "mnid":"1",  "msg": params}
        '''
        message = {"id":"MN STATUS", "mnid":"1"}
        self.broadcast(json.dumps(message))
        #self.broadcast(f"Data: {params}")

        reactor.callLater(3, self.tick)

    def register(self, client):
        if client not in self.clients:
            print("registered client {}".format(client.peer))
            self.clients.append(client)

    def unregister(self, client):
        if client in self.clients:
            print("unregistered client {}".format(client.peer))
            self.clients.remove(client)

    def broadcast(self, msg):
        print("broadcasting message '{}' ..".format(msg))
        for c in self.clients:
            c.sendMessage(msg.encode('utf8'))
            print("message sent to {}".format(c.peer))





def ws_handler():
    """
    This process should get message from zmq and send it to front end via ws

    Getting complicated with twisted, this is how you broadcast:
    https://github.com/crossbario/autobahn-python/blob/master/examples/twisted/websocket/broadcast/server.py

    trying to follow example done with tornado:
    https://github.com/cesium-ml/message_flow/blob/master/websocket_server.py

    - have an IOLoop expecting events on the zmq socket
    - when there is an event, broadcast it.

    :return:
    `
    """

    log.startLogging(sys.stdout)

    ServerFactory = BroadcastServerFactory
    # ServerFactory = BroadcastPreparedServerFactory

    factory = ServerFactory(u"ws://127.0.0.1:9001")
    factory.protocol = BroadcastServerProtocol
    listenWS(factory)

    reactor.run()


#################old
#    factory = WebSocketServerFactory(u"ws://127.0.0.1:9001")
#    factory.protocol = MyServerProtocol
    # factory.setProtocolOptions(maxConnections=2)

    # note to self: if using putChild, the child must be bytes...

#    reactor.listenTCP(9001, factory)
#    reactor.run()



