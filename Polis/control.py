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

    rpc = RPC(config["Polis"]["wallet"]["username"],
              config["Polis"]["wallet"]["password"],
              config["Polis"]["wallet"]["ip"],
              config["Polis"]["wallet"]["port"])

    if args.lstx:
        args.listunspent = True
        args.listlockunspent = True

    if args.listunspent:
        rest = rpc.listunspent()
        rpc_output += "\"listunspent:\" " + "\r\n"
        cpt = 0
        for itr in rest :
            if itr['spendable'] and itr['solvable']:
                rpc_output += str(cpt) + " : "
                rpc_output += str(itr['txid']) + " : " + str(itr['amount'])
                rpc_output += "\r\n"
            cpt += 1

    if args.listlockunspent:
        rest = rpc.listlockunspent()
        rpc_output += "\"listlockunspent:\" " + "\r\n"
        cpt = 0
        for itr in rest:
            rpc_output += str(cpt) + " : "
            rpc_output += str(itr['txid'])
            rpc_output += "\r\n"
            cpt += 1

    if args.listaccounts:
        rpc_output += "\"listaccounts:\" " + json.dumps(rpc.listaccounts(), indent=2)
        rpc_output += "\r\n"

    if args.getbalance:
        rpc_output += "\"getbalance:\" " + json.dumps(rpc.getbalance(), indent=2)
        rpc_output += "\r\n"

    if args.masternode:
        rpc_output += "\"masternode:\" " + json.dumps(rpc.getMasternode(*str(args.masternode[0])), indent=2)
        rpc_output += "\r\n"

    print(rpc_output)

