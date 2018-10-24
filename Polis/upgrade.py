import logging
import time
import sys
import json
from fabric import Connection
from invoke.exceptions import UnexpectedExit


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
def transfert_new_version(connection, dir, sourceFolder, versionToUpload):
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
def start_daemon(connection, dir, wallet_dir=""):
    # Restart the daemon
    try:
        conx_str = '{}/polisd -daemon -reindex'.format(dir)
        if wallet_dir != "" :
            conx_str += " --datadir=" + wallet_dir
        result = connection.run(conx_str, hide=True)
        msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
        logging.info(msg.format(result))
    except Exception as e :
        logging.error('Could not start  : {}'.format('polisd'), exc_info=e)

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
    init()

    if len(sys.argv) > 2:
        file = open(sys.argv[1], "r")
    else:
        file = open("config_test.json", "r")
    config = json.load(file)

    for cnx in config["masternodes"]:
        # noinspection PyBroadException
        try :
            kwargs = {"connect_timeout=": 30}
            if "connection_certificate" in cnx :
                kwargs["key_filename="] = cnx["connection_certificate"]
            connection = Connection(cnx["connection_string"], kwargs)
            target_directory = cnx["destination_folder"]

            # Create directory if does not exist
            create_polis_directory(connection, target_directory)

            # Stop the daemon if running
            stop_daemon(connection, target_directory)

            # Transfert File to remote directory
            transfert_new_version(connection, target_directory, config["SourceFolder"], config["VersionToUpload"])

            # Start the new daemon
            if "wallet_directories" in cnx :
                for wallet in cnx["wallet_directories"]:
                    start_daemon(connection, target_directory, wallet["wallet_directory"])
            else:
                start_daemon(connection, target_directory)

            logging.info('{} Has been  successfully upgraded'.format(cnx["connection_string"]))

        except Exception as e:
            logging.error('Could not upgrade {}'.format(cnx["connection_string"]), exc_info=e)


if __name__ == '__main__':
    main()
