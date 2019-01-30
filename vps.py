from invoke.exceptions import UnexpectedExit
from fabric import Connection
from config import logging,config
import secrets
import string


class VPS:
    def __init__(self, masternode, coin):
        self.masternode = masternode
        kwargs = {}
        if "connection_certificate" in masternode :
            kwargs['key_filename'] = masternode["connection_certificate"]
        else:
            if "password" in masternode:
                kwargs['password'] = masternode["password"]

        if "destination_folder" in masternode :
            self.installed_folder = masternode["destination_folder"]
        else:
            self.installed_folder = coin.default_dir

        if "wallet_directory" in masternode :
            self.wallet_directory = masternode["wallet_directory"]
        else:
            self.wallet_directory = coin.default_wallet_dir


        try:
            self.connection = Connection(masternode["connection_string"],
                                         connect_timeout=31, connect_kwargs=kwargs)
        except UnexpectedExit as e:
            #possibly try to start  the daemon again
            logging.error('Connecting failed unexpectedly', exc_info=e)
            return '{"status":"restart"}'
        except Exception as e:
            logging.error('Could not do_action {} : {}'.format(self.masternode["connection_string"], e),
                          exc_info=e)
            return '{"status":"restart"}'

    def __del__(self):
        try:
            self.connection.close()
        except Exception as e:
            logging.error('Could not close connection')
            return 'failed to close connection'

    def actions(self, action, coin):
        try:
            # list of actions that are accepted
            actions = {'clean_wallet':'rm -rf {}/{{blocks,peers.dat,chainstate}}'.format(coin.default_wallet_dir),
                       'kill_daemon':'killall -9 {}'.format(coin.daemon),
                       'view_crontab':'crontab -l', 'ps':'ps -ef'}

            result = self.connection.run(actions[action], hide=False)

            return result.stdout
        except Exception as e :
            logging.error('Problem in actions method for {}'.format(action), exc_info=e)
            return "{'status':'restart'}"

    '''
    check file's hash, useful to check if a script is correct
    '''
    def check_file(self):
        return
    '''
    '''
    def check_watcher_log(self):
        return

    def getIP(self):
        return self.masternode["connection_string"].split("@")[1].split(":")[0]

    def upgrade(self, coin):
        try:
            self.connection.put("Polis/"+coin.version_to_upload)
            logging.info("Uploaded {}".format(coin.version_to_upload))
            self.connection.put(coin.scripts["local_path"]+coin.scripts["upgrade"])
            cmd = "/bin/bash {} {} {} {} {} \"{}\"".format(coin.scripts["upgrade"], coin.cli, coin.default_dir, coin.daemon, coin.default_wallet_dir, coin.addnode)
            logging.info("Uploaded {}".format(coin.scripts["local_path"]+coin.scripts["upgrade"]))
            result = self.connection.run(cmd, hide=False)

            logging.info("Done executing: ".format(result.stdout))
            success = "success: result.stdout: {}".format(result.stdout)
            return success
        except UnexpectedExit as e:
             logging.warning("Problem upgrading", exc_info=e)
             return '{"status":"failed"}'
        except Exception as e:
             logging.warning("Could not upload daemon bin: ".format(e), exc_info=e)
             return '{"status":"failed"}'

    '''
    '''
    def preconf(self, coin):
        try:
            self.connection.put(coin.preconf)
            self.connection.run("/bin/bash {}".format(coin.preconf))
            self.connection.put(coin.version_to_upload)
            result = self.connection.run("mkdir {} && mkdir {} && tar zxvf {} {}".format(config["WalletsFolder"],
                                                                                         self.installed_folder,
                                                                                         coin.version_to_upload,
                                                                                         self.installed_folder), hide=False)

            return result
        except UnexpectedExit as e:
            logging.info("Exceptioin in preconf")
            return '{"status":"failed"}'
        except Exception as e:
            return '{"status":"failed"}'


    '''
    Generate password for rpc using this.
    
    '''
    def generatePassword(self , length=30):
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for i in range(length))
        return password


    ''' 
    second part configuration script, generates privkey and gets polisd running properly
    TODO: this can easily be all generated within the script and
    simply pasted into the remote .wallet file at location. Might
    require a polisd running locally though, to generate masternode
    privkey 
    '''
    def daemonconf(self, coin):
        try:
            self.connection.put(coin.scripts['local_path']+coin.scripts['confdaemon'])
            cmd = "/bin/bash {} {} {} {} {}".format(coin.scripts['confdaemon'], coin.coin_name, coin.addnode,
                                                     coin.default_dir, self.getIP(), self.generatePassword())
            result = self.connection.run(cmd, hide=False)
            #should contain masternodeprivkey
            return result.stdout
        except Exception as e:
            logging.error('Exception in daemonconf ')
            return '{"status":"failed"}'

    '''
    '''
    def install_watcher(self, coin):
        try:
            self.connection.put(coin.scripts["local_path"]+coin.scripts["watcher_cron"])
            logging.info('Uploaded watcher_cron.sh')
            cmd = "/bin/bash {} {} {} {} {}".format(coin.scripts["watcher_cron"], coin.name, coin.default_dir, coin.daemon,
                                                 coin.default_wallet_dir)
            result = self.connection.run(cmd, hide=False)
            if result.stdout == '' and result.stderr == '':
                return "{'status':'success'}"

            return "{'status':'There was a problem installing watcher'}"
        except UnexpectedExit as e:
            logging.warning('{} exited unexpectedly'.format(coin.cli), exc_info=e)
            return '{"status":"failed"}'
        except Exception as e:
            logging.error('Could not do_action {} : {}'.format(self.masternode["connection_string"], e), exc_info=e)
            return '{"status":"failed"}'

    def install_sentinel(self, coin):
        try:
            self.connection.put(coin.scripts["local_path"]+coin.scripts["sentinel_setup"])
            result = self.connection.run("/bin/bash {} {} {} {}".format(coin.scripts["sentinel_setup"],
                                                                   coin.sentinel_git,
                                                                    self.installed_folder,
                                                                   coin.coin_name), hide=False)
            logging.info('Uploaded sentinel_setup.sh:\n {}'.format(result))
            return result
        except UnexpectedExit as e:
            logging.warning('{} exited unexpectedly'.format(coin.cli), exc_info=e)
            return '{"status":"failed"}'
        except Exception as e:
            logging.error('Could not do_action {} : {}'.format(self.masternode["connection_string"], e), exc_info=e)
            return '{"status":"failed"}'
    '''
    eventually offer async_cli functions
    '''
    async def async_cli(self, action, coin):
        try:
            cmd = "{}/{} --datadir={} {}".format(self.installed_folder, coin.cli, self.wallet_directory, action)
            logging.info("Attempting to execute command from masternode object: {}".format(cmd))
            '''
            need to have a threadpool and throw this in there and await the result
            '''
            result = self.connection.run(cmd, hide=False)
            logging.info("Executed {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}".format(result))
            return result.stdout
        except UnexpectedExit as e:
            #possibly try to start  the daemon again
            logging.warning('{} exited unexpectedly'.format(coin.cli), exc_info=e)
            return '{"status":"restart"}'
        except Exception as e:
            logging.error('Could not do action on daemon at {}'.format(self.getIP()))

    def kill_daemon(self,coin):
        try:
            kill ="{}/{} --datadir={} stop".format(self.installed_folder, coin.cli, self.wallet_directory)
            result = self.connection.run(kill, hide=False)
            return result.stdout
        except UnexpectedExit as e:
            #possibly try to start  the daemon again
            logging.warning('{} exited unexpectedly'.format(coin.cli), exc_info=e)
            return '{"status":"restart"}'
        except Exception as e:
            logging.error('Could not do action on daemon at {}'.format(self.getIP()))
            return '{"status":"restart"}'


    def daemon_action(self, coin, reindex = 0):
        try:
            cmd = "{}/{} --datadir={}".format(self.installed_folder, coin.daemon, self.wallet_directory)
            if reindex == 1:
                cmd += " -reindex"
            result = self.connection.run(cmd, hide=False)
            logging.info("Executed {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}".format(result))
            return result.stdout
        except UnexpectedExit as e:
            logging.warning('{} exited unexpectedly'.format(coin.daemon), exc_info=e)
            return '{"status":"restart"}'
        except Exception as e:
            logging.error('Could not do action on daemon at {}'.format(self.getIP()))
