#  https://github.com/crossbario/autobahn-python/blob/master/examples/twisted/websocket/echo/server.py

from autobahn.twisted.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory
import json
import zmq


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
        frontend = context.socket(zmq.XREQ)
        frontend.bind("tcp://*:5561")
        # Socket facing services
        backend = context.sockt(zmq.XREP)
        backend.bind("tcp://*:5562")

        zmq.proxy(frontend, backend)
        #zmq.device(zmq.QUEUE, frontend, backend)
    except Exception as e:

        print(e)
        print("bringing down zmq device")
    finally:
        pass
        frontend.close()
        backend.close()
        context.term()


def ws_handler():
    """
    This process should get message from zmq and send it to front end via ws

    :return:
    """

    from twisted.internet import reactor

    factory = WebSocketServerFactory(u"ws://127.0.0.1:9001")
    factory.protocol = MyServerProtocol
    # factory.setProtocolOptions(maxConnections=2)

    # note to self: if using putChild, the child must be bytes...

    reactor.listenTCP(9001, factory)
    reactor.run()



