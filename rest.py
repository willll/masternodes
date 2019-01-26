import json
from klein import Klein
from twisted.web.static import File
from twisted.internet.defer import succeed
import jinja2
from coin import Coin,Polis
from vps import VPS
from config import config,logging
from twisted.internet.defer import inlineCallbacks, returnValue, ensureDeferred
from twisted.internet import threads
from twisted.web import server
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
                vps = VPS(config['masternodes'][int(idx)],Polis(config['Polis']))
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

        result = VPS(config["masternodes"][mn_idx],Polis(config['Polis'])).daemon_action(Polis(config['Polis']))
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
        return VPS(config["masternodes"][mnidx],Polis(config['Polis'])).install_watcher(Polis(config["Polis"]))


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

        coin = Polis(config['Polis'])

        vps = VPS({
            "connection_sting": "{}@{}:{}".format(request.args.get('user'), request.args.get('host'),
                                                  request.args.get('port')),
            "password": password,
            "name": request.args.get("name")},coin)

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
Serve static CSS files/icons
'''
@app.route('/static/', branch=True)
def static_static(request):
    return File("./static")


'''
Serve static Js files
'''
@app.route('/js/', branch=True)
def static_js(request):
    return File("./js")

'''
Requests going straight to the shell or relative to the system itself
'''
with app.subroute("/sys") as sys:
    '''
    Read crontab for given mn and return
    '''
    @sys.route('/cron/read')
    def cron_read(request):
        mnidx = int(request.args.get(b'mnidx', [0])[0])
        coin = Polis(config["Polis"])
        vps = VPS(config["masternodes"][mnidx], coin)
        result = {"result": vps.actions("view_crontab").splitlines()}
        logging.info("Crontab requested got:\n{}".format(result))

        return json.dumps(result)

    '''
    get processes running
    '''
    @sys.route('/ps')
    def ps(request):
        mnidx = int(request.args.get(b'mnidx', [0])[0])
        return returnValue(json.dumps({"result": VPS(config["masternodes"][mnidx], Polis(config["Polis"])).actions("ps").splitlines()}))

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
        vps = VPS(config["masternodes"][mnidx], coin)

        d = ensureDeferred(vps.async_cli(actions[actidx], coin))
        return d
        '''
        TODO: setup a websocket channel to talk to the front end
        TODO: receive config for creation of new mn
        TODO:
        '''
