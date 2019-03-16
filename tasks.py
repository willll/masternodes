from coin import Coin,Polis
from vps import VPS
import logging
from config import config, memcached

from twisted.internet import task
from twisted.internet import reactor

tasks = []

actions = {'mnstat': 'masternode status',
               'gi': 'getinfo',
               'mnss': 'mnsync status',
               'mnsr': 'mnsync reset'}

def configure_reactor():
    for command in actions :
        for i in range(0, len(config["masternodes"])):
            l = task.LoopingCall(action, i, command)
            l.start(60.0, False)  # call every 30 seconds
            tasks.append(l)

    # l.stop() will stop the looping calls
    #reactor.run()

def action(mnidx, actidx = 0):
    coin = Polis(config["Polis"])
    vps = VPS(config["masternodes"][mnidx], coin)
    res = vps.async_cli(actions[actidx], coin)
    memcached.client.set('{}{}'.format(actidx, mnidx), res)
