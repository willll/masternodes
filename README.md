# Masternodes
masternodes toolbox, bleh bleh bleh

* main.py : website ...

* Polis/upgrade.py : ...

# How to :

sudo apt install python3-venv

python3 -m venv .

source bin/activate

sudo pip3 install -r requirements.txt

# How to dump memcache keys :

memcdump --servers=localhost


# VirtualBox portforwarding: 

setup new host adapter in virtualbox, then add adapter to adapter 2 in the VM

from the VM deteermine the host IP, add it to rpcallowip and then connect to the VM
from the host.
