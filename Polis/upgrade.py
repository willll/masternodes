import logging
import time
import sys
import json
import string
import secrets
import os
from fabric import Connection
from invoke.exceptions import UnexpectedExit
import argparse
import utils

'''
    Globals
'''
default_wallet_dir = ""
default_wallet_conf_file = ""

def executeCmd(connection, cmd, hide=True) :
    result = connection.run(cmd, hide=hide)
    msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
    logging.info(msg.format(result))

'''

'''
def is_sentinel_installed(connection):
    is_installed = False
    try:
        # Search for Polis/sentinel in crontable
        result = connection.run('crontab -l | grep -c "Polis/sentinel"', hide=True)
        msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
        logging.info(msg.format(result))
        if result.stdout == '1\n' :
            is_installed = True
    except UnexpectedExit:
        logging.info('{} does not exist !'.format(dir))
    return is_installed

'''

'''
def install_sentinel(connection, wallet_dir):
    try:
        logging.info("Installing sentinel !")
        executeCmd(connection, "apt-get install -y virtualenv")
        executeCmd(connection, "cd {}".format(wallet_dir))
        executeCmd(connection, "git clone https://github.com/polispay/sentinel.git")
        executeCmd(connection, "virtualenv venv")
        executeCmd(connection, "venv/bin/pip install -r requirements.txt",)
        executeCmd(connection, "echo polis_conf={}polis.conf >> sentinel.conf".format(wallet_dir))
        executeCmd(connection, "crontab -l > tempcron")
        executeCmd(connection, "echo \"* * * * * cd {}/sentinel && ./venv/bin/python bin/sentinel.py 2>&1 >> sentinel-cron.log\" >> tempcron".format(wallet_dir))
        executeCmd(connection, "crontab tempcron")
        executeCmd(connection, "rm tempcron")
    except Exception as e:
        logging.error('Could not install vps', exc_info=e)

'''

'''
def is_vps_installed(connection):
    is_installed = False
    try:
        # Search for libdb4.8-dev package,
        result = connection.run('dpkg-query -W --showformat=\'${Status}\n\' libdb4.8-dev | grep -c "install ok installed"', hide=True)
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
def install_vps(connection, swap_supported = False):
    try:
        cmds_create_swap = [    "touch /var/swap.img",
                                "chmod 600 /var/swap.img",
                                "dd if=/dev/zero of=/var/swap.img bs=1024k count=2000",
                                "mkswap /var/swap.img",
                                "swapon /var/swap.img",
                                "echo \"/var/swap.img none swap sw 0 0\" >> /etc/fstab" ]

        cmds_apt_get = [        "apt-get update -y",
                                "apt-get upgrade -y",
                                "apt-get dist-upgrade -y",
                                "apt-get install nano htop git -y",
                                "apt-get install build-essential libtool autotools-dev automake pkg-config libssl-dev libevent-dev bsdmainutils software-properties-common -y",
                                "apt-get install libboost-all-dev -y",
                                "add-apt-repository ppa:bitcoin/bitcoin -y",
                                "apt-get update -y",
                                "apt-get install libdb4.8-dev libdb4.8++-dev -y" ]

        if swap_supported :
            logging.info("Create SWAP file !")
            for cmd in cmds_create_swap :
                executeCmd(connection, '{}'.format(cmd))

        logging.info("Download dependencies !")
        for cmd in cmds_apt_get:
            executeCmd(connection, '{}'.format(cmd))
    except Exception as e:
        logging.error('Could not install vps', exc_info=e)

'''

'''
def is_directory_exists(connection, dir):
    isExists = False
    try:
        executeCmd(connection, '[[ -d {} ]]'.format(dir))
        isExists = True;
    except UnexpectedExit:
        logging.info('{} does not exist !'.format(dir))
    return isExists

'''

'''
def create_polis_directory(connection, dir):
    exists = is_directory_exists(connection, dir)
    if not exists :
        executeCmd(connection, 'mkdir -p {}'.format(dir))
    return exists

'''

'''
def stop_daemon(connection, dir):
    # Clean up th mess
    try:
        cnt = 0
        executeCmd(connection, '{}/polis-cli stop'.format(dir))
        while cnt < 120: # Wait for the daemon to stop for 2 minutes
            executeCmd(connection, 'ps -A | grep polisd')
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
        executeCmd(connection, 'unzip -u -o {}/{} -d {}'.format(dir, versionToUpload, dir))
        # Delete the archive
        executeCmd(connection, 'rm {}/{}'.format(dir, versionToUpload))
        # fix permissions
        executeCmd(connection, 'chmod 755 {}/*'.format(dir))

    except Exception as e :
        logging.error('Could not deploy : {}'.format(versionToUpload), exc_info=e)

'''

'''
def create_wallet_dir(connection, wallet_dir, PUBLICIP, PRIVATEKEY, delete_before=False):
    if delete_before :
        executeCmd(connection, 'rm -rf {}'.format(wallet_dir))
    exists = is_directory_exists(connection, wallet_dir)
    if not exists:
        executeCmd(connection, 'mkdir -p {}'.format(wallet_dir))
        # Transfer the inflated to file to the target
        dir_path = os.path.dirname(os.path.realpath(__file__))
        polis_conf_tpl = dir_path + '/polis.conf'
        result = connection.put(polis_conf_tpl, wallet_dir)
        msg = "Transfered {0} to {1}"
        logging.debug(msg.format(polis_conf_tpl, wallet_dir))
        # Setup the config file
        polis_conf = wallet_dir + 'polis.conf'
        # source : https://stackoverflow.com/questions/2257441/random-string-generation-with-upper-case-letters-and-digits-in-python/23728630#23728630
        RPCUSER = ''.join(secrets.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(50))
        executeCmd(connection, 'sed -i \'s/<RPCUSER>/{}/g\' {}'.format(RPCUSER, polis_conf))
        RPCPASSWORD = ''.join(secrets.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(50))
        executeCmd(connection, 'sed -i \'s/<RPCPASSWORD>/{}/g\' {}'.format(RPCPASSWORD, polis_conf))
        executeCmd(connection, 'sed -i \'s/<PUBLICIP>/{}/g\' {}'.format(PUBLICIP, polis_conf))
        executeCmd(connection, 'sed -i \'s/<PRIVATEKEY>/{}/g\' {}'.format(PRIVATEKEY, polis_conf))

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
        executeCmd(connection, conx_str)

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
            cmd = "sed -i '/^addnode/d' {}".format(wallet_config_file)
        elif option == "clear connection" :
            cmd = "sed -i '/^connection/d' {}".format(wallet_config_file)
        else :
            raise Exception('Invalid option')
        executeCmd(connection, cmd)

    except UnexpectedExit as e :
        logging.error('Could not clean up : {}'.format(wallet_config_file), exc_info=e)

'''

'''
def add_addnode(connection, wallet_config_file):
    try:
        if wallet_config_file == "" :
            raise Exception('Missing wallet configuration file')

        cmd = "echo \"addnode=insight.polispay.org:24126\naddnode=explorer.polispay.org:24126\" >> {}".format(wallet_config_file)
        executeCmd(connection, cmd)

    except UnexpectedExit as e :
        logging.error('Could not add addnode : {}'.format(wallet_config_file), exc_info=e)


'''

'''
def start_daemon(connection, dir, wallet_dir="", use_wallet_dir=False, use_reindex=False):
    # Restart the daemon
    cmd = '{}/polisd -daemon'.format(dir)
    try:
        if use_reindex:
            cmd += ' -reindex'
        if wallet_dir != "" and use_wallet_dir :
            cmd += " --datadir=" + wallet_dir
        executeCmd(connection, cmd)

    except Exception as e :
        logging.error('Could not start  : {}'.format(cmd), exc_info=e)

'''

'''
def install_boostrap(connection, target_directory, cnx):
    global default_wallet_dir
    global default_wallet_conf_file
    # Stop the daemon if running
    stop_daemon(connection, target_directory)

    wallet_dirs, use_wallet_dir = get_wallet_dir(cnx)

    for wallet_dir in wallet_dirs:
        wallet_conf_file = wallet_dir + default_wallet_conf_file
        # Clean up old wallet dir
        clean_up_wallet_dir(connection, wallet_dir)
        executeCmd(connection, "cd {}".format(wallet_dir))

        # Download bootstrap and unzip it
        executeCmd(connection, "wget http://wbs.cryptosharkspool.com/polis/bootstrap.zip",)
        executeCmd(connection, "unzip -o bootstrap.zip")
        executeCmd(connection, "rm -f bootstrap.zip")
        # Start the new daemon
        start_daemon(connection, target_directory, wallet_dir, use_wallet_dir, False)

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
def reindex_masternode(connection, target_directory, cnx):
    global default_wallet_dir
    global default_wallet_conf_file
    # Stop the daemon if running
    stop_daemon(connection, target_directory)

    wallet_dirs, use_wallet_dir = get_wallet_dir(cnx)

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
    parser.add_argument('-deploy', action='store_true', help='deploy a new version')
    parser.add_argument('-cleanConfig', action='store_true', help='clean up to config files')
    parser.add_argument('-addNodes', action='store_true', help='edit the config file to add addnode entries')
    parser.add_argument('-reindex', action='store_true', help='reindex the masternodes')
    parser.add_argument('-installVPS', action='store_true', help='install the VPSs')
    parser.add_argument('-installBootstrap', action='store_true', help='install the bootstrap')
    parser.add_argument('-deployConfig', action='store_true', help='deploy polis.conf')
    parser.add_argument('-startDaemon', action='store_true', help='start the daemon')
    parser.add_argument('-masternodeConf', action='store_true', help='output the masternode.conf content')
    args = parser.parse_args()

    # Load configuration file
    file = open(args.config)
    config = json.load(file)

    # Global settings
    default_wallet_dir = config["Polis"]["default_wallet_dir"]
    default_wallet_conf_file = config["Polis"]["default_wallet_conf_file"]

    masternode_conf = ""

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

            wallet_dirs, use_wallet_dir = get_wallet_dir(cnx)

            if args.masternodeConf and "private_key" in cnx :
                masternode_conf += "{} {}:24126 {} {}\n".format(cnx["connection_string"],
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
                if not is_vps_installed(connection) :
                    install_vps(connection)
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
                if not is_vps_installed(connection) :
                    install_vps(connection)

                # Create directory if does not exist
                create_polis_directory(connection, target_directory)

                # Stop the daemon if running
                stop_daemon(connection, target_directory)

                # Transfer File to remote directory
                transfer_new_version(connection, target_directory, config["SourceFolder"], config["VersionToUpload"])

                for wallet_dir in wallet_dirs:
                    wallet_conf_file = wallet_dir+default_wallet_conf_file

                    if not is_directory_exists(connection, wallet_dir) :
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
                    if not is_sentinel_installed(connection):
                        install_sentinel(connection, wallet_dir)

                logging.info('{} Has been successfully upgraded'.format(cnx["connection_string"]))

        except Exception as e:
            logging.error('Could not upgrade {}'.format(cnx["connection_string"]), exc_info=e)

    if args.masternodeConf:
        print(masternode_conf)


if __name__ == '__main__':
    main()
