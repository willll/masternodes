import time
import sys
import json
import logging
from fabric import Connection
from invoke.exceptions import UnexpectedExit
from klein import Klein
import jinja2
import hashlib

file = open("config.json", "r") 
config = json.load(file)

app = Klein()

logging.basicConfig(
    filename = "debug_rest_py.log",
    filemode="w",
    level = logging.INFO)

'''
''' 
@app.route('/')
def hello_world(request):
    return 'Hello, World! <a href="/mns/list">Masternodes</a> <a href="/daemon/startpolis">Start Polis</a> <a href=''>Masternodes</a> '
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
async def shell_actions(action, connection, dir, wallet_dir="", use_wallet_dir=False):
    try:
        # list of actions that are accepted
        actions = {'clean_wallet':'', 
                'kill_daemon':'',
                'view_crontab':'',
                'view_script':'',
                'start_polis':''}

        
        result = await connection.run(conx_str, hide=False)
        logging.info(">>> Executed {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}".format(result))

        return result
    except Exception as e :
        logging.error('Could not getinfo  : {}'.format('polisd'), exc_info=e)
        return "failed"


'''
'''
async def any_daemon(action, connection, dir, wallet_dir="", use_wallet_dir=False):
    try:
        conx_str = '{}/polisd'.format(dir)
        if wallet_dir != "" and use_wallet_dir :
            conx_str += " --datadir=" + wallet_dir
        conx_str += " "+action

        result = await connection.run(conx_str, hide=False)
        logging.info("Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}".format(result))

        return result
    except Exception as e :
        logging.error('Could not getinfo  : {}'.format('polisd'), exc_info=e)
        return "failed"

''' 
This can be used to restart daemon if getinfo isnt responding, and mn is down likely because it crashed
'''
async def do_action_daemon(masternode, actions = ['--daemon']):
    try:
        kwargs = {}
        if "connection_certificate" in masternode :
            kwargs['key_filename'] = masternode["connection_certificate"]
        else :
            # Must be mutually excluded
            if "password" in masternode:
                kwargs['password'] = masternode["password"]

        connection = Connection(masternode["connection_string"],  connect_timeout=30, connect_kwargs=kwargs)

        target_directory = masternode["destination_folder"]

        use_wallet_dir = True

        results = []
        for action in actions:
            result = await any_daemon(action, connection, target_directory, masternode["wallet_directories"][0]["wallet_directory"], use_wallet_dir )
            results.append(result)
            logging.info('{} Has been successfully applied to {}'.format(action, masternode["connection_string"]))

        connection.close()
        return results
    except Exception as e:
        logging.error('Could not do_action_daemon {}'.format(masternode["connection_string"]), exc_info=e)
        return 'failed'
'''
Synchronous
''' 
def any_cli(action, connection, dir, wallet_dir="", use_wallet_dir=False):
    try:
        conx_str = '{}/polis-cli'.format(dir)
        if wallet_dir != "" and use_wallet_dir :
            conx_str += " --datadir=" + wallet_dir
        conx_str += " "+action


        result = connection.run(conx_str, hide=False)
        if result == "error: couldn't connect to server: unknown (code -1)":
            logging.info(result)
            return result
        msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
        logging.info(msg.format(result))

        return result
    except UnexpectedExit as e:
        #possibly try to start polisd
        logging.warning('{} exited unexpectedly'.format('polis-cli'), exc_info=e)
        return "UnexpectedExit"
    except Exception as e :
        logging.error('Could not getinfo: {}'.format('polis-cli'), exc_info=e)
        return "any_cli failed"
'''
async
''' 
async def any_cli_async(action, connection, dir, wallet_dir="", use_wallet_dir=False):
    try:
        conx_str = '{}/polis-cli'.format(dir)
        if wallet_dir != "" and use_wallet_dir :
            conx_str += " --datadir=" + wallet_dir
        conx_str += " "+action

        logging.info('>>> Executing command {}'.format('polis-cli'))
        result = connection.run(conx_str, hide=False)
        if result == "error: couldn't connect to server: unknown (code -1)":
            logging.warning('>>> Got result {}'.format(result))
            return result

        logging.info(">>> Succesfully executed {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}".format(result))

        return result
    except UnexpectedExit as e:
        #possibly try to start polisd
        logging.warning('{} exited unexpectedly'.format('polis-cli'), exc_info=e)
        return "UnexpectedExit"
    except Exception as e :
        logging.error('Could not getinfo: {}'.format('polis-cli'), exc_info=e)
        return "any_cli failed"
'''
asynchronous do cli action
'''
async def async_dacli(masternode,actions):
    # noinspection PyBroadException
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

        target_directory = masternode["destination_folder"]

        use_wallet_dir = True
        
        for action in actions:
            result = await any_cli_async(action, connection, target_directory, masternode["wallet_directories"][0]["wallet_directory"], use_wallet_dir )
            if result == 'UnexpectedExit':
                results = '{"status":"restart"}'
            else:
                results = result.stdout
        

        connection.close()
        logging.info('>>> Connection closed'.format(masternode["connection_string"]))
        return results
    except Exception as e:
        logging.error('Could not do_action {} : {}'.format(masternode["connection_string"], e), exc_info=e)
        return 'exception' 
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

            return "Result of running polisd {}: {} <br> <a href=/mns/cli/masternodes/status></a>".format(actions, result)
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
        
        mn_idx = request.args.get('mn')
        [result] = do_action_daemon(config['masternodes'][int(mn_idx)])
        logging.info('Executed: polisd @ {} returned: {}'.format(mn_idx, result))
        return result 

'''
REST endpoint to clean up wallet dir (rm blockchain files) start daemon with -resync
TODO:
'''


'''
Create a new MN:
Deploy a new MN based on form information, also save it to config
TODO: 
    - Form which takes: IP of new VPS, password of vps, tx output optional (eventually generate automatically here through request)
    - Runs script to update VPS, copy polis binary from local, generate priv key, install sentinel and crontab job, install sscript to watch daemon every minute and relaunch it 
'''
@app.route('/create',methods=['POST', 'GET'])
def create(request):
    if(request.method == "POST"):
        logging.info('ip = {}, password = {}, port = {}, name = {}'.format(request.args.get('ip'),
            request.args.get('password'),request.args.get('port'),request.args.get('name')))
        
        masternode = { 
            "connection_sting": "{}@{}:{}".format(request.args.get('user'), request.args.get('host'),
                request.args.get('port)')),
            "password":request.args.get('password'),
            "name":request.args.get("name") }
        
        #upload scripts to host

        try:
            polis = config["Polis"]
        

            connection = Connection(masternode["connection_string"],  connect_timeout=31, connect_kwargs=kwargs)
            
            # does all the apt get
            result = connection.put(polis["preconf"], hide=False)
            logging.info('Uploaded {}:\n {} '.format(polis["preconf"],result))
            result = connection.run("/bin/bash {}".format(polis["preconf"]),hide=False)
            logging.info('Ran {}:\n {}'.format(polis["preconf"],result))


            #get polisd from another mn if not available locally (polis.zip)
            """
            polishash = hashlib.md5(open("polis.tgz","rb").read()).hexdigest()
            if(polishash != config["polisHash"]):
                #wrong version, need to get new one from top MN
            """

            connection.put(polis["preconf"]["version_to_upload"], hide=False)
            connection.run("mkdir {} && mkdir {} && tar zxvf {} {}".format(config["WalletsFolder"], polis["default_dir"],polis["version_to_upload"],polis["default_dir"]), hide=False) 

            #second part configuration script, generates privkey and gets polisd running properly
            result = connection.put(polis["confdaemon"], hide=False)
            logging.info('Uploaded {}:\n {}'.format(polis["confdaemon"], result))
            result = connection.run("/bin/bash {}".format(polis["confdaemon"]), hide=False) 
            logging.info('Ran {}:\n {}'.format(polis["confdaemon"]), result)

            """
            extract privkey from result here, 
            save it in msaternode["masternode_private_key"]
            """
            #Setup script which watches daemon and restarts it on crash
            connection.put(polis["watcher_cron"], hide=False)
            logging.info('Uploaded {}:\n {}'.format(polis["watcher_cron"], result))
            result = connection.run("/bin/bash {}".format(polis["watcher_cron"]), hide=False) 
            logging.info('Uploaded {}:\n {}'.format(polis["watcher_cron"], result))


            #setup sentinel
            connection.put(polis["sentinel_setup"], hide=False)
            logging.info('Uploaded {}:\n {}'.format(polis["sentinel_setup"], result))
            result = connection.run("/bin/bash {}".format(polis["sentinel_setup"]), hide=False) 
            logging.info('Uploaded {}:\n {}'.format(polis["sentinel_setup"], result))

            

            config["masternodes"].append(masternode)
            with open('config.json', 'w') as outfile:
                json.dump(config, outfile)

            connection.close() 
            #save masternode to config.json.
            return result
        except UnexpectedExit as e:
            #possibly try to start polisd
            logging.warning('{} exited unexpectedly'.format('polis-cli'), exc_info=e)
            return "UnexpectedExit"
        except Exception as e :
            logging.error('Could not getinfo: {}'.format('polis-cli'), exc_info=e)
            return "any_cli failed" 

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
        file = open("config.json", "r") 
        config = json.load(file)
        error=None
        template="mnlist-jquery.html"

        preload = []
        idx=0
        for mn in config["masternodes"]: 
            preload.append({"cnx":mn["connection_string"],"idx":idx})
            idx+=1

        logging.info("Returning preloaded template for frontend {}".format(preload)) 
        return render_without_request(template, masternodes=preload)
    '''
    Nonblocking masternode status request using await
    '''
    @mns.route('/cli/masternode/status', methods=['GET'])
    async def cli_mn_status(request):
        
        mnidx = int(request.args.get(b'mnidx', [0])[0])
        action = ['masternode status']

        result = await async_dacli(config['masternodes'][mnidx],action)

        logging.info("{} no blocking masternode status requested for mn {}  ".format(action,mnidx)) 
        return result

    '''
    Asynchronously do an action part of available actions:
    actidx: the action 
    mnidx: index of the masternode
    '''
    @mns.route('/cli/action', methods=['GET'])
    async def cli_mn_action(request):
        
        mnidx = int(request.args.get(b'mnidx', [0])[0])
        actidx = request.args.get(b'actidx', ['mnstat'])[0] 
        action = {'mnsyncstat':'mnsync status','mnstat':'masternode status','gi':'getinfo','mnss':'mnsync status' }

        result = await async_dacli(config['masternodes'][mnidx],action)

        logging.info("{} no blocking masternode status requested for mn {}  ".format(action,mnidx)) 
        return result

if __name__ == '__main__':
    app.run(host=config["Listen"]["host"], port=config["Listen"]["port"])
 
