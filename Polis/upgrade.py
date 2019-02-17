# system imports
import logging
import sys
import json
import os
import argparse

# third party imports
from fabric import Connection

# project imports
import utils
import info
import sentinel
import vps
from polis import Polis

'''
    Globals
'''
default_wallet_dir = ""
default_wallet_conf_file = ""


'''

'''
def get_wallet_dir(cnx):
    wallet_dirs = []
    use_wallet_dir = False
    if "wallet_directories" in cnx:
        for wallet in cnx["wallet_directories"]:
            wallet_dirs.append(wallet["wallet_directory"])
        use_wallet_dir = True
    elif "wallet_directory" in cnx:
        wallet_dirs = [cnx["wallet_directory"]]
    else:
        wallet_dirs = [ default_wallet_dir ]
    return (wallet_dirs, use_wallet_dir)


'''
Create a Polis connection
'''
def create_polis_connection(conf):
    kwargs = {}
    if "connection_certificate" in conf:
        kwargs['key_filename'] = conf["connection_certificate"]
    else:
        # Must be mutually excluded
        if "connection_password" in conf:
            kwargs['password'] = conf["connection_password"]

    connection = Connection(conf["connection_string"], connect_timeout=30, connect_kwargs=kwargs)

    target_directory = conf["destination_folder"]

    wallet_dirs, use_wallet_dir = get_wallet_dir(conf)

    polis = Polis(connection, target_directory)
    return polis, wallet_dirs, use_wallet_dir, connection

'''
Moves a masternode to another VPS
'''
def move_masternode(masternodeMove, config, configfilename):

    cpt = 0
    source = 0
    destination = 0
    for tmp in config:
        if cpt == masternodeMove[0]:
           source = tmp
        if cpt == masternodeMove[1]:
           destination = tmp
        cpt+=1

    if source == 0 or destination == 0 :
        logging.error('Could not move addnode {} to {}'.format(masternodeMove[0], masternodeMove[1]))
        Exception('Bad mova arguments')

    # Create source connection
    polis_source, source_wallet_dirs, source_use_wallet_dir, source_connection = create_polis_connection(source)

    # Create destination connection
    polis_destination, destination_wallet_dirs, destination_source_use_wallet_dir, destination_connection = create_polis_connection(destination)

    polis_source.stop_daemon()
    polis_destination.stop_daemon()

    destination["wallet_directory"] = source["wallet_directory"]
    destination["private_key"] = source["private_key"]
    destination["outputs"] = source["outputs"]
    source["wallet_directory"] = ""
    source["private_key"] = ""
    source["outputs"] = ""

    for wallet_dir in source_wallet_dirs:
        wallet_conf_file = wallet_dir + default_wallet_conf_file

        if not utils.is_directory_exists(source_connection, wallet_dir):
            polis.create_wallet_dir(wallet_dir,
                                    utils.get_ip_from_connection_string(conf["connection_string"]),
                                    conf["private_key"])

        # Clean up old wallet dir
        polis.clean_up_wallet_dir(wallet_dir)

        # Clean up the config file
        if args.cleanConfig:
            polis.clean_up_config(wallet_conf_file, "clear addnode")

        # Add addnode in the config file
        if args.addNodes:
            polis.add_addnode(wallet_conf_file)

        if args.installBootstrap:
            polis.install_boostrap(conf)
        else:
            # Start the new daemon
            polis.start_daemon(wallet_dir, use_wallet_dir)

        # install sentinel
        if not sentinel.is_sentinel_installed(connection):
            sentinel.install_sentinel(connection, wallet_dir)

    polis_destination.create_wallet_dir(wallet_dir,
                                        utils.get_ip_from_connection_string(conf["connection_string"]),
                                        destination["private_key"], True)


'''

'''
def init(args):
    # create logger
    debug_level = logging.INFO

    if args.masternodeStatus or args.masternodeConf or args.masternodeDiagnostic :
        debug_level = logging.ERROR

    logger = logging.getLogger('logger')
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler('debug.log')
    fh.setLevel(logging.DEBUG)
    ch = logging.basicConfig(stream=sys.stdout, level=debug_level)
    logger.addHandler(fh)
    logger.addHandler(ch)

'''

'''
def main():
    global default_wallet_dir
    global default_wallet_conf_file

    # CLI arguments
    parser = argparse.ArgumentParser(description='Masternodes upgrade script')
    parser.add_argument('--config', nargs='?', default="config.json", help='config file in Json format')
    parser.add_argument('-deploy', action='store_true', help='deploy a new version')
    parser.add_argument('-cleanConfig', action='store_true', help='clean up to config files')
    parser.add_argument('-addNodes', action='store_true', help='edit the config file to add addnode entries')
    parser.add_argument('-r', '--reindex', action='store_true', help='reindex the masternodes')
    parser.add_argument('-installVPS', action='store_true', help='install the VPSs')
    parser.add_argument('-installBootstrap', action='store_true', help='install the bootstrap')
    parser.add_argument('-installSentinel', action='store_true', help='install sentinel')
    parser.add_argument('-deployConfig', action='store_true', help='deploy polis.conf')
    parser.add_argument('-s', '--startDaemon', action='store_true', help='start the daemon')
    parser.add_argument('-masternodeConf', action='store_true', help='output the masternode.conf content')
    parser.add_argument('-ls','--masternodeStatus', action='store_true', help='output the masternode status')
    parser.add_argument('-masternodeDiagnostic', action='store_true', help='output diagnostics')
    parser.add_argument('-grep', '--masternodeList', nargs='+', type=int, help='filter mastenodes by id')
    parser.add_argument('-mv', '--masternodeMove', nargs=2, type=int, help='move masternodes from one id to another')
    args = parser.parse_args()

    init(args)

    # Load configuration file
    file = open(args.config)
    config = json.load(file)

    # Global settings
    default_wallet_dir = config["Polis"]["default_wallet_dir"]
    default_wallet_conf_file = config["Polis"]["default_wallet_conf_file"]

    masternode_output = ""

    connection_string_max_length = utils.max_string_length(config["masternodes"])

    masternode_index = -1

    if args.masternodeMove:
        move_masternode(args.masternodeMove, config["masternodes"])
        logging.info('{} Has been successfully moved to {}'.format(args.masternodeMove[0], args.masternodeMove[1]))
        utils.backup_configuration_file(args.config)
        json.dump(config, file)
    #
    for conf in config["masternodes"]:
        masternode_index += 1
        # noinspection PyBroadException
        try:

            if args.masternodeList and masternode_index not in args.masternodeList:
                continue

            target_directory = conf["destination_folder"]

            polis, wallet_dirs, use_wallet_dir, connection = create_polis_connection(conf)

            if args.masternodeDiagnostic:
                f = "{0:<4}: {1:<%d}: {2}\n" % (connection_string_max_length + 1)
                for wallet_dir in wallet_dirs:
                    masternode_output += f.format(masternode_index,
                                                  conf["connection_string"],
                                                  info.get_masternode_diagnostic(connection, target_directory, wallet_dir, use_wallet_dir))

            if args.masternodeStatus:
                f = "\r\n{0:<4}: {1:<%d}:\r\n{2}" % (connection_string_max_length + 1)
                for wallet_dir in wallet_dirs:
                    masternode_output += f.format(masternode_index,
                                                  conf["connection_string"],
                                                  info.get_masternode_status(connection, target_directory, wallet_dir, use_wallet_dir))


            if args.masternodeConf and "private_key" in conf :
                masternode_output += "{0:>15} {}:24126 {1} {2}\n".format(conf["connection_string"],
                                                          utils.get_ip_from_connection_string(conf["connection_string"]),
                                                          conf["private_key"],
                                                          conf["outputs"])

            if args.startDaemon:
                for wallet_dir in wallet_dirs:
                    polis.start_daemon(wallet_dir, use_wallet_dir)
                    logging.info('{} Has been successfully reindexed'.format(conf["connection_string"]))

            if args.reindex:
                polis.reindex_masternode(conf)
                logging.info('{} Has been successfully reindexed'.format(conf["connection_string"]))

            if args.installVPS:
                if not vps.is_vps_installed(connection):
                    vps.install_vps(connection)
                    logging.info('{} Has been successfully installed'.format(conf["connection_string"]))
                else:
                    logging.info('{} Already installed'.format(conf["connection_string"]))

            if args.installBootstrap and not args.deploy:
                polis.install_boostrap(conf)
                logging.info('{} Has been successfully reindexed'.format(conf["connection_string"]))

            if args.installSentinel and not args.deploy:
                for wallet_dir in wallet_dirs:
                    # install sentinel
                    if not sentinel.is_sentinel_installed(connection):
                        sentinel.install_sentinel(connection, wallet_dir)

            if args.deployConfig:
                for wallet_dir in wallet_dirs:
                    wallet_conf_file = wallet_dir + default_wallet_conf_file
                    polis.create_wallet_dir(wallet_dir,
                                      utils.get_ip_from_connection_string(conf["connection_string"]),
                                      conf["private_key"], True)
                    if args.addNodes:
                        polis.add_addnode(wallet_conf_file)
                logging.info('{} Has been successfully configured'.format(conf["connection_string"]))

            if args.deploy:
                # Install VPS
                if not vps.is_vps_installed(connection):
                    vps.install_vps(connection)

                # Create directory if does not exist
                polis.create_polis_directory()

                # Stop the daemon if running
                polis.stop_daemon()

                # Transfer File to remote directory
                polis.transfer_new_version(config["SourceFolder"], config["VersionToUpload"])

                for wallet_dir in wallet_dirs:
                    wallet_conf_file = wallet_dir+default_wallet_conf_file

                    if not utils.is_directory_exists(connection, wallet_dir):
                        polis.create_wallet_dir(wallet_dir,
                                          utils.get_ip_from_connection_string(conf["connection_string"]),
                                          conf["private_key"])

                    # Clean up old wallet dir
                    polis.clean_up_wallet_dir(wallet_dir)

                    # Clean up the config file
                    if args.cleanConfig:
                        polis.clean_up_config(wallet_conf_file, "clear addnode")

                    # Add addnode in the config file
                    if args.addNodes:
                        polis.add_addnode(wallet_conf_file)

                    if args.installBootstrap:
                        polis.install_boostrap(conf)
                    else:
                        # Start the new daemon
                        polis.start_daemon(wallet_dir, use_wallet_dir)

                    # install sentinel
                    if not sentinel.is_sentinel_installed(connection):
                        sentinel.install_sentinel(connection, wallet_dir)

                logging.info('{} Has been successfully upgraded'.format(conf["connection_string"]))

        except Exception as e:
            logging.error('Could not upgrade {}'.format(conf["connection_string"]), exc_info=e)

    if args.masternodeDiagnostic:
        is_unique, duplicates = vps.is_genkey_unique(config)
        if not is_unique:
            masternode_output += "Found duplicate keys : {} and {}".format(duplicates[0], duplicates[1])


    if args.masternodeStatus or args.masternodeConf or args.masternodeDiagnostic:
        print(masternode_output)


if __name__ == '__main__':
    main()
