# system imports
import logging
import sys
import json

from rpc import RPC

'''
init
'''


def init(args):
    # create logger
    debug_level = logging.INFO

    #if args.masternodeStatus or args.masternodeConf or args.masternodeDiagnostic:
    #    debug_level = logging.ERROR

    logger = logging.getLogger('logger')
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler('debug.log')
    fh.setLevel(logging.DEBUG)
    ch = logging.basicConfig(stream=sys.stdout, level=debug_level)
    logger.addHandler(fh)
    logger.addHandler(ch)


'''
control
'''

def rpc_control(args):
    init(args)

    # Load configuration file
    file = open(args.config)
    config = json.load(file)
    file.close()

    rpc_output = ""

    rpc = RPC(config["Polis"]["wallet"]["username"],config["Polis"]["wallet"]["password"],config["Polis"]["wallet"]["ip"],config["Polis"]["wallet"]["port"])

    if args.listunspent:
        rpc_output += str(rpc.listunspent())
        rpc_output += "\r\n"

    if args.getbalance:
        rpc_output += str(rpc.getbalance())
        rpc_output += "\r\n"

    print(rpc_output)

