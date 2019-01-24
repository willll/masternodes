from fabric import Connection
from klein import Klein
import jinja2
from coin import Coin,Polis
from vps import VPS
from config import config,logging

app = Klein()


'''
'''
@app.route('/')
def hello_world(request):
    return 'Hello, World! <a href="/mns/list">Masternodes</a>' \
           '<a href="/daemon/startpolis">Start Polis</a> <a href=''>Masternodes</a> '

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
'''
def shell_actions(action, masternode):
    try:
        # list of actions that are accepted
        actions = {'clean_wallet':'',
                'kill_daemon':'',
                'view_crontab':'crontab -l',
                'view_script':'',
                'start_polis':''}

        kwargs = {}
        if "connection_certificate" in masternode :
            kwargs['key_filename'] = masternode["connection_certificate"]
        else:
            # Must be mutually excluded
            if "password" in masternode:
                kwargs['password'] = masternode["password"]

        connection = Connection(masternode["connection_string"],  connect_timeout=31, connect_kwargs=kwargs)
        logging.info('>>> Got connection to {} using {} '.format(masternode["connection_string"], kwargs))

        result =  connection.run(actions[action], hide=False)
        logging.info(">>> Executed {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}".format(result))

        connection.close()
        return result
    except Exception as e :
        logging.error('Could not getinfo  : {}'.format('polisd'), exc_info=e)
        return "shell_actions failed"

'''
This can be used to restart daemon if getinfo isnt responding, and mn is down likely because it crashed
'''
def do_action_daemon(masternode, action = ['--daemon'], coin = 'Polis'):
    try:
        kwargs = {}
        if "connection_certificate" in masternode :
            kwargs['key_filename'] = masternode["connection_certificate"]
        else :
            # Must be mutually excluded
            if "password" in masternode:
                kwargs['password'] = masternode["password"]

        connection = Connection(masternode["connection_string"],  connect_timeout=31, connect_kwargs=kwargs)
        logging.info('>>> Got connection to {} using {} '.format(masternode["connection_string"], kwargs))

        if "destination_folder" in masternode: 
            conx_str = '{}/{}'.format( masternode["destination_folder"],
                                      config[coin]["daemon"])
        elif "default_dir" in config[coin]:
            conx_str = '{}/{}'.format(config[coin]["default_dir"],
                                      config[coin]["daemon"])
        else:
            conx_str = config[coin]["daemon"]

        if "wallet_directory" in masternode :
            wallet_dir = masternode["wallet_directory"]
            conx_str += " --datadir=" + wallet_dir
        elif config[coin]["default_wallet_dir"]:
            conx_str += " --datadir=" + config[coin]["default_wallet_dir"]

        conx_str += " "+action
        result =  connection.run(conx_str, hide=False)
        logging.info('{} executed on {}'.format(action, masternode["connection_string"]))

        connection.close()
        logging.info('Connection closed to {} '.format(masternode["connection_string"]))
        return result.stdout

    except Exception as e:
        logging.error('Problem in do_action_daemon {}'.format(masternode["connection_string"]), exc_info=e)
        return 'failed'

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
                address = config['masternodes'][int(idx)]
                result = "<p>Masternode: "+str(address)+"</p>"
                for r in do_action_daemon(address, actions):
                    result += "<p>"+str(r) +"</p>\n"

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
        result = do_action_daemon(config['masternodes'][mn_idx])
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
        masternode = config["masternodes"][mnidx]
        return VPS(masternode).install_watcher(Polis(config["Polis"]))

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
    if(request.method == "POST"):

        password = request.args.get('password')

        logging.info('ip = {}, password = {}, port = {}, name = {}'.format(request.args.get('ip'),
            password,request.args.get('port'),request.args.get('name')))

        vps = VPS({
            "connection_sting": "{}@{}:{}".format(request.args.get('user'), request.args.get('host'),
                request.args.get('port)')),
            "password":password,
            "name":request.args.get("name") })

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

        #save masternode to config.json.
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

        coin = Polis(config["Polis"])
        mn = VPS(config["masternodes"][mnidx], coin)
        result = mn.async_cli(actions[actidx], coin)

        return result
