'''
TODO: setup a websocket channel to talk to the front end
TODO: receive config for creation of new mn
TODO: action to delete old block chain cache, and cache .dat files
TODO: display config for one MN, and allow saving it too: with password, or certificat
TODO: test new MN creation
TODO: use ListBox on left side with list of IPs, should be searchable/filterable and can select multiple IPs
    with checkbox
TODO: Display information fromt he block explorer about block # and other relevant
TODO: Des checkbox pour sélectionner les mn en groupe
TODO: Une barre d'actions en haut pour appliquer aux mn sélectionné
TODO: un évent pour refesh la page aux 5 min
TODO: masternode start from this script (via RPC)
TODO: Enable multi threading or non blocking of requests/responses,
    - WSGI, gunicorn, multiprocessing (python),
    - https://stackoverflow.com/questions/40912982/how-can-my-twisted-klein-app-listen-on-multiple-ports

DONE:
'''


from rest import app, wsResource, factory
from config import config


if __name__ == '__main__':
    app.run(host=config["Listen"]["host"], port=config["Listen"]["port"])




