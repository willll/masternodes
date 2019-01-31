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
            self.connection = Connection(self.masternode["connection_string"],
                                         connect_timeout=31, connect_kwargs=kwargs)
        except UnexpectedExit as e:
            #possibly try to start  the daemon again
            logging.error('Connecting failed unexpectedly', exc_info=e)
            return '{"status":"restart"}'
        except Exception as e:
            logging.error(f"Could not do_action {self.masternode['connection_string']} : {e}", exc_info=e)
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
            actions = {"clean_wallet": f"rm -rf {self.wallet_directory}/{{blocks,peers.dat,chainstate}}",
                       "kill_daemon": f"killall -9 {coin.daemon}",
                       "view_crontab": "crontab -l",
                       "ps": "ps -ef"}

            result = self.connection.run(actions[action], hide=False)

            return result.stdout
        except Exception as e :
            logging.error(f"Problem in actions method for {action}", exc_info=e)
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
            logging.info(f"Uploaded {coin.version_to_upload}")
            self.connection.put(coin.scripts["local_path"]+coin.scripts["upgrade"])
            cmd = f"/bin/bash {coin.scripts['upgrade']} {coin.cli} {self.installed_folder} {coin.daemon} {self.wallet_directory} '{coin.addnode}'"
            logging.info(f"Uploaded {coin.scripts['local_path']+coin.scripts['upgrade']}")
            result = self.connection.run(cmd, hide=False)

            logging.info("Done executing: ".format(result.stdout))
            success = f"success: result.stdout: {result.stdout}"
            return success
        except UnexpectedExit as e:
             logging.warning("Problem upgrading", exc_info=e)
             return '{"status":"failed"}'
        except Exception as e:
             logging.warning(f"Could not upload daemon bin: {e} ", exc_info=e)
             return '{"status":"failed"}'

    '''
    '''
    def preconf(self, coin):
        try:
            self.connection.put(coin.scripts["local_path"]+coin.scripts["preconf"])
            cmd = f"/bin/bash {coin.scripts['preconf']}"
            self.connection.run(cmd, hide=False)
            #copy bin
            #remove above hardcoded path
            upload = "Polis/"+coin.version_to_upload
            self.connection.put(upload)
            cmd= f"mkdir {config['WalletsFolder']} && mkdir {self.installed_folder} && tar zxvf {coin.version_to_upload} -C {self.installed_folder}"
            result = self.connection.run(cmd, hide=False)

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
            daemonconf = coin.scripts['local_path']+coin.scripts['confdaemon']
            pw = self.generatePassword()
            ip = self.getIP()
            coin_name = "polis"
            self.connection.put(daemonconf)
            cmd = f"/bin/bash {coin.scripts['confdaemon']} {coin_name} {coin.addnode} {self.installed_folder} {ip} {pw}"
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
            cmd = f"/bin/bash {coin.scripts['watcher_cron']} {coin.name} {self.installed_folder} {coin.daemon} {self.wallet_directory}"
            result = self.connection.run(cmd, hide=False)
            if result.stdout == '' and result.stderr == '':
                return "{'status':'success'}"

            return "{'status':'There was a problem installing watcher'}"
        except UnexpectedExit as e:
            logging.warning(f"{coin.cli} exited unexpectedly", exc_info=e)
            return '{"status":"failed"}'
        except Exception as e:
            logging.error(f"Could not do_action {self.masternode['connection_string']} : {e}", exc_info=e)
            return '{"status":"failed"}'

    def install_sentinel(self, coin):
        try:
            self.connection.put(coin.scripts["local_path"]+coin.scripts["sentinel_setup"])
            cmd = f"/bin/bash {coin.scripts['sentinel_setup']} {coin.sentinel_git} {self.installed_folder} {coin.coin_name} {self.wallet_directory}"
            result = self.connection.run(cmd, hide=False)
            logging.info(f"Uploaded sentinel_setup.sh:\n {result}")
            return result
        except UnexpectedExit as e:
            logging.warning(f"{coin.cli} exited unexpectedly ", exc_info=e)
            return '{"status":"failed"}'
        except Exception as e:
            logging.error(f"Could not do_action {self.masternode['connection_string']} : {e}", exc_info=e)
            return '{"status":"failed"}'
    '''
    eventually offer async_cli functions
    '''
    async def async_cli(self, action, coin):
        try:
            cmd = f"{self.installed_folder}/{coin.cli} --datadir={self.wallet_directory} {action}"
            logging.info(f"Attempting to execute command from masternode object: {cmd}")
            '''
            need to have a threadpool and throw this in there and await the result
            '''
            result = self.connection.run(cmd, hide=False)
            logging.info(f"Executed {result.command} on {result.connection.host}, got stdout:\n{result.stdout}")
            return result.stdout
        except UnexpectedExit as e:
            #possibly try to start  the daemon again
            logging.warning(f"{coin.cli} exited unexpectedly", exc_info=e)
            return '{"status":"restart"}'
        except Exception as e:
            logging.error(f"Could not do action on daemon at {self.getIP()}")

    def kill_daemon(self,coin):
        try:
            kill =f"{self.installed_folder}/{coin.cli} --datadir={self.wallet_directory} stop"
            result = self.connection.run(kill, hide=False)
            return result.stdout
        except UnexpectedExit as e:
            #possibly try to start  the daemon again
            logging.warning(f"{coin.cli} exited unexpectedly", exc_info=e)
            return '{"status":"restart"}'
        except Exception as e:
            logging.error(f"Could not do action on daemon at {self.getIP()}")
            return '{"status":"restart"}'


    def daemon_action(self, coin, reindex = 0):
        try:
            cmd = f"{self.installed_folder}/{coin.daemon} --datadir={self.wallet_directory}"
            if reindex == 1:
                cmd += " -reindex"
            result = self.connection.run(cmd, hide=False)
            logging.info(f"Executed {result.command} on {result.connection.host}, got stdout:\n{result.stdout}")
            return result.stdout
        except UnexpectedExit as e:
            logging.warning(f"{coin.daemon} exited unexpectedly", exc_info=e)
            return '{"status":"restart"}'
        except Exception as e:
            logging.error(f"Could not do action on daemon at {self.getIP()}")
