
from invoke.exceptions import UnexpectedExit
from utils import executeCmd
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
