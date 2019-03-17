from slickrpc import Proxy


# https://en.bitcoin.it/wiki/Original_Bitcoin_client/API_calls_list

class RPC:
    def __init__(self, username, password, ip, port=24127):
        self.proxy = Proxy(service_url="http://{}:{}@{}:{}".format(username, password, ip, port))


    def listunspent(self):
        return self.proxy.listunspent()

    def listlockunspent(self):
        return self.proxy.listlockunspent()

    def listaccounts(self):

    def listtransactions(self):
        return self.proxy.listtransactions()


    def getstakingstatus(self):
        return self.proxy.getstakingstatus()

    def getbalance(self):
        return self.proxy.getbalance()


    def getnewaddress(self):
        return self.proxy.getnewaddress()


    def walletpassphrase(self, pw):
        return self.proxy.walletpassphrase(pw, 1)


    def sendtoaddress(self, address, send):
        return self.proxy.sendtoaddress(address, send)



    '''
    
    from slickrpc import Proxy;
from time import sleep

p = Proxy(service_url='http://poliscoreuser:fklafdd@127.0.0.1:24127');

#print(p.masternode("outputs"))

MN_COLLAT = 1000
#check if theres already mn capable unspent output
unspent = p.listunspent()
txs = p.listtransactions()
for tx in txs:
    print(f"{tx['amount']} polis : {tx['confirmations']} confirmations")
print(f"Got {len(unspent)} unspent outputs")
balance = 0
for u in unspent:
    balance += u['amount']
    print(u['amount'])
    if u['amount'] == MN_COLLAT:
        print(f"Already have output: {u['txid']} {u['vout']}")
        exit(1)
    if balance > MN_COLLAT:
        break
print ( f"Got balance: {balance}")
print ( p.getstakingstatus())
exit(1)
if balance > MN_COLLAT:
    print("Enough unspent tx for new mn")
    print("Creating unspent mn output ")
    mn_address = p.getnewaddress()
    print(f"Got address: {mn_address}")

    pw = 'fsfs'
    p.walletpassphrase(pw, 1)
    txid = p.sendtoaddress(mn_address, MN_COLLAT)
    txconf = 0
    while txconf == False:
        unspent = p.listunspent()
        for o in unspent :
            if o['txid'] ==txid:
                print(f"{o['txid']} {o['vout']}")
                txconf = True
        print("Waiting for tx broadcast...\r")
        sleep(10)
        
    '''