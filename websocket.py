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

        def handeZMQ():
            '''
            Read ZMQ push/pull for  messages and send
            to frontend
            :return:
            '''
            port = "5570"
            context = zmq.Context()
            socket = context.socket(zmq.PULL)
            socket.connect("tcp://localhost:%s" % port)
            while True:
                #  Wait for next request from client
                message = socket.recv_json()

                params = json.loads(message)

                self.sendMessage(params)



    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            print("Text message received: {0}".format(payload.decode('utf8')))

        # echo back message verbatim
        self.sendMessage(payload, isBinary)

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))





