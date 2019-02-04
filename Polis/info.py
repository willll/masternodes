import json
from utils import executeCmd
from sentinel import is_sentinel_installed
from vps import is_vps_installed, is_polis_installed, is_monitoring_script_installed
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
        logging.error('Bad response format : {}\r\n {}'.format(e, result))

    return result

def get_masternode_diagnostic(connection, config, dir, wallet_dir="", use_wallet_dir=False):
    result = ""
    try:
        f = '\r\n{0:<15} : {1}\r\n'
        # First check if the VPS is installed properly (WIP)
        if not is_vps_installed(connection) :
            result += f.format('vps', 'not installed')
        # Check if polisd is there
        if not is_polis_installed(connection, dir):
            result += f.format('polisd', 'not installed')

        #BUG : should be checked by wallet, not by VPS !
        if not is_sentinel_installed(connection) :
            result += f.format('sentinel', 'not installed')
        if not is_monitoring_script_installed(connection):
            result += f.format('monitoring script', 'not installed')
        # end of diagnostics
        if result == "" :
            result = "OK"

    except Exception as e:
        logging.error('Bad response format : {}\n {}'.format(e, result))

    return result
