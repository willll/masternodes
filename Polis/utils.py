import re
import logging

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
    return result

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
