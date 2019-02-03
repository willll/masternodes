import re
import logging
from invoke.exceptions import UnexpectedExit

'''

'''
def executeCmd(connection, cmd, hide=True) :
    result = connection.run(cmd, hide=hide)
    msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
    logging.info(msg.format(result))
    return result

'''

'''
def sendFile(connection, source_file, destination_dir) :
    result = connection.put(source_file, destination_dir)
    msg = "Transfered {0} to {1}"
    logging.debug(msg.format(source_file, destination_dir))
    return result



    result = connection.run(cmd, hide=hide)
    msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
    logging.info(msg.format(result))

'''

'''
def is_directory_exists(connection, dir):
    is_exists = False
    try:
        executeCmd(connection, '[[ -d {} ]]'.format(dir))
        is_exists = True;
    except UnexpectedExit:
        logging.info('{} does not exist !'.format(dir))
    return is_exists

'''

'''
def is_file_exists(connection, file):
    is_exists = False
    try:
        executeCmd(connection, '[[ -f {} ]]'.format(file))
        is_exists = True;
    except UnexpectedExit:
        logging.info('{} does not exist !'.format(file))
    return is_exists

'''

'''
def maxStringsLength(masternode) :
    result = 0
    for mn in masternode :
        result = max(result, len(mn["connection_string"]))
    return result

'''

'''
def get_ip_from_connection_string(str) :
    ip = re.compile('(([2][5][0-5]\.)|([2][0-4][0-9]\.)|([0-1]?[0-9]?[0-9]\.)){3}'
                +'(([2][5][0-5])|([2][0-4][0-9])|([0-1]?[0-9]?[0-9]))')
    match = ip.search(str)
    return match.group()
