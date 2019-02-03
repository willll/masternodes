import json
from utils import executeCmd
from sentinel import is_sentinel_installed
from vps import is_vps_installed
import logging


def get_polisd_cmd(dir, wallet_dir="", use_wallet_dir=False):
    cmd = '{}/polis-cli'.format(dir)
    result = ""
    if wallet_dir != "" and use_wallet_dir:
        cmd += " --datadir=" + wallet_dir
    return cmd

'''

'''
def get_masternode_status(connection, dir, wallet_dir="", use_wallet_dir=False):
    result = ""
    try:
        cmd = get_polisd_cmd(dir, wallet_dir, use_wallet_dir)
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

def get_masternode_diagnostic(connection, dir, wallet_dir="", use_wallet_dir=False):
    result = ""
    try:
        f = '{0:<15} : {1}\n'
        if not vps.is_vps_installed(connection) :
            result += f.format('vps', 'not installed')
        #BUG : should be checked by wallet, not by VPS !
        if not sentinel.is_sentinel_installed(connection) :
            result += f.format('sentinel', 'not installed')




    except Exception as e:
        logging.error('Bad response format : {}\n {}'.format(e, result))

    return result
