
from invoke.exceptions import UnexpectedExit
from utils import executeCmd, is_directory_exists
import logging

'''

'''
def is_sentinel_installed(connection):
    is_installed = False
    try:
        # Search for Polis/sentinel in crontable
        result = executeCmd(connection, 'crontab -l | grep -c "Polis/sentinel"')
        if result.stdout == '1\n' :
            is_installed = True

    except UnexpectedExit:
        try:
            # Else look for the wallet directory
            result = executeCmd(connection, 'crontab -l | grep -c ".poliscore/sentinel"')
            if result.stdout == '1\n':
                is_installed = True

        except UnexpectedExit:
            logging.info('{} does not exist !'.format(dir))
    return is_installed

'''

'''
def install_sentinel(connection, wallet_dir):
    try:
        logging.info("Installing sentinel !")
        sentinel_path = wallet_dir + 'sentinel'
        executeCmd(connection, "apt-get install -y virtualenv")
        if is_directory_exists(connection, sentinel_path) :
            executeCmd(connection, "rm -rf {}".format(sentinel_path))
        executeCmd(connection, "git clone https://github.com/polispay/sentinel.git {}".format(sentinel_path))
        executeCmd(connection, "virtualenv {}/venv".format(sentinel_path))
        executeCmd(connection, "{}/venv/bin/pip install -r {}/requirements.txt".format(sentinel_path,sentinel_path))
        executeCmd(connection, "echo polis_conf={}polis.conf >> {}/sentinel.conf".format(wallet_dir, sentinel_path))
        try :
            executeCmd(connection, "crontab -l > {}/tempcron".format(sentinel_path))
        except Exception as e:
            logging.warning('crontab is empty, create a new one', exc_info=e)
            executeCmd(connection, "touch {}/tempcron".format(sentinel_path))
        executeCmd(connection, "echo \"* * * * * cd {}sentinel && ./venv/bin/python bin/sentinel.py 2>&1 >> sentinel-cron.log\" >> {}/tempcron".format(wallet_dir,sentinel_path))
        executeCmd(connection, "crontab {}/tempcron".format(sentinel_path))
        executeCmd(connection, "rm {}/tempcron".format(sentinel_path))
    except Exception as e:
        logging.error('Could not install vps', exc_info=e)
