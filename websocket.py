from autobahn.twisted.websocket import WebSocketServerProtocol

class MyServerProtocol(WebSocketServerProtocol):

    def onMes

    def onConnect(self, request):
        '''
        In this callback you can do things like

        csage(self, payload, isBinary):
        ## echo back message verbatim
        self.sendMessage(payload, isBinary)
hecking or setting cookies or other HTTP headers
        verifying the client IP address
        checking the origin of the WebSocket request
        negotiate WebSocket subprotocols
        :param request:
        :return:
        '''
        print(f"Client connecting: {request.peer}")

    def onOpen(self):
        print("WebSocket connection open.")

    def onClose(self, wasClean, code, reason):
        '''

        :param wasClean:
        :param code:
        :param reason:
        :return:
        '''
        print(f"WebSocket connection closed: {format(reason)}")

'''
async def consumer(message):
    print("consumer: ", message)


async def producer():
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    return (now)


async def consumer_handler(websocket):
    while True:
        async for message in websocket:
            print(f"this went in glob_message: {message}")
            await consumer(message)    #global glob_message


async def producer_handler(websocket):
    #global glob_message
    while True:
        message = await producer()
        print("producer: ", message)
        await websocket.send(message)
        await asyncio.sleep(5.0)


async def handler(websocket, path):
    producer_task = asyncio.ensure_future(producer_handler(websocket))
    consumer_task = asyncio.ensure_future(consumer_handler(websocket))
    done, pending = await asyncio.wait(
        [consumer_task, producer_task],
        return_when=asyncio.ALL_COMPLETED,
    )

    for task in pending:
        task.cancel()

'''

