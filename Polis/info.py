import json
from utils import executeCmd
import logging

'''

'''
def get_masternode_status(connection, dir, wallet_dir="", use_wallet_dir=False):
    # Restart the daemon
    cmd = '{}/polis-cli'.format(dir)
    result = ""
    try:
        if wallet_dir != "" and use_wallet_dir :
            cmd += " --datadir=" + wallet_dir
        cmd += " masternode status"
        result = executeCmd(connection, cmd)
        result = json.loads(result.stdout)
        if "status" in result :
            result = result["status"]
        else :
            logging.error('Bad response format, "status" not found : {}'.format(result))

    except Exception as e:
        logging.error('Bad response format : {}\n {}'.format(e, result))

    return result