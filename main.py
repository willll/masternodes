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


from rest import app
from config import config
import zmq
from multiprocessing import Process,Queue
import json
import time
import random

def setup_zmq():
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


from coin import Polis
from vps import VPS

def cli_action(mnidx, actidx):
    '''
    This should not be here,
    but while i figure out structure it should work.

    :return:
    '''
    actions = {'mnstat': 'masternode status',
               'gi': 'getinfo',
               'mnss': 'mnsync status',
               'mnsr': 'mnsync reset'}

    coin = Polis(config["Polis"])
    vps = VPS(config["masternodes"][mnidx], coin)

    result = vps.async_cli(actions[actidx], coin)

    print(f"Sending result to websocket:\n\t{result}\n")

    return result

def websocket_sender():
    '''
    should send result to front end

    :return:
    '''


def server():
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

        proc = Process(target=cli_action, args=(params['mnidx'], params['actidx'],))
        procs[params['id']] = proc
        #need to join somewhere here

        #instantiate thread here to handle work

        #do websocket response.

if __name__ == '__main__':
    #start queue
    Process(target=setup_zmq).start()
    #start some workers:
    Process(target=server).start()


    app.run(host=config["Listen"]["host"], port=config["Listen"]["port"])




