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
def transfer_new_version(connection, dir, sourceFolder, versionToUpload):
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
def clean_up_wallet_dir(connection, wallet_dir):
    resources_to_delete = ["chainstate", "blocks", "peers.dat"]
    to_delete_str = " ".join(wallet_dir + str(x) for x in resources_to_delete)
    try:
        if wallet_dir == "" :
            raise Exception('Missing wallet directory')
        conx_str = 'rm -rf {}'.format(to_delete_str)
        result = connection.run(conx_str, hide=True)
        msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
        logging.info(msg.format(result))
    except UnexpectedExit as e :
        logging.error('Could not delete : {}'.format(to_delete_str), exc_info=e)


'''

'''
def clean_up_config(connection, wallet_config_file, option):
    try:
        if wallet_config_file == "" :
            raise Exception('Missing wallet configuration file')
        conx_str = ""
        if option == "clear addnode" :
            conx_str = "sed -i '/^addnode/d' {}".format(wallet_config_file)
        elif option == "clear connection" :
            conx_str = "sed -i '/^connection/d' {}".format(wallet_config_file)
        else :
            raise Exception('Invalid option')
        result = connection.run(conx_str, hide=True)
        msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
        logging.info(msg.format(result))
    except UnexpectedExit as e :
        logging.error('Could not clean up : {}'.format(wallet_config_file), exc_info=e)



'''

'''
def start_daemon(connection, dir, wallet_dir="", use_wallet_dir=False):
    # Restart the daemon
    try:
        conx_str = '{}/polisd -daemon -reindex'.format(dir)
        if wallet_dir != "" and use_wallet_dir :
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
