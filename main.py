'''
TODO: setup a websocket channel to talk to the front end
TODO: receive config for creation of new mn
TODO: action to delete old block chain cache, and cache .dat files
TODO: display config for one MN, and allow saving it too: with password, or certificat
TODO: test new MN creation
TODO: use ListBox on left side with list of IPs, should be searchable/filterable and can select multiple IPs
    with checkbox
TODO: Display information fromt he block explorer about block # and other relevant
TODO: Des checkbox pour sélectionner les mn en groupe
TODO: Une barre d'actions en haut pour appliquer aux mn sélectionné
TODO: un évent pour refesh la page aux 5 min
TODO: masternode start from this script (via RPC)
TODO: Enable multi threading or non blocking of requests/responses,
    - WSGI, gunicorn, multiprocessing (python),
    - https://stackoverflow.com/questions/40912982/how-can-my-twisted-klein-app-listen-on-multiple-ports

DONE:
'''

from config import config
import zmq
from multiprocessing import Process,Queue
import json

def setup_zmq():
    '''
    This process is the ZMQ REQ/REP broker

    :return:
    '''
    #create a queue to use by workers, which is fed by REST
    try:
        context = zmq.Context(1)
        # Socket facing clients
        frontend = context.socket(zmq.XREP)
        frontend.bind("tcp://*:5559")
        # Socket facing services
        backend = context.socket(zmq.XREQ)
        backend.bind("tcp://*:5560")

        zmq.device(zmq.QUEUE, frontend, backend)
    except Exception as e:
        print(e)
        print("bringing down zmq device")
    finally:
        pass
        frontend.close()
        backend.close()
        context.term()

def ws_handler():
    '''
    This process should get message from zmq and send it to front end via ws

    :return:
    '''


    from websocket import WebSocketServerFactory, MyServerProtocol
    from twisted.internet import reactor

    factory = WebSocketServerFactory(u"ws://127.0.0.1:9001")
    factory.protocol = MyServerProtocol
    # factory.setProtocolOptions(maxConnections=2)

    # note to self: if using putChild, the child must be bytes...

    reactor.listenTCP(9001, factory)
    reactor.run()


def cli_action(mnidx, actidx, reqid):
    '''
    This should not be here,
    but while i figure out structure it should work.

    This process takes care of actions that will block because of SSH

    :return:
    '''

    from coin import Polis
    from vps import VPS
    actions = {'mnstat': 'masternode status',
               'gi': 'getinfo',
               'mnss': 'mnsync status',
               'mnsr': 'mnsync reset'}

    coin = Polis(config["Polis"])
    vps = VPS(config["masternodes"][mnidx], coin)

    result = vps.async_cli(actions[actidx], coin)

    #use new push/pull queue for websocket results
    port = "5570"
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind(f"tcp://127.0.0.1:{port}")

    msg = {'id': reqid, 'mnidx': mnidx, 'actidx': actidx, 'result': result}
    socket.send_string(json.dumps(msg))

    #should clean up by exiting process here?
    return result


def server():
    '''
    This process should read the queue for blocking REST requests and start a
    process to deal with it and send results to websocket handler

    :return:
    '''
    port = "5560"
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.connect("tcp://localhost:%s" % port)
    procs = {}



    while True:
        #  Wait for next request from client
        message = socket.recv_json()
        print(f"Received request: {message}")

        params = json.loads(message)

        socket.send_json("{'result':'success'}")

        Process(target=cli_action, args=(params['mnidx'], params['actidx'], params['id'], )).start()
        #need to join somewhere here


if __name__ == '__main__':
    #start queue broker
    Process(target=setup_zmq).start()

    #start some SSH REST request workers:
    Process(target=server).start()

    #start websocket handler
    Process(target=ws_handler).start()

    from rest import app
    app.run(host=config["Listen"]["host"], port=config["Listen"]["port"])




