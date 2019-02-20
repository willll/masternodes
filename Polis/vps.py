from invoke.exceptions import UnexpectedExit
from utils import execute_command, is_file_exists
import logging



'''
is_genkey_unique
'''
def is_genkey_unique(config):
    is_unique = True
    duplicates = []
    tmp = {}
    for conf in config["masternodes"] :
        if "private_key" in conf :
            if tmp.get(conf["private_key"]) == None:
                tmp[conf["private_key"]] = conf["connection_string"]
            else :
                duplicates.append(conf["connection_string"])
                duplicates.append(tmp.get(conf["private_key"]))
                is_unique = False
                continue
    return (is_unique, duplicates)


'''
is_vps_installed
'''
def is_vps_installed(connection):
    is_installed = False
    try:
        # Search for libdb4.8-dev package,
        result = execute_command(connection, 'dpkg-query -W --showformat=\'${Status}\n\' libdb4.8-dev | grep -c "install ok installed"')
        if result.stdout == '1\n' :
            is_installed = True
    except UnexpectedExit:
        logging.info('{} does not exist !'.format(dir))
    return is_installed


'''
is_polis_installed
'''
def is_polis_installed(connection, dir):
    return is_file_exists(connection, "{}/{}".format(dir, 'polisd'))


'''
is_monitoring_script_installed
'''
def is_monitoring_script_installed(connection):
    is_installed = False
    try:
        # Search for Polis/sentinel in crontable
        result = execute_command(connection, 'crontab -l | grep -c "polischk.sh"')
        if result.stdout == '1\n' :
            is_installed = True

    except UnexpectedExit:
        logging.info('Monitoring script is not installed !')
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
                execute_command(connection, '{}'.format(cmd))

        logging.info("Download dependencies !")
        for cmd in cmds_apt_get:
            execute_command(connection, '{}'.format(cmd))
    except Exception as e:
        logging.error('Could not install vps', exc_info=e)
