from flask import Flask, request, render_template
import time
import sys
import json
import logging
from fabric import Connection
from invoke.exceptions import UnexpectedExit

app = Flask(__name__)

'''

''' 
@app.route('/')
def hello_world():
    return 'Hello, World!'
'''

''' 
def rpc_cli(action, connection, dir, wallet_dir="", use_wallet_dir=False):
    return

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
def do_action_daemon(cnx, actions):
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
        

        if len(actions) == 0 :
            actions=['--daemon']
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
''' 
@app.route('/startpolis', methods=['GET', 'POST'])
def start_polisd():
    if len(sys.argv) > 2:
        file = open(sys.argv[1], "r")
    else:
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
                result += "<p>"+str(r) +"</o>\n"
                
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
        return "Unexpected exit of polis-cli <a href='/startpolis'>start polis</a>"
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

        connection = Connection(cnx["connection_string"],  connect_timeout=30, connect_kwargs=kwargs)

        target_directory = cnx["destination_folder"]

        use_wallet_dir = True
        
        results = []
        for action in actions:
            result = any_cli(action, connection, target_directory, cnx["wallet_directories"][0]["wallet_directory"], use_wallet_dir )
            results.append(result.stdout)
        

        connection.close()
        logging.info('{} Has been  successfully upgraded'.format(cnx["connection_string"]))
        return results
    except Exception as e:
        logging.error('Could not do_action {} : {}'.format(cnx["connection_string"], e), exc_info=e)
        return 'exception'

'''
''' 
@app.route('/listmn', methods=['GET'])
def listmn(template='mnlist.html', actions = ['getinfo']): 
    if len(sys.argv) > 2:
        file = open(sys.argv[1], "r")
    else:
        file = open("config.json", "r") 
    config = json.load(file)
    error = None 

    actions = ["masternode status", "getinfo", "mnsync status"]
    result=[]
    for cnx in config["masternodes"]: 
        result.append(do_action_cli(cnx,actions))

    return render_template(template, masternodes=result)

'''

''' 
@app.route('/action', methods=['POST', 'GET'])
def action():

    if len(sys.argv) > 2:
        file = open(sys.argv[1], "r")
    else:
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
