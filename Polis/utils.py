import re
import os
import datetime
import logging
import shutil
from invoke.exceptions import UnexpectedExit
# third party imports
from patchwork.files import exists

'''
execute_command
'''


def execute_command(connection, cmd, hide=True):
    result = connection.run(cmd, hide=hide)
    msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
    logging.info(msg.format(result))
    return result


'''
send_file
'''


def send_file(connection, source_file, destination_dir):
    result = connection.put(source_file, destination_dir)
    msg = "Transfered {0} to {1}"
    logging.debug(msg.format(source_file, destination_dir))
    return result


'''
is_directory_exists
'''


def is_directory_exists(connection, directory):
    is_exists = False
    try:
        execute_command(connection, '[[ -d {} ]]'.format(directory), False)
        is_exists = True
    except UnexpectedExit:
        logging.info('{} does not exist !'.format(directory))
    return is_exists


'''
is_file_exists
'''


def is_file_exists(connection, file):
    return exists(connection, file)


'''
is_file_exists
'''


def control_cron_service(connection, start = False):
    cmd = "sudo /etc/init.d/cron "
    try:
        if start:
            cmd += "start"
        else :
            cmd += "stop"

        execute_command(connection, '{}'.format(cmd))
        is_exists = True
    except UnexpectedExit as e:
        logging.info('could not execute : {} ({})'.format(cmd, e))



'''
max_string_length
'''


def max_string_length(masternode):
    result = 0
    for mn in masternode:
        result = max(result, len(mn["connection_string"]))
    return result


'''
get_ip_from_connection_string
'''


def get_ip_from_connection_string(string):
    ip = re.compile('(([2][5][0-5]\.)|([2][0-4][0-9]\.)|([0-1]?[0-9]?[0-9]\.)){3}'
                +'(([2][5][0-5])|([2][0-4][0-9])|([0-1]?[0-9]?[0-9]))')
    match = ip.search(string)
    return match.group()


'''
Backup configuration file
'''


def backup_configuration_file(filename):
    strdate = datetime.datetime.now().strftime("%Y-%m-%d#%H:%M:%S")
    targetdir = "backup/"
    targetfile = targetdir + strdate + "_" + filename

    try:
        shutil.copy2(os.path.realpath(filename), os.path.realpath(targetfile))
    except FileNotFoundError:
        os.makedirs(os.path.dirname(targetdir))
        backup_configuration_file(filename)
