from flask import Flask, request
import time
import sys
import json
import logging
from fabric import Connection
from invoke.exceptions import UnexpectedExit

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route('/abc')
def show_config():
    return 'Hello, World!'

def any_cli(action, connection, dir, wallet_dir="", use_wallet_dir=False):
    try:
        conx_str = '{}/polis-cli'.format(dir)
        if wallet_dir != "" and use_wallet_dir :
            conx_str += " --datadir=" + wallet_dir
        conx_str += " "+action

        result = connection.run(conx_str, hide=False)
        msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
        logging.info(msg.format(result))

        return result
    except Exception as e :
        logging.error('Could not getinfo  : {}'.format('polis-cli'), exc_info=e)
        return "failed"
'''



''' 
def do_action(cnx, action):
    # noinspection PyBroadException
    try:
        kwargs = {}
        if "connection_certificate" in cnx :
            kwargs['key_filename'] = cnx["connection_certificate"]
        else :
            # Must be mutually excluded
            if "connection_password" in cnx:
                kwargs['password'] = cnx["connection_password"]

        connection = Connection(cnx["connection_string"], connect_timeout=30, connect_kwargs=kwargs)

        target_directory = cnx["destination_folder"]

        use_wallet_dir = True
        
        result = any_cli(action, connection, target_directory, cnx["wallet_directories"][0]["wallet_directory"], use_wallet_dir )

        logging.info('{} Has been  successfully upgraded'.format(cnx["connection_string"]))
        return result
    except Exception as e:
        logging.error('Could not upgrade {}'.format(cnx["connection_string"]), exc_info=e)
        return 'failed'

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
        action = request.form['action'] or 'getinfo'
        result = "<p>"
        for idx in mns: 
            #blocking do action until complete...
            result += str(do_action(config['masternodes'][int(idx)], action))
        result += "</p>"

        return result 

    else:
        mnlist = "<form method='POST'>\n<select name=mns multiple>\n"
        idx = 0 
        for cnx in config["masternodes"]: 
            mnlist += "\t<option value='" + str(idx)+ "'>"+ cnx['connection_string']+"</option>\n"
            idx+=1

        mnlist += "</select>\n"
        action = "<select name=action>\n"
        action += "\t<option value=getinfo>getinfo</option>\n"
        action += "\t<option value='masternode status'>masternode status</option>\n"
        action += "</select>"
        return mnlist+action+ "<p><input type=submit value=submit></form>" 
