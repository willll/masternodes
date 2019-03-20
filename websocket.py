#  https://github.com/crossbario/autobahn-python/blob/master/examples/twisted/websocket/echo/server.py

from autobahn.twisted.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory
import json
import zmq


class MyServerProtocol(WebSocketServerProtocol):

    def onConnect(self, request):
        print("Client connecting: {0}".format(request.peer))

    def onOpen(self):
        print("WebSocket connection open.")

    def onMessage(self, payload, isBinary):
        '''
        Read ZMQ push/pull for  messages and send
        to frontend
        :return:
        '''
        print("Received message on websocket, looking for ZMQ")
        port = "5570"
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect(f"tcp://127.0.0.1:{port}")

        #  Wait for next request from client
        message = socket.recv_json()

        params = json.loads(message)

        self.sendMessage("ZMQ content:".encode('utf8'))
        self.sendMessage(params.encode('utf8'))


    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))





