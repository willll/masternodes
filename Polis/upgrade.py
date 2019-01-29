import logging
import time
import sys
import json
import string
import secrets
import re
from fabric import Connection
from invoke.exceptions import UnexpectedExit
import argparse

'''
    Globals
'''
default_wallet_dir = ""
default_wallet_conf_file = ""

'''

'''
def is_vps_installed(connection):
    is_installed = False
    try:
        # Search for libdb4.8-dev package,
        result = connection.run('dpkg-query -W --showformat=\'${Status}\n\' libdb4.8-dev|grep -c "install ok installed"', hide=True)
        msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
        logging.info(msg.format(result))
        if result.stdout == '1\n' :
            is_installed = True
    except UnexpectedExit:
        logging.info('{} does not exist !'.format(dir))
    return is_installed

'''
    BUG : Must be logged in root ! 
    TODO : add an interactive shell to ask user for credentials
'''
def install_vps(connection):
    try:
        cmds = [ "touch /var/swap.img",
                "chmod 600 /var/swap.img",
                "dd if=/dev/zero of=/var/swap.img bs=1024k count=2000",
                "mkswap /var/swap.img",
                "swapon /var/swap.img",
                "echo \"/var/swap.img none swap sw 0 0\" >> /etc/fstab",
                "apt-get update -y",
                "apt-get upgrade -y",
                "apt-get dist-upgrade -y",
                "apt-get install nano htop git -y",
                "apt-get install build-essential libtool autotools-dev automake pkg-config libssl-dev libevent-dev bsdmainutils software-properties-common -y",
                "apt-get install libboost-all-dev -y",
                "add-apt-repository ppa:bitcoin/bitcoin -y",
                "apt-get update -y",
                "apt-get install libdb4.8-dev libdb4.8++-dev -y" ]

        for cmd in cmds :
            result = connection.run('{}'.format(cmd), hide=True)
            msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
            logging.info(msg.format(result))
    except Exception as e:
        logging.error('Could not install vps', exc_info=e)

def get_ip_from_connection_string(str) :
    ip = re.compile('(([2][5][0-5]\.)|([2][0-4][0-9]\.)|([0-1]?[0-9]?[0-9]\.)){3}'
                +'(([2][5][0-5])|([2][0-4][0-9])|([0-1]?[0-9]?[0-9]))')
    match = ip.search(str)
    return match.group()

'''

'''
def is_directory_exists(connection, dir):
    isExists = False
    try:
        result = connection.run('[[ -d {} ]]'.format(dir), hide=True)
        msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
        logging.info(msg.format(result))
        isExists = True;
    except UnexpectedExit:
        logging.info('{} does not exist !'.format(dir))
    return isExists

'''

'''
def create_polis_directory(connection, dir):
    exists = is_directory_exists(connection, dir)
    if not exists :
        result = connection.run('mkdir -p {}'.format(dir), hide=True)
        msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
        logging.info(msg.format(result))
    return exists

'''

'''
def stop_daemon(connection, dir):
    # Clean up th mess
    try:
        cnt = 0
        result = connection.run('{}/polis-cli stop'.format(dir), hide=True)
        msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
        logging.info(msg.format(result))
        while cnt < 120: # Wait for the daemon to stop for 2 minutes
            result = connection.run('ps -A | grep polisd', hide=True)
            msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
            logging.debug(msg.format(result))
            time.sleep(1) # Wait one second before retry
            cnt = cnt + 1
    except UnexpectedExit:
        logging.info('{} does not run !'.format('polisd'))

'''

'''
def transfer_new_version(connection, dir, sourceFolder, versionToUpload):
    try:
        # Transfer the inflated to file to the target
        result = connection.put('{}{}'.format(sourceFolder, versionToUpload), dir)
        msg = "Transfered {0} to {1}"
        logging.debug(msg.format(versionToUpload, connection))
        # deflate the file
        result = connection.run('unzip -u -o {}/{} -d {}'.format(dir, versionToUpload, dir), hide=True)
        msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
        logging.info(msg.format(result))
        # Delete the archive
        result = connection.run('rm {}/{}'.format(dir, versionToUpload), hide=True)
        msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
        logging.info(msg.format(result))
        # fix permissions
        result = connection.run('chmod 755 {}/*'.format(dir), hide=True)
        msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
        logging.info(msg.format(result))
    except Exception as e :
        logging.error('Could not deploy : {}'.format(versionToUpload), exc_info=e)

'''

'''
def create_wallet_dir(connection, wallet_dir, PUBLICIP, PRIVATEKEY):
    exists = is_directory_exists(connection, dir)
    if not exists:
        result = connection.run('mkdir -p {}'.format(dir), hide=True)
        msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
        logging.info(msg.format(result))
        # Transfer the inflated to file to the target
        result = connection.put('./polis.conf', dir)
        msg = "Transfered {0} to {1}"
        logging.debug(msg.format('./polis.conf', connection))
        # Setup the config file
        polis_conf = dir + 'polis.conf'
        RPCUSER = ''.join(secrets.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(50))
        result = connection.run('sed - i \'s/<RPCUSER>/{}/g\' {}'.format(RPCUSER, polis_conf), hide=True)
        msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
        logging.info(msg.format(result))
        RPCPASSWORD = ''.join(secrets.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(50))
        result = connection.run('sed - i \'s/<RPCPASSWORD>/{}/g\' {}'.format(RPCPASSWORD, polis_conf), hide=True)
        msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
        logging.info(msg.format(result))
        result = connection.run('sed - i \'s/<PUBLICIP>/{}/g\' {}'.format(PUBLICIP, polis_conf), hide=True)
        msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
        logging.info(msg.format(result))
        result = connection.run('sed - i \'s/<PRIVATEKEY>/{}/g\' {}'.format(PRIVATEKEY, polis_conf), hide=True)
        msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
        logging.info(msg.format(result))
    return exists


'''

'''
def clean_up_wallet_dir(connection, wallet_dir):
    resources_to_delete = ["chainstate", "blocks", "peers.dat"]
    to_delete_str = " ".join(wallet_dir + str(x) for x in resources_to_delete)
    try:
        if wallet_dir == "" :
            raise Exception('Missing wallet directory')
        conx_str = 'rm -rf {}'.format(to_delete_str)
        result = connection.run(conx_str, hide=True)
        msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
        logging.info(msg.format(result))
    except UnexpectedExit as e :
        logging.error('Could not delete : {}'.format(to_delete_str), exc_info=e)


'''

'''
def clean_up_config(connection, wallet_config_file, option):
    try:
        if wallet_config_file == "" :
            raise Exception('Missing wallet configuration file')
        conx_str = ""
        if option == "clear addnode" :
            conx_str = "sed -i '/^addnode/d' {}".format(wallet_config_file)
        elif option == "clear connection" :
            conx_str = "sed -i '/^connection/d' {}".format(wallet_config_file)
        else :
            raise Exception('Invalid option')
        result = connection.run(conx_str, hide=True)
        msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
        logging.info(msg.format(result))
    except UnexpectedExit as e :
        logging.error('Could not clean up : {}'.format(wallet_config_file), exc_info=e)

'''

'''
def add_addnode(connection, wallet_config_file):
    try:
        if wallet_config_file == "" :
            raise Exception('Missing wallet configuration file')

        cmd = "echo \"addnode=insight.polispay.org:24126\naddnode=explorer.polispay.org:24126\" >> {}".format(wallet_config_file)

        result = connection.run(cmd, hide=True)
        msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
        logging.info(msg.format(result))
    except UnexpectedExit as e :
        logging.error('Could not add addnode : {}'.format(wallet_config_file), exc_info=e)


'''

'''
def start_daemon(connection, dir, wallet_dir="", use_wallet_dir=False, use_reindex=False):
    # Restart the daemon
    try:
        conx_str = '{}/polisd -daemon'.format(dir)
        if use_reindex:
            conx_str += ' -reindex'
        if wallet_dir != "" and use_wallet_dir :
            conx_str += " --datadir=" + wallet_dir
        result = connection.run(conx_str, hide=True)
        msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
        logging.info(msg.format(result))
    except Exception as e :
        logging.error('Could not start  : {}'.format('polisd'), exc_info=e)

'''

'''
def reindex_masternode(connection, target_directory, cnx):
    global default_wallet_dir
    global default_wallet_conf_file
    # Stop the daemon if running
    stop_daemon(connection, target_directory)

    wallet_dirs = []

    use_wallet_dir = False

    if "wallet_directories" in cnx:
        for wallet in cnx["wallet_directories"]:
            wallet_dirs.append(wallet["wallet_directory"])
        use_wallet_dir = True

    else:
        wallet_dirs = [ default_wallet_dir ]

    for wallet_dir in wallet_dirs:
        wallet_conf_file = wallet_dir + default_wallet_conf_file
        # Clean up old wallet dir
        clean_up_wallet_dir(connection, wallet_dir)
        # Start the new daemon
        start_daemon(connection, target_directory, wallet_dir, use_wallet_dir, True)

'''

'''
def init():
    # create logger
    logger = logging.getLogger('logger')
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler('debug.log')
    fh.setLevel(logging.DEBUG)
    ch = logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    logger.addHandler(fh)
    logger.addHandler(ch)

'''

'''
def main():
    global default_wallet_dir
    global default_wallet_conf_file
    init()

    # CLI arguments
    parser = argparse.ArgumentParser(description='Masternodes upgrade script')
    parser.add_argument('--config', nargs='?', default="config.json", help='config file in Json format')
    parser.add_argument('-cleanConfig', action='store_true', help='clean up to config files')
    parser.add_argument('-addNodes', action='store_true', help='edit the config file to add addnode entries')
    parser.add_argument('-onlyReindex', action='store_true', help='only reindex the masternodes')
    parser.add_argument('-onlyInstallVPS', action='store_true', help='only install the VPSs')
    args = parser.parse_args()

    # Load configuration file
    file = open(args.config)
    config = json.load(file)

    # Global settings
    default_wallet_dir = config["Polis"]["default_wallet_dir"]
    default_wallet_conf_file = config["Polis"]["default_wallet_conf_file"]

    for cnx in config["masternodes"]:
        # noinspection PyBroadException
        try :
            kwargs = {}
            if "connection_certificate" in cnx :
                kwargs['key_filename'] = cnx["connection_certificate"]
            else :
                # Must be mutually excluded
                if "connection_password" in cnx:
                    kwargs['password'] = cnx["connection_password"]

            connection = Connection(cnx["connection_string"], connect_timeout=30, connect_kwargs=kwargs)

            target_directory = cnx["destination_folder"]

            if args.onlyReindex :
                reindex_masternode(connection, target_directory, cnx)
                logging.info('{} Has been successfully reindexed'.format(cnx["connection_string"]))

            elif args.onlyInstallVPS :
                if not is_vps_installed(connection) :
                    install_vps(connection)
                    logging.info('{} Has been successfully installed'.format(cnx["connection_string"]))
                else:
                    logging.info('{} Already installed'.format(cnx["connection_string"]))

            else:
                # Install VPS
                if not is_vps_installed(connection) :
                    install_vps(connection)

                # Create directory if does not exist
                create_polis_directory(connection, target_directory)

                # Stop the daemon if running
                stop_daemon(connection, target_directory)

                # Transfer File to remote directory
                transfer_new_version(connection, target_directory, config["SourceFolder"], config["VersionToUpload"])

                wallet_dirs = []
                use_wallet_dir = False

                if "wallet_directories" in cnx :
                    for wallet in cnx["wallet_directories"]:
                        wallet_dirs.append( wallet["wallet_directory"] )
                    use_wallet_dir = True
                else:
                    wallet_dirs = [ default_wallet_dir ]

                for wallet_dir in wallet_dirs:
                    wallet_conf_file = wallet_dir+default_wallet_conf_file

                    if not is_directory_exists(connection, wallet_dir) :
                        create_wallet_dir(connection, wallet_dir, get_ip_from_connection_string(cnx["connection_string"]), cnx["private_key"])

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

                logging.info('{} Has been successfully upgraded'.format(cnx["connection_string"]))

        except Exception as e:
            logging.error('Could not upgrade {}'.format(cnx["connection_string"]), exc_info=e)


if __name__ == '__main__':
    main()
