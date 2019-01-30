import json, time
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
        mn_idx = int(request.args.get(b'mnidx', [0])[0])
        reindex = int(request.args.get(b'reindex', [0])[0])
        coin = Polis(config['Polis'])

        vps = VPS(config["masternodes"][mn_idx], coin)
        result = vps.kill_daemon(coin)
        time.sleep(10)
        logging.info("Killed daemon {}".format(result))
        result = vps.daemon_action(coin, reindex)
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
    @scripts.route('/watcher/<int:mnidx>', methods=['GET'])
    def watcher_install(request, mnidx):
        return VPS(config["masternodes"][mnidx], Polis(config['Polis'])).install_watcher(Polis(config["Polis"]))


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
@app.route('/create', methods=['POST', 'GET'])
def create(request):
    if request.method == b'POST':
        password =(request.args.get(b'password', [0])[0]).decode()
        ip =(request.args.get(b'ip', [0])[0]).decode()
        port =(request.args.get(b'port', [0])[0]).decode()
        name =(request.args.get(b'name', [0])[0]).decode()
        user =(request.args.get(b'user', [0])[0]).decode()

        logging.info('ip = {}, password = {}, port = {}, name = {}'.format(ip, password, port, name))

        coin = Polis(config['Polis'])

        masternode = {"connection_string": "{}@{}:{}".format(user,ip,port), "password": password, "name": name}

        vps = VPS(masternode, coin)

        '''
        does all the apt get
        get polisd from another mn if not available locally (polis.tgz)
        '''
        result = vps.preconf(coin)
        logging.info("Preconf done apt gets and made directorys, copied polis.tgz:\n{}".format(result))

        result = vps.daemonconf(coin)
        logging.info("Daemon configured\n{}".format(result))

        masternode["masternodeprivkey"] = result


        result = vps.install_watcher(Polis(config["Polis"]))
        logging.info('Uploaded and ran watcher_cron.sh :\n {}'.format(result))

        result = vps.install_sentinel(coin)
        logging.info('Uploaded and ran sentinel_setup.sh :\n {}'.format(result))

        config["masternodes"].append(masternode)

        with open('config.json', 'w') as outfile:
            json.dump(config, outfile, sort_keys=True, indent=4, ensure_ascii=False)

        return "{{\"status\":\"{}}}\"".format(masternode.masternodeprivkey)

    else:
        template= "new_mn.html"
        return render_without_request(template)

'''
Upgrade masternode to new version
 ->
 (VPS)
 polis-cli stop,
 put new bins,
 clear dat blockchain cache,
 start_daemon,
 (local)
 masternode start 

@param mnidx: index of the masternode to upgrade
'''
@app.route('/upgrade/<int:mnidx>/', methods=['GET'])
def upgrade(request, mnidx):
    coin = Polis(config["Polis"])
    vps = VPS(config["masternodes"][mnidx], coin)

    logging.info("vps.upgrade called ! for: {}".format(vps.getIP()))
    result = vps.upgrade(coin)
    return result





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
    @sys.route('/cron/read/<int:mnidx>')
    def cron_read(request, mnidx):
        coin = Polis(config["Polis"])
        vps = VPS(config["masternodes"][mnidx], coin)
        result = {"result": vps.actions("view_crontab", coin).splitlines()}
        logging.info("Crontab requested got:\n{}".format(result))

        return json.dumps(result)

    '''
    get processes running
    '''
    @sys.route('/ps/<int:mnidx>')
    def ps(request, mnidx):
        coin = Polis(config["Polis"])
        return returnValue(json.dumps({"result": VPS(config["masternodes"][mnidx], coin).actions("ps", coin).splitlines()}))

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
    @mns.route('/cli/mnsync/reset/<int:mnidx>', methods=['GET'])
    def cli_mnsync_reset(request, mnidx):
        logging.info("mnsync status called with mnidx: {} and mnss".format(mnidx))
        request.redirect("/mns/cli/action?mnidx={}&actidx={}".format(mnidx, 'mnsr'))
        return None


    '''
    Nonblocking masternode status request using await
    '''
    @mns.route('/cli/mnsync/status/<int:mnidx>', methods=['GET'])
    def cli_mnsync_status(request, mnidx):
        logging.info("mnsync status called with mnidx: {} and mnss".format(mnidx))
        request.redirect("/mns/cli/action?mnidx={}&actidx={}".format(mnidx, 'mnss'))
        return None


    '''
    Nonblocking masternode status request using await
    '''
    @mns.route('/cli/<int:mnidx>/masternode/status', methods=['GET'])
    def cli_masternode_status(request, mnidx):
        redirect = "/mns/cli/action/{}/{}".format(mnidx, 'mnstat')
        request.redirect(redirect)
        return None

    '''
    Asynchronously do an action part of available actions:
    actidx: the action
    mnidx: index of the masternode
    '''
    @mns.route('/cli/action/<int:mnidx>/<actidx>', methods=['GET'])
    async def cli_mn_action(request, mnidx, actidx = 0):
        actions = {'mnstat': 'masternode status',
                   'gi': 'getinfo',
                   'mnss': 'mnsync status',
                   'mnsr': 'mnsync reset'}

        coin = Polis(config["Polis"])
        vps = VPS(config["masternodes"][mnidx], coin)

        d = await vps.async_cli(actions[actidx], coin)
        return d

