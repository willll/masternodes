from invoke.exceptions import UnexpectedExit
from utils import executeCmd
import logging

'''

'''
def is_vps_installed(connection):
    is_installed = False
    try:
        # Search for libdb4.8-dev package,
        result = executeCmd(connection, 'dpkg-query -W --showformat=\'${Status}\n\' libdb4.8-dev | grep -c "install ok installed"')
        if result.stdout == '1\n' :
            is_installed = True
    except UnexpectedExit:
        logging.info('{} does not exist !'.format(dir))
    return is_installed

'''

'''
def is_polis_installed(connection, ):
    is_installed = False
    try:
        # Search for libdb4.8-dev package,
        result = executeCmd(connection, '| grep -c "install ok installed"')
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
