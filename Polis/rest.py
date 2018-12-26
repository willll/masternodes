import time
import sys
import json
import logging
from fabric import Connection
from invoke.exceptions import UnexpectedExit
from klein import Klein
import requests 
from twisted.web.template import Element, renderer, XMLFile
from twisted.python.filepath import FilePath
import jinja2

app = Klein()
logging.basicConfig(
    filename = "debug_rest_py.log",
    filemode="w",
    level = logging.INFO)

'''

''' 
@app.route('/')
def hello_world(request):
    return 'Hello, World!'
'''
Temporary fix for templating
''' 
import jinja2

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
def any_daemon(action, connection, dir, wallet_dir="", use_wallet_dir=False):
    try:
        conx_str = '{}/polisd'.format(dir)
        if wallet_dir != "" and use_wallet_dir :
            conx_str += " --datadir=" + wallet_dir
        conx_str += " "+action

        result = connection.run(conx_str, hide=False)
        msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
        logging.info(msg.format(result))

        return result
    except Exception as e :
        logging.error('Could not getinfo  : {}'.format('polisd'), exc_info=e)
        return "failed"

'''

this can be used to restart daemon if getinfo isnt responding, and mn is down likely because it crashed
'''
def do_action_daemon(cnx, actions = ['--daemon']):
    try:
        kwargs = {}
        if "connection_certificate" in cnx :
            kwargs['key_filename'] = cnx["connection_certificate"]
        else :
            # Must be mutually excluded
            if "password" in cnx:
                kwargs['password'] = cnx["password"]

        connection = Connection(cnx["connection_string"],  connect_timeout=30, connect_kwargs=kwargs)

        target_directory = cnx["destination_folder"]

        use_wallet_dir = True

        results = []
        for action in actions:
            result = any_daemon(action, connection, target_directory, cnx["wallet_directories"][0]["wallet_directory"], use_wallet_dir )
            results.append(result)
            logging.info('{} Has been successfully applied to {}'.format(action, cnx["connection_string"]))

        connection.close()
        return results
    except Exception as e:
        logging.error('Could not do_action_daemon {}'.format(cnx["connection_string"]), exc_info=e)
        return 'failed'
'''
Offers a page with all mns and possibility to restart one by selecting
'''
@app.route('/startpolis', methods=['GET', 'POST'])
def start_polisd(request):
    file = open("config.json", "r") 
    config = json.load(file)
    error=None

    if request.method == 'POST':
        mns = request.form.getlist('mns')
        actions = request.form.getlist('params')
        result='Attempted starting: '+', '.join(mns)
        for idx in mns: 
            address = config['masternodes'][int(idx)]
            result = "<p>Masternode: "+str(address)+"</p>"
            for r in do_action_daemon(address, actions):
                result += "<p>"+str(r) +"</p>\n"
                
        logging.info('finished looping') 
        return result+" <a href=/listmn>List MN</a>"
    else:
        #diisplay list of all MNs with "start" button
        mnlist = "<form method='POST'>\n<select name=mns multiple>\n"
        idx = 0 
        for cnx in config["masternodes"]: 
            mnlist += "\t<option value='" + str(idx)+ "'>"+ cnx['connection_string']+"</option>\n"
            idx+=1

        mnlist += "</select>\n"
        return mnlist+ "<p><input type=submit value=start></form>" 

'''
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
''' 
def do_action_cli(cnx, actions):
    # noinspection PyBroadException
    try:
        kwargs = {}
        if "connection_certificate" in cnx :
            kwargs['key_filename'] = cnx["connection_certificate"]
        else :
            # Must be mutually excluded
            if "password" in cnx:
                kwargs['password'] = cnx["password"]

        connection = Connection(cnx["connection_string"],  connect_timeout=31, connect_kwargs=kwargs)

        target_directory = cnx["destination_folder"]

        use_wallet_dir = True
        
        results = []
        for action in actions:
            result = any_cli(action, connection, target_directory, cnx["wallet_directories"][0]["wallet_directory"], use_wallet_dir )
            if result != 'UnexpectedExit':
                results.append(result.stdout)
            else:
                results.append('{"status":"restart"}')
        

        connection.close()
        logging.info('{} Has been  successfully upgraded'.format(cnx["connection_string"]))
        return results
    except Exception as e:
        logging.error('Could not do_action {} : {}'.format(cnx["connection_string"], e), exc_info=e)
        return 'exception'

'''
list all mns, this is not so good because it's blocking and waits to get everything
''' 
@app.route('/listmn',methods=['GET'])
def listmn(request): 
    file = open("config.json", "r") 
    config = json.load(file)
    error = None 

    actions = ["masternode status", "getinfo", "mnsync status"]
    result=[]
    for cnx in config["masternodes"]: 
        result.append(do_action_cli(cnx,actions))

    return render_without_request(template, masternodes=result)
'''
Endpoint for getinfo on specific mn
'''
@app.route('/cli/getinfo', methods=[])
def cli_getinfo(request):
    file = open("config.json", "r") 
    config = json.load(file) 
    
    mn_idx = request.args.get('mn')
    action = ['getinfo']
    result = do_action_cli(config['masternodes'][mn_idx],action)

    logging.info("{} requested for mn {} returning {}".format(actions,mnidx,result)) 
    return result 
'''
Endpoint for mnsync staus on specific mn
'''
@app.route('/cli/mnsync/status', methods=['GET'])
def cli_mnsync_status(request):
    file = open("config.json", "r") 
    config = json.load(file) 
    
    mn_idx = request.args.get('mn')
    action = ['mnsync status']
    result = do_action_cli(config['masternodes'][mn_idx],action)

    logging.info("{} requested for mn {} returning {}".format(actions,mnidx,result)) 
    return result 
'''
REST endpoint to launch polisd on given server
TODO:
    It would be useful to have some feedback to the front end as to the status
    maybe a websocket update of getinfo and mnsync status.
''' 
@app.route('/daemon/launch', methods=['GET'])
def daemon_masternode_start(request):
    file = open("config.json", "r") 
    config = json.load(file) 
    
    mn_idx = request.args.get('mn')
    [result] = do_action_daemon(config['masternodes'][int(mn_idx)])
    logging.info('Executed: polisd @ {} returned: {}'.format(mn_idx, result))
    return result 
'''
returns rendered list of masternodes (mnlist-jquery.html), with a list of masternodes to preload into DOM
TODO: change config format to  IP:{...information about masternode..}
'''
@app.route('/masternodes', methods=['GET'])
def masternodes(request):
    file = open("config.json", "r") 
    config = json.load(file)
    error = None 
    template="mnlist-jquery.html"

    preload = []
    idx=0
    for mn in config["masternodes"]: 
        preload.append({"cnx":mn["connection_string"],"idx":idx})
        idx+=1

    logging.info("Returning preloaded template for frontend") 
    return render_without_request(template, masternodes=preload)
'''
returns json of masternode status request to provided mn
''' 
@app.route('/cli/masternode/status', methods=['GET'])
def mnstatus(request): 
    file = open("config.json", "r") 
    config = json.load(file)
    error = None 

    #sometimes gets Nonetype. 
    mnidx = request.args.get('mnidx') or 0 
    
    actions = ["masternode status"]
    result = ''
    [result] = do_action_cli(config["masternodes"][int(mnidx)],actions)

    logging.info("{} requested for mn {} returning {}".format(actions,mnidx,result)) 
    return result 
'''
Remove unnecessary
'''
@app.route('/action', methods=['POST', 'GET'])
def action(request):

    file = open("config.json", "r") 
    config = json.load(file)
    error = None 

    if request.method == 'POST':
        mns = request.form.getlist('mns')
        actions = request.form.getlist('actions') or ['getinfo']
        result=''
        for idx in mns: 
            #blocking do action until complete...
            address = config['masternodes'][int(idx)]
            result = "<p>Masternode: "+str(address)+"</p>"
            for r in do_action_cli(address, actions):
                result += "<p>"+str(r) +"</o>\n"

        return result 

    else:
        mnlist = "<form method='POST'>\n<select name=mns multiple>\n"
        idx = 0 
        for cnx in config["masternodes"]: 
            mnlist += "\t<option value='" + str(idx)+ "'>"+ cnx['connection_string']+"</option>\n"
            idx+=1

        mnlist += "</select>\n"
        action = "<select name=actions multiple>\n"
        action += "\t<option value='getinfo'>getinfo</option>\n"
        action += "\t<option value='masternode status'>masternode status</option>\n"
        action += "\t<option value='mnsync status'>mnsync status</option>\n"
        action += "</select>"
        return mnlist+action+ "<p><input type=submit value=submit></form>" 


 
if __name__ == "__main__":
    app.run("localhost", 5000)
