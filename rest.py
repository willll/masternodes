import time
import sys
import json
import logging
from fabric import Connection
from invoke.exceptions import UnexpectedExit
from klein import Klein
import jinja2
from twisted.internet import defer, task, reactor

file = open("config.json", "r")
config = json.load(file)

app = Klein()

logging.basicConfig(
    filename="debug_rest_py.log",
    filemode="w",
    level=logging.INFO)

'''
'''
@app.route('/')
def hello_world(request):
    return 'Hello, World! <a href="/mns/list">Masternodes</a>' \
           '<a href="/daemon/startpolis">Start Polis</a> <a href=''>Masternodes</a> '


class Coin:
    def __init__(self, name):
        self.name = name

class Polis(Coin):
    def __init__(self, config):
        Coin.__init__(self, "polis")
        self.default_wallet_dir = config["default_wallet_dir"]
        self.default_dir = config["default_dir"]
        self.version_to_upload = config["version_to_upload"]
        self.scripts = config["scripts"]
        self.preconf = config["preconf"]
        self.confdaemon = config["confdaemon"]
        self.cli = config["cli"]
        self.daemon = config["daemon"]
        self.vps = config["vps"]
        self.sentinel_git = config["sentinel_git"]

class VPS:
    def __init__(self, masternode):
        self.masternode = masternode
        kwargs = {}
        if "connection_certificate" in masternode :
            kwargs['key_filename'] = masternode["connection_certificate"]
        else:
            if "password" in masternode:
                kwargs['password'] = masternode["password"]

        try:
            self.connection = Connection(masternode["connection_string"], connect_timeout=31, connect_kwargs=kwargs)
        except UnexpectedExit as e:
            #possibly try to start  the daemon again
            logging.error('{} exited unexpectedly'.format(coin.cli), exc_info=e)
            return '{"status":"restart"}'
        except Exception as e:
            logging.error('Could not do_action {} : {}'.format(masternode["connection_string"], e), exc_info=e)
            return '{"status":"restart"}'

    def __del__(self):
        try:
            self.connection.close()
        except Exception as e:
            logging.error('Could not close connection')
            return 'failed to close connection'

    def actions(self, action):
        try:
            # list of actions that are accepted
            actions = {'clean_wallet':'',
                    'kill_daemon':'',
                    'view_crontab':'crontab -l',
                    'view_script':'',
                    'start_polis':''}

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

    '''
    '''
    def preconf(self, coin):
        try:
            self.connection.put(coin.preconf)
            self.connection.run("/bin/bash {}".format(coin.preconf))
            self.connection.put(coin.version_to_upload)
            result = self.connection.run("mkdir {} && mkdir {} && tar zxvf {} {}".format(config["WalletsFolder"],
                                                                                         coin.default_dir,
                                                                                         coin.version_to_upload,
                                                                                         coin.default_dir), hide=False)

            return result
        except UnexpectedExit as e:
            logging.info("Exceptioin in preconf")
            return '{"status":"failed"}'
        except Exception as e:
            return '{"status":"failed"}'

    '''
    second part configuration script, generates privkey and gets polisd running properly
    TODO: this can easily be all generated within the script and
    simply pasted into the remote .wallet file at location. Might
    require a polisd running locally though, to generate masternode
    privkey 
    '''
    def daemonconf(self, coin):
        try:
            result = self.connection.put(coin.confdaemon )
            result = self.connection.run("/bin/bash {} {} {} {} {}".format(
                coin.confdaemon, coin.coin_name, coin.addnode,
                coin.default_dir, self.getIP()), hide=False)
        except Exception as e:
            logging.error('Exception in daemonconf ')
            return  '{"status":"failed"}'

    '''
    '''
    def install_watcher(self, coin):
        try:
            self.connection.put(coin.scripts["local_path"]+coin.scripts["watcher_cron"])
            logging.info('Uploaded watcher_cron.sh')
            result = self.connection.run("/bin/bash {} {} {} {}".format(
                coin.scripts["watcher_cron"], coin.name, coin.default_dir, coin.daemon,
                coin.default_wallet_dir), hide=False)
            if result.stdout == '' and result.stderr == '':
                return "{'status':'success'}"

            return "{'status':'There was a problem installing watcher'}"
        except UnexpectedExit as e:
            logging.warning('{} exited unexpectedly'.format(coin.cli), exc_info=e)
            return '{"status":"failed"}'
        except Exception as e:
            logging.error('Could not do_action {} : {}'.format(masternode["connection_string"], e), exc_info=e)
            return '{"status":"failed"}'


    def install_sentinel(self, coin):
        try:
            connection.put(coin.scripts["local_path"]+coin.scripts["sentinel_setup"])
            result = connection.run("/bin/bash {} {} {} {}".format(coin.scripts["sentinel_setup"],
                                                                   coin.sentinel_git,
                                                                   coin.default_dir,
                                                                   coin.coin_name), hide=False)
            logging.info('Uploaded sentinel_setup.sh:\n {}'.format(result))
            return result
        except UnexpectedExit as e:
            logging.warning('{} exited unexpectedly'.format(coin.cli), exc_info=e)
            return '{"status":"failed"}'
        except Exception as e:
            logging.error('Could not do_action {} : {}'.format(masternode["connection_string"], e), exc_info=e)
            return '{"status":"failed"}'
    '''
    eventually offer async_cli functions
    '''
    def async_cli(self, action, coin):
        try:
            cmd = "{}/{} --datadir={} {}".format(coin.default_dir,coin.cli, coin.default_wallet_dir, action)
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
            logging.error('Could not do_action {} : {}'.format(self.getIP(), e), exc_info=e)
            return '{"status":"restart"}'

    def daemon_action(self, coin):
        try:
            cmd = "{}/{} --datadir={}".format(coin.default_dir, coin.daemon, coin.default_wallet_dir)
            result = self.connection.run(cmd, hide=False)
            logging.info("Executed {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}".format(result))
            return result.stdout
        except UnexpectedExit as e:
            logging.warning('{} exited unexpectedly'.format(coin.daemon), exc_info=e)
            return '{"status":"restart"}'
        except Exception as e:
            logging.error('Could not do action on daemon at {}'.format(self.getIP()))


'''
Temporary fix for templating
TODO:
    Replace with twisted templating,
    REMOVE
'''
def render_without_request(template_name, **template_vars):
    """
    Usage is the same as flask.render_template:

    render_without_request('my_template.html', var1='foo', var2='bar')
    """
    env = jinja2.Environment(
        loader=jinja2.PackageLoader('rest','templates')
    )
    template = env.get_template(template_name)
    return template.render(**template_vars)


'''
Sub routes pertaining to polis-cli actions
'''
with app.subroute("/daemon") as daemon:
    '''
    startpolis
    Serves a page with all mns and possibility to restart one by selecting

    When given masternodes mns=[indexes,..]  and params it will try to execute: polisd params on each.
    if no params it'll just use default --daemon (not necessary)
    '''
    @daemon.route('/startpolis', methods=['GET', 'POST'])
    def start_polisd(request):

        if request.method == 'POST':
            mns = request.form.getlist('mns')
            actions = request.form.getlist('params')

            result='Attempted starting: '+', '.join(mns)
            for idx in mns:
                vps = VPS(config['masternodes'][int(idx)])
                result = vps.daemon_action(Polis(config["Polis"]))
                logging.info("Restarted {} got: {}".format(vps.getIP(), result))

            return "Result of polisd {}: {} <br><a href=/mns/cli/masternodes/status></a>".format(actions, result)
        else:
            #diisplay list of all MNs with "start" button
            mnlist = "<form method='POST'>\n<select name=mns multiple>\n"
            idx = 0

            for masternode in config["masternodes"]:
                mnlist += "\t<option value='" + str(idx)+ "'>"+ masternode['connection_string']+"</option>\n"
                idx+=1

            mnlist += "</select>\n"
            return mnlist+ "<p><input type=submit value=start></form>"

    '''
    REST endpoint to launch polisd on given server
    TODO:
        It would be useful to have some feedback to the front end as to the status
        maybe a websocket update of getinfo and mnsync status.
    '''
    @daemon.route('/launch', methods=['GET'])
    def daemon_masternode_start(request):
        mn_idx = int(request.args.get(b'mn')[0])

        result = VPS(masternode).daemon_action(config['masternodes'][mn_idx], Polis(config['Polis']))
        logging.info('Executed: polisd @ {} returned: {}'.format(mn_idx, result))
        return result

'''
REST endpoint to clean up wallet dir (rm blockchain files) start daemon with -resync
TODO:
'''

'''
Subroute of script installs (to crontab mostly)
'''
with app.subroute("/scripts") as scripts:
    '''
    Install watcher using this, or get log, or get version (hash).
    '''
    @scripts.route('/watcher', methods=['GET'])
    def watcher_install(request):
        mnidx = int(request.args.get(b'mnidx',[0])[0])
        return VPS(config["masternodes"][mnidx]).install_watcher(Polis(config["Polis"]))

'''
Manage the config file from web
'''
with app.subroute("/config") as conf:
    ''' 
    Return json of config.
    '''
    @conf.route('/read', methods= ['GET'])
    def config_read(request):
        return json.dumps(config)

    '''
    receive json to modify the conf
    '''
    @conf.route('/write', methods= ['POST'])
    def config_write(request):
        return succeed()

    '''
    add configuration for one masternode
    '''
    @conf.route('/mn/add', methods=['post'])
    def config_add_mn(request):
        return succeed()

    '''
    return HTML form to manage config,
    '''
    @conf.route('/view', methods=['GET'])
    def config_view(request):
        return render_without_request()


'''
Create a new MN:
Deploy a new MN based on form information, also save it to config
TODO:
    - Form which takes: IP of new VPS, password of vps, tx output optional
    (eventually generate automatically here through request)
    - Runs script to update VPS, copy polis binary from local,
    generate priv key, install sentinel and crontab job, install
    sscript to watch daemon every minute and relaunch it
'''
@app.route('/create',methods=['POST', 'GET'])
def create(request):
    if request.method == "POST":
        password = request.args.get('password')

        logging.info('ip = {}, password = {}, port = {}, name = {}'.format(request.args.get('ip'),
                                                                           password,
                                                                           request.args.get('port'),
                                                                           request.args.get('name')))

        vps = VPS({
            "connection_sting": "{}@{}:{}".format(request.args.get('user'), request.args.get('host'),
                                                  request.args.get('port')),
            "password": password,
            "name": request.args.get("name")})

        coin = Polis(config['Polis'])

        '''
        does all the apt get
        get polisd from another mn if not available locally (polis.tgz)
        '''
        result = vps.preconf(coin)
        logging.info("Preconf done apt gets and made directorys, copied polis.tgz:\n{}".format(result))

        result = vps.daemonconf(coin)
        logging.info("Daemon configures\n{}".format(result))

        result = vps.install_watcher(Polis(config["Polis"]))
        logging.info('Uploaded and ran watcher_cron.sh :\n {}'.format(result))

        result = vps.install_sentinel(coin)
        logging.info('Uploaded and ran sentinel_setup.sh :\n {}'.format(result))

        config["masternodes"].append(masternode)
        with open('config.json', 'w') as outfile:
            json.dump(config, outfile)

        return result

    else:
        template="new_mn.html"
        return render_without_request(template)

'''
Sub routes pertaining to polis-cli actions
'''
with app.subroute("/mns") as mns:
    '''
    returns rendered list of masternodes (mnlist-jquery.html), with a list of masternodes to preload into DOM
    TODO: change config format to  IP:{...information about masternode..}
    '''
    @mns.route('/list', methods=['GET'])
    def masternodes(request):
        template="mnlist-jquery.html"

        preload = []
        idx=0
        for mn in config["masternodes"]:
            preload.append({"cnx": mn["connection_string"], "idx": idx})
            idx += 1

        logging.info("Returning preloaded template for frontend {}".format(preload))
        return render_without_request(template, masternodes=preload)

    '''
    Read crontab for given mn and return
    '''
    @mns.route('/cron/read')
    def cron_read(request):
        mnidx = int(request.args.get(b'mnidx', [0])[0])
        return succeed()

    '''
    Nonblocking masternode status request using await
    '''
    @mns.route('/cli/mnsync/status', methods=['GET'])
    def cli_mnsync_status(request):
        mnidx = int(request.args.get(b'mnidx', [0])[0])
        logging.info("mnsync status called with mnidx: {} and mnss".format(mnidx))
        request.redirect("/mns/cli/action?mnidx={}&actidx={}".format(mnidx, 'mnss'))
        return None
    '''
    Nonblocking masternode status request using await
    '''
    @mns.route('/cli/masternode/status', methods=['GET'])
    def cli_masternode_status(request):
        mnidx = int(request.args.get(b'mnidx', [0])[0])
        request.redirect("/mns/cli/action?mnidx={}&actidx={}".format(mnidx, 'mnstat'))
        return None

    '''
    Asynchronously do an action part of available actions:
    actidx: the action
    mnidx: index of the masternode
    '''
    @mns.route('/cli/action', methods=['GET'])
    def cli_mn_action(request):
        mnidx =int(request.args.get(b'mnidx', [0])[0])
        actidx =request.args.get(b'actidx', [b'mnstat'])[0]

        logging.info("ARGUMENTS: 1 / {}  /2/ {} /3/ {} ".format(request.args, request.args.get(b'actidx'), actidx))
        actions = {b'mnstat': 'masternode status',
                   b'gi': 'getinfo',
                   b'mnss': 'mnsync status'}

        mn = VPS(config["masternodes"][mnidx])
        coin = Polis(config["Polis"])
        result = mn.async_cli(actions[actidx], coin)
        '''
        TODO: setup a websocket channel to talk to the front end
        '''
        return result

