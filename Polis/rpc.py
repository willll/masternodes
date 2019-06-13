from slickrpc import Proxy

# https://en.bitcoin.it/wiki/Original_Bitcoin_client/API_calls_list


class RPC:
    def __init__(self, username, password, ip, port=24127):
        self.proxy = Proxy(service_url=f"http://{username}:{password}@{ip}:{port}")

    # == Wallet ==
    # -- list --

    def listunspent(self):
        return self.proxy.listunspent()

    def listlockunspent(self):
        return self.proxy.listlockunspent()

    def listaccounts(self):
        return self.proxy.listaccounts()

    def listtransactions(self):
        return self.proxy.listtransactions()

    def listaddressgroupings(self):
        return self.proxy.listaddressgroupings()

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

    def dumpprivkey(self, address, two_fa=''):
        return self.proxy.dumpprivkey(address, two_fa)

    def createrawtransaction(self, inputs, outputs):
        return self.proxy.createrawtransaction(inputs, outputs)

    def decoderawtransaction(self, tx):
        return self.proxy.decoderawtransaction(tx)

    def signrawtransaction(self, tx, previous_tx, keychain):
        return self.proxy.signrawtransaction(tx, previous_tx, keychain)

    def sendrawtransaction(self, signedTx):
        return self.proxy.sendrawtransaction(signedTx)

    def lockunspent(self, lock, tx):
        return self.proxy.lockunspent(lock, tx)

    # == Polis ==

    def getMasternode(self, arg):
        return self.proxy.masternode(arg)

    def masternodelist(self, mode, filter):
        return self.proxy.masternodelist(mode, filter)

    def masternodebroadcast(self, command):
        return self.proxy.masternodebroadcast(command)
