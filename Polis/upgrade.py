# system imports
import logging
import time
import sys
import json
import string
import secrets
import os

# third party imports
from fabric import Connection
from invoke.exceptions import UnexpectedExit

# project imports
import argparse
import utils
import info
import sentinel
import vps

'''
    Globals
'''
default_wallet_dir = ""
default_wallet_conf_file = ""


'''

'''
def get_wallet_dir(cnx) :
    wallet_dirs = []
    use_wallet_dir = False
    if "wallet_directories" in cnx:
        for wallet in cnx["wallet_directories"]:
            wallet_dirs.append(wallet["wallet_directory"])
        use_wallet_dir = True
    elif "wallet_directory" in cnx:
        wallet_dirs = [cnx["wallet_directory"]]
    else:
        wallet_dirs = [ default_wallet_dir ]
    return (wallet_dirs, use_wallet_dir)


'''

'''
def create_polis_directory(connection, dir):
    exists = utils.is_directory_exists(connection, dir)
    if not exists :
        utils.executeCmd(connection, 'mkdir -p {}'.format(dir))
    return exists

'''

'''
def stop_daemon(connection, dir):
    # Clean up th mess
    try:
        cnt = 0
        utils.executeCmd(connection, '{}/polis-cli stop'.format(dir))
        while cnt < 120: # Wait for the daemon to stop for 2 minutes
            utils.executeCmd(connection, 'ps -A | grep [p]olisd')
            time.sleep(1) # Wait one second before retry
            cnt = cnt + 1
        # Ok at this ppint polisd is still running, enough !
        utils.executeCmd(connection, 'killall -9 polisd')
    except UnexpectedExit:
        logging.info('{} does not run !'.format('polisd'))

'''

'''
def transfer_new_version(connection, dir, sourceFolder, versionToUpload):
    try:
        # Transfer the inflated to file to the target
        utils.sendFile(connection, '{}{}'.format(sourceFolder, versionToUpload), dir)
        # deflate the file
        utils.executeCmd(connection, 'unzip -u -o {}/{} -d {}'.format(dir, versionToUpload, dir))
        # Delete the archive
        utils.executeCmd(connection, 'rm {}/{}'.format(dir, versionToUpload))
        # fix permissions
        utils.executeCmd(connection, 'chmod 755 {}/*'.format(dir))

    except Exception as e :
        logging.error('Could not deploy : {}'.format(versionToUpload), exc_info=e)

'''

'''
def create_wallet_dir(connection, wallet_dir, PUBLICIP, PRIVATEKEY, delete_before=False):
    if delete_before :
        utils.executeCmd(connection, 'rm -rf {}'.format(wallet_dir))
    exists = utils.is_directory_exists(connection, wallet_dir)
    if not exists:
        utils.executeCmd(connection, 'mkdir -p {}'.format(wallet_dir))
        # Transfer the inflated to file to the target
        dir_path = os.path.dirname(os.path.realpath(__file__))
        polis_conf_tpl = dir_path + '/polis.conf'
        utils.sendFile(connection, polis_conf_tpl, wallet_dir)
        # Setup the config file
        polis_conf = wallet_dir + 'polis.conf'
        # source : https://stackoverflow.com/questions/2257441/random-string-generation-with-upper-case-letters-and-digits-in-python/23728630#23728630
        rpcuser = ''.join(secrets.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(50))
        utils.executeCmd(connection, 'sed -i \'s/<RPCUSER>/{}/g\' {}'.format(rpcuser, polis_conf))
        rpcpassword = ''.join(secrets.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(50))
        utils.executeCmd(connection, 'sed -i \'s/<RPCPASSWORD>/{}/g\' {}'.format(rpcpassword, polis_conf))
        utils.executeCmd(connection, 'sed -i \'s/<PUBLICIP>/{}/g\' {}'.format(PUBLICIP, polis_conf))
        utils.executeCmd(connection, 'sed -i \'s/<PRIVATEKEY>/{}/g\' {}'.format(PRIVATEKEY, polis_conf))

    return exists


'''

'''
def clean_up_wallet_dir(connection, wallet_dir):
    resources_to_delete = [ "chainstate", "blocks", "peers.dat", "backups", "banlist.dat", "database", "db.log", "debug.log" ]
    to_delete_str = " ".join(wallet_dir + str(x) for x in resources_to_delete)
    try:
        if wallet_dir == "" :
            raise Exception('Missing wallet directory')
        conx_str = 'rm -rf {}'.format(to_delete_str)
        utils.executeCmd(connection, conx_str)

    except UnexpectedExit as e :
        logging.error('Could not delete : {}'.format(to_delete_str), exc_info=e)


'''

'''
def clean_up_config(connection, wallet_config_file, option):
    try:
        if wallet_config_file == "" :
            raise Exception('Missing wallet configuration file')
        if option == "clear addnode" :
            cmd = "sed -i '/^addnode/d' {}".format(wallet_config_file)
        elif option == "clear connection" :
            cmd = "sed -i '/^connection/d' {}".format(wallet_config_file)
        else :
            raise Exception('Invalid option')
        utils.executeCmd(connection, cmd)

    except UnexpectedExit as e :
        logging.error('Could not clean up : {}'.format(wallet_config_file), exc_info=e)

'''

'''
def add_addnode(connection, wallet_config_file):
    try:
        if wallet_config_file == "" :
            raise Exception('Missing wallet configuration file')

        cmd = "echo \"addnode=insight.polispay.org:24126\naddnode=explorer.polispay.org:24126\" >> {}".format(wallet_config_file)
        utils.executeCmd(connection, cmd)

    except UnexpectedExit as e :
        logging.error('Could not add addnode : {}'.format(wallet_config_file), exc_info=e)


'''

'''
def start_daemon(connection, directory, wallet_dir="", use_wallet_dir=False, use_reindex=False):
    # Restart the daemon
    cmd = '{}/polisd -daemon'.format(directory)
    try:
        if use_reindex:
            cmd += ' -reindex'
        if wallet_dir != "" and use_wallet_dir :
            cmd += " --datadir=" + wallet_dir
        utils.executeCmd(connection, cmd)

    except Exception as e :
        logging.error('Could not start  : {}'.format(cmd), exc_info=e)

'''

'''
def install_boostrap(connection, target_directory, cnx):
    global default_wallet_conf_file
    # Stop the daemon if running
    stop_daemon(connection, target_directory)

    wallet_dirs, use_wallet_dir = get_wallet_dir(cnx)

    for wallet_dir in wallet_dirs:
        # Clean up old wallet dir
        clean_up_wallet_dir(connection, wallet_dir)
        utils.executeCmd(connection, "cd {}".format(wallet_dir))

        # Download bootstrap 1.4.8-1 and unzip it
        #utils.executeCmd(connection, "wget http://wbs.cryptosharkspool.com/polis/bootstrap.zip -O {}/bootstrap.zip".format(wallet_dir))
        #utils.executeCmd(connection, "unzip -o {}/bootstrap.zip -d {}".format(wallet_dir, wallet_dir))
        #utils.executeCmd(connection, "cp -rf {}/bootstrap/* {}".format(wallet_dir, wallet_dir))
        #utils.executeCmd(connection, "rm -rf {}/bootstrap*".format(wallet_dir))
        # Download bootstrap 1.4.9
        utils.executeCmd(connection,
                         "wget http://explorer.polispay.org/images/bootstrap.dat -O {}/bootstrap.dat".format(
                             wallet_dir))
        # Start the new daemon
        start_daemon(connection, target_directory, wallet_dir, use_wallet_dir, False)

'''

'''
def reindex_masternode(connection, target_directory, cnx):
    global default_wallet_dir
    global default_wallet_conf_file
    # Stop the daemon if running
    stop_daemon(connection, target_directory)

    wallet_dirs, use_wallet_dir = get_wallet_dir(cnx)

    for wallet_dir in wallet_dirs:
        # Clean up old wallet dir
        clean_up_wallet_dir(connection, wallet_dir)
        # Start the new daemon
        start_daemon(connection, target_directory, wallet_dir, use_wallet_dir, True)

'''

'''
def init(args):
    # create logger
    debug_level = logging.INFO

    if args.masternodeStatus or args.masternodeConf :
        debug_level = logging.ERROR

    logger = logging.getLogger('logger')
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler('debug.log')
    fh.setLevel(logging.DEBUG)
    ch = logging.basicConfig(stream=sys.stdout, level=debug_level)
    logger.addHandler(fh)
    logger.addHandler(ch)

'''

'''
def main():
    global default_wallet_dir
    global default_wallet_conf_file

    # CLI arguments
    parser = argparse.ArgumentParser(description='Masternodes upgrade script')
    parser.add_argument('--config', nargs='?', default="config.json", help='config file in Json format')
    parser.add_argument('-deploy', action='store_true', help='deploy a new version')
    parser.add_argument('-cleanConfig', action='store_true', help='clean up to config files')
    parser.add_argument('-addNodes', action='store_true', help='edit the config file to add addnode entries')
    parser.add_argument('-reindex', action='store_true', help='reindex the masternodes')
    parser.add_argument('-installVPS', action='store_true', help='install the VPSs')
    parser.add_argument('-installBootstrap', action='store_true', help='install the bootstrap')
    parser.add_argument('-deployConfig', action='store_true', help='deploy polis.conf')
    parser.add_argument('-startDaemon', action='store_true', help='start the daemon')
    parser.add_argument('-masternodeConf', action='store_true', help='output the masternode.conf content')
    parser.add_argument('-masternodeStatus', action='store_true', help='output the masternode status')
    parser.add_argument('-masternodeDiagnostic', action='store_true', help='output diagnostics')
    parser.add_argument('-l', '--masternodeList', nargs='+', type=int, help='output diagnostics')
    args = parser.parse_args()

    init(args)

    # Load configuration file
    file = open(args.config)
    config = json.load(file)

    # Global settings
    default_wallet_dir = config["Polis"]["default_wallet_dir"]
    default_wallet_conf_file = config["Polis"]["default_wallet_conf_file"]

    masternode_output = ""

    connection_string_max_length = utils.maxStringsLength(config["masternodes"])

    masternode_index = -1

    for cnx in config["masternodes"]:
        masternode_index += 1
        # noinspection PyBroadException
        try :

            if args.masternodeList and masternode_index not in args.masternodeList:
                continue

            kwargs = {}
            if "connection_certificate" in cnx :
                kwargs['key_filename'] = cnx["connection_certificate"]
            else :
                # Must be mutually excluded
                if "connection_password" in cnx:
                    kwargs['password'] = cnx["connection_password"]

            connection = Connection(cnx["connection_string"], connect_timeout=30, connect_kwargs=kwargs)

            target_directory = cnx["destination_folder"]

            wallet_dirs, use_wallet_dir = get_wallet_dir(cnx)

            if args.masternodeDiagnostic :
                f = "{0:<4}: {1:<%d}: {2}\n" % (connection_string_max_length + 1)
                for wallet_dir in wallet_dirs:
                    masternode_output += f.format(masternode_index,
                                                  cnx["connection_string"],
                                                  info.get_masternode_diagnostic(connection, target_directory, wallet_dir, use_wallet_dir))

            if args.masternodeStatus:
                f = "{0:<4}: {1:<%d}: {2}\n" % (connection_string_max_length + 1)
                for wallet_dir in wallet_dirs:
                    masternode_output += f.format(masternode_index,
                                                  cnx["connection_string"],
                                                  info.get_masternode_status(connection, target_directory, wallet_dir, use_wallet_dir))

            if args.masternodeConf and "private_key" in cnx :
                masternode_output += "{0:>15} {}:24126 {1} {2}\n".format(cnx["connection_string"],
                                                          utils.get_ip_from_connection_string(cnx["connection_string"]),
                                                          cnx["private_key"],
                                                          cnx["outputs"])

            if args.startDaemon :
                for wallet_dir in wallet_dirs:
                    start_daemon(connection, target_directory, wallet_dir, use_wallet_dir)
                    logging.info('{} Has been successfully reindexed'.format(cnx["connection_string"]))

            if args.reindex :
                reindex_masternode(connection, target_directory, cnx)
                logging.info('{} Has been successfully reindexed'.format(cnx["connection_string"]))

            if args.installVPS :
                if not vps.is_vps_installed(connection) :
                    vps.install_vps(connection)
                    logging.info('{} Has been successfully installed'.format(cnx["connection_string"]))
                else:
                    logging.info('{} Already installed'.format(cnx["connection_string"]))

            if args.installBootstrap :
                install_boostrap(connection, target_directory, cnx)
                logging.info('{} Has been successfully reindexed'.format(cnx["connection_string"]))

            if args.deployConfig :
                for wallet_dir in wallet_dirs:
                    wallet_conf_file = wallet_dir + default_wallet_conf_file
                    create_wallet_dir(connection, wallet_dir,
                                      utils.get_ip_from_connection_string(cnx["connection_string"]),
                                      cnx["private_key"], True)
                    if args.addNodes:
                        add_addnode(connection, wallet_conf_file)
                logging.info('{} Has been successfully configured'.format(cnx["connection_string"]))

            if args.deploy :
                # Install VPS
                if not vps.is_vps_installed(connection) :
                    vps.install_vps(connection)

                # Create directory if does not exist
                create_polis_directory(connection, target_directory)

                # Stop the daemon if running
                stop_daemon(connection, target_directory)

                # Transfer File to remote directory
                transfer_new_version(connection, target_directory, config["SourceFolder"], config["VersionToUpload"])

                for wallet_dir in wallet_dirs:
                    wallet_conf_file = wallet_dir+default_wallet_conf_file

                    if not utils.is_directory_exists(connection, wallet_dir) :
                        create_wallet_dir(connection, wallet_dir,
                                          utils.get_ip_from_connection_string(cnx["connection_string"]),
                                          cnx["private_key"])

                    # Clean up old wallet dir
                    clean_up_wallet_dir(connection, wallet_dir)

                    # Clean up the config file
                    if args.cleanConfig :
                        clean_up_config(connection, wallet_conf_file, "clear addnode")

                    # Add addnode in the config file
                    if args.addNodes :
                        add_addnode(connection, wallet_conf_file)

                    # Start the new daemon
                    start_daemon(connection, target_directory, wallet_dir, use_wallet_dir)

                    # install sentinel
                    if not sentinel.is_sentinel_installed(connection):
                        sentinel.install_sentinel(connection, wallet_dir)

                logging.info('{} Has been successfully upgraded'.format(cnx["connection_string"]))

        except Exception as e:
            logging.error('Could not upgrade {}'.format(cnx["connection_string"]), exc_info=e)

    if args.masternodeStatus or args.masternodeConf or args.masternodeDiagnostic :
        print(masternode_output)


if __name__ == '__main__':
    main()
