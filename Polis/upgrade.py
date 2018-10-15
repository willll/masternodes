import logging
import time
import sys
from fabric import Connection
from invoke.exceptions import UnexpectedExit

ConnectionsList = [ ['bob@192.168.1.1',    '/home/bob/Polis'],
                    ['john@192.68.1.2',    '/home/john/Polis'],
                   ]

SourceFolder = '/home/me/'
VersionToUpload = 'polis-1.3.1.zip'


def test(connection):
    try:
        result = connection.run('ps -A | grep bash', hide=True)
        msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
        logging.info(msg.format(result))
    except UnexpectedExit:
        logging.info('does not exist !')


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


def create_polis_directory(connection, dir):
    exists = is_directory_exists(connection, dir)
    if not exists :
        result = connection.run('mkdir -p {}'.format(dir), hide=True)
        msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
        logging.info(msg.format(result))
    return exists


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


def transfert_new_version(connection, dir):
    try:
        # Transfer the inflated to file to the target
        result = connection.put('{}{}'.format(SourceFolder, VersionToUpload), dir)
        msg = "Transfered {0} to {1}"
        logging.debug(msg.format(VersionToUpload, connection))
        # deflate the file
        result = connection.run('unzip -u -o {}/{} -d {}'.format(dir, VersionToUpload, dir), hide=True)
        msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
        logging.info(msg.format(result))
        # Delete the archive
        result = connection.run('rm {}/{}'.format(dir, VersionToUpload), hide=True)
        msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
        logging.info(msg.format(result))
        # fix permissions
        result = connection.run('chmod 755 {}/*'.format(dir), hide=True)
        msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
        logging.info(msg.format(result))
    except Exception as e :
        logging.error('Could not deploy : {}'.format(VersionToUpload), exc_info=e)


def start_daemon(connection, dir):
    # Restart the daemon
    try:
        result = connection.run('{}/polisd -daemon -reindex'.format(dir), hide=True)
        msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
        logging.info(msg.format(result))
    except Exception as e :
        logging.error('Could not start  : {}'.format('polisd'), exc_info=e)


def main():
    # create logger
    logger = logging.getLogger('')
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler('debug.log')
    fh.setLevel(logging.DEBUG)
    ch = logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    logger.addHandler(fh)
    logger.addHandler(ch)

    #
    for cnx in ConnectionsList:
        # noinspection PyBroadException
        try :
            connection = Connection(cnx[0], connect_timeout=30)
            target_directory = cnx[1]

            # Create directory if does not exist
            create_polis_directory(connection, target_directory)

            # Stop the daemon if running
            stop_daemon(connection, target_directory)

            # Transfert File to remote directory
            transfert_new_version(connection, target_directory)

            # Start the new daemon
            start_daemon(connection, target_directory)

            logging.info('{} Has been  successfully upgraded'.format(cnx[0]))

        except Exception as e:
            logging.error('Could not upgrade {}'.format(cnx[0]), exc_info=e)


if __name__ == '__main__':
    main()
