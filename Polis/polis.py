# system imports
import logging
import time
import string
import secrets
import os

# third party imports
from invoke.exceptions import UnexpectedExit

# project imports
import utils


class Polis:
    def __init__(self, connection, target_directory):
        self.connection = connection
        self.target_directory = target_directory


'''
===== Daemon control =====
'''


'''
Start the daemon
'''


def start_daemon(self, directory, wallet_dir="", use_wallet_dir=False, use_reindex=False):
    # Restart the daemon
    cmd = '{}/polisd -daemon'.format(directory)
    try:
        if use_reindex:
            cmd += ' -reindex'
        if wallet_dir != "" and use_wallet_dir:
            cmd += " --datadir=" + wallet_dir
        utils.execute_command(self.connection, cmd)

    except Exception as e:
        logging.error('Could not start  : {}'.format(cmd), exc_info=e)


'''
Stop the daemon
'''


def stop_daemon(self, dir = None):
    # Clean up th mess
    try:
        if dir == None:
            dir = self.target_directory
        cnt = 0
        utils.execute_command(self.connection, '{}/polis-cli stop'.format(dir))
        while cnt < 120:  # Wait for the daemon to stop for 2 minutes
            utils.execute_command(self.connection, 'ps -A | grep [p]olisd')
            time.sleep(1)  # Wait one second before retry
            cnt = cnt + 1
        # Ok at this ppint polisd is still running, enough !
        utils.execute_command(self.connection, 'killall -9 polisd')
    except UnexpectedExit:
        logging.info('{} does not run !'.format('polisd'))



'''
===== Wallet FS operations =====
'''


'''
Creates polis executables directory
'''
def create_polis_directory(self, dir):
    exists = utils.is_directory_exists(self.connection, dir)
    if not exists :
        utils.execute_command(self.connection, 'mkdir -p {}'.format(dir))
    return exists


'''
Creates polis's wallet directory
'''
def create_wallet_dir(self, wallet_dir, public_ip, private_key, delete_before=False):
    if delete_before:
        utils.execute_command(self.connection, 'rm -rf {}'.format(wallet_dir))
    exists = utils.is_directory_exists(self.connection, wallet_dir)
    if not exists:
        utils.execute_command(self.connection, 'mkdir -p {}'.format(wallet_dir))
        # Transfer the inflated to file to the target
        dir_path = os.path.dirname(os.path.realpath(__file__))
        polis_conf_tpl = dir_path + '/polis.conf'
        utils.send_file(self.connection, polis_conf_tpl, wallet_dir)
        # Setup the config file
        polis_conf = wallet_dir + 'polis.conf'
        rpcuser = ''.join(
            secrets.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(50))
        utils.execute_command(self.connection, 'sed -i \'s/<RPCUSER>/{}/g\' {}'.format(rpcuser, polis_conf))
        rpcpassword = ''.join(
            secrets.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(50))
        utils.execute_command(self.connection, 'sed -i \'s/<RPCPASSWORD>/{}/g\' {}'.format(rpcpassword, polis_conf))
        utils.execute_command(self.connection, 'sed -i \'s/<PUBLICIP>/{}/g\' {}'.format(public_ip, polis_conf))
        utils.execute_command(self.connection, 'sed -i \'s/<PRIVATEKEY>/{}/g\' {}'.format(private_key, polis_conf))

    return exists


'''
Puts the files
'''


def transfer_new_version(self, dir, source_folder, version_to_upload):
    try:
        # Transfer the inflated to file to the target
        utils.send_file(self.connection, '{}{}'.format(source_folder, version_to_upload), dir)
        # deflate the file
        utils.execute_command(self.connection, 'unzip -u -o {}/{} -d {}'.format(dir, version_to_upload, dir))
        # Delete the archive
        utils.execute_command(self.connection, 'rm {}/{}'.format(dir, version_to_upload))
        # fix permissions
        utils.execute_command(self.connection, 'chmod 755 {}/*'.format(dir))

    except Exception as e:
        logging.error('Could not deploy : {}'.format(version_to_upload), exc_info=e)



'''
Cleans up the wallet directory 
'''
def clean_up_wallet_dir(self, wallet_dir):
    resources_to_delete = [ "chainstate", "blocks", "peers.dat", "backups", "banlist.dat", "database", "db.log", "debug.log" ]
    to_delete_str = " ".join(wallet_dir + str(x) for x in resources_to_delete)
    try:
        if wallet_dir == "" :
            raise Exception('Missing wallet directory')
        conx_str = 'rm -rf {}'.format(to_delete_str)
        utils.execute_command(self.connection, conx_str)

    except UnexpectedExit as e:
        logging.error('Could not delete : {}'.format(to_delete_str), exc_info=e)


'''
===== Wallet configuration =====
'''


'''
Cleans up the polis.conf from previous configurations
'''


def clean_up_config(self, wallet_config_file, option):
    try:
        if wallet_config_file == "":
            raise Exception('Missing wallet configuration file')
        if option == "clear addnode":
            cmd = "sed -i '/^addnode/d' {}".format(wallet_config_file)
        elif option == "clear connection":
            cmd = "sed -i '/^connection/d' {}".format(wallet_config_file)
        else :
            raise Exception('Invalid option')
        utils.execute_command(self.connection, cmd)

    except UnexpectedExit as e:
        logging.error('Could not clean up : {}'.format(wallet_config_file), exc_info=e)


'''
Adds node entries in polis.conf
'''
def add_addnode(self, wallet_config_file):
    try:
        if wallet_config_file == "":
            raise Exception('Missing wallet configuration file')

        cmd = "echo \"addnode=insight.polispay.org:24126\naddnode=explorer.polispay.org:24126\" >> {}".format(wallet_config_file)
        utils.execute_command(self.connection, cmd)

    except UnexpectedExit as e:
        logging.error('Could not add addnode : {}'.format(wallet_config_file), exc_info=e)


'''
===== bootstrap =====

Note : needs to be adapted based on discord directives, make sure to unpack the file manually to understand
its content/structure
'''


'''
bootstrap installation
'''


def install_boostrap(self, cnx):
    # Stop the daemon if running
    self.stop_daemon()

    wallet_dirs, use_wallet_dir = self.get_wallet_dir(cnx)

    for wallet_dir in wallet_dirs:
        # Clean up old wallet dir
        self.clean_up_wallet_dir(self.connection, wallet_dir)
        utils.execute_command(self.connection, "cd {}".format(wallet_dir))

        # Download bootstrap 1.4.8-1 and unzip it
        #utils.execute_command(connection, "wget http://wbs.cryptosharkspool.com/polis/bootstrap.zip -O {}/bootstrap.zip".format(wallet_dir))
        #utils.execute_command(connection, "unzip -o {}/bootstrap.zip -d {}".format(wallet_dir, wallet_dir))
        #utils.execute_command(connection, "cp -rf {}/bootstrap/* {}".format(wallet_dir, wallet_dir))
        #utils.execute_command(connection, "rm -rf {}/bootstrap*".format(wallet_dir))
        # Download bootstrap 1.4.9
        utils.execute_command(self.connection,
                         "wget http://explorer.polispay.org/images/bootstrap.dat -O {}/bootstrap.dat".format(
                             wallet_dir))
        # Start the new daemon
        self.start_daemon(self.connection, self.target_directory, wallet_dir, use_wallet_dir, False)


'''
===== Masternode controls =====
'''


'''
Reindexes the masternode
'''


def reindex_masternode(self, cnx):

    # Stop the daemon if running
    self.stop_daemon()

    wallet_dirs, use_wallet_dir = self.get_wallet_dir(cnx)

    for wallet_dir in wallet_dirs:
        # Clean up old wallet dir
        self.clean_up_wallet_dir(self.connection, wallet_dir)
        # Start the new daemon
        self.start_daemon(self.connection, self.target_directory, wallet_dir, use_wallet_dir, True)


