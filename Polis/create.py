from slickrpc.exc import RpcException
import json
from rpc import RPC


class Create:
    """
    create a new masternode output
    """

    def __init__(self, config_file,  MN_COLLAT= 1000, pw = ''):
        # Load configuration file
        file = open(config_file)
        config = json.load(file)
        file.close()

        self.rpc = RPC(config["Polis"]["wallet"]["username"],
                  config["Polis"]["wallet"]["password"],
                  config["Polis"]["wallet"]["ip"],
                  config["Polis"]["wallet"]["port"])

        self.MN_COLLAT = MN_COLLAT

        self.rpc.walletpassphrase(pw)

    def get_collat(self, unspent):
        """
        take a list of unspent outputs and return a list of tx to make at least 1 collateral sized output
        If it"s not possible return empty list
        """

        inputs = []
        total = 0
        keychain = []

        keys = {}

        for u in unspent:
            inputs.append({'txid': u['txid'], 'vout': u['vout']})
            total += u['amount']
            privkey = ''
            try:
                privkey = self.rpc.dumpprivkey(u['address'])
            except RpcException as e:
                """
                WARNING! Your one time authorization code is: dJ7W
                    This command exports your wallet private key. Anyone with this key has complete control over your funds. 
                    If someone asked you to type in this command, chances are they want to steal your coins. 
                    Polis team members will never ask for this command's output and it is not needed for masternode setup or diagnosis!

                     Please seek help on one of our public channels. 
                     Telegram: https://t.me/PolisPayOfficial
                     Discord: https://discord.gg/FgfC53V
                     Reddit: https://www.reddit.com/r/PolisBlockChain/
                """
                two_fa = e.message.splitlines()[0].split(': ')[1]
                privkey = self.rpc.dumpprivkey(u['address'], two_fa)

            print(f"{privkey}")
            keychain.append(privkey)

            if privkey in keys:
                keys[privkey] += 1
            else:
                keys[privkey] = 1

            if total > self.MN_COLLAT:
                return [inputs, keychain, keys, total]

        return []

    def prepare_raw_tx(self, mn_address, change_address, inputs, total, qty=1000, fee=0.00001):
        """
        Create and sign a transaction to be broadcast,
        this is used to create a masternode output tx
        for example
        """
        return self.rpc.createrawtransaction(inputs, {mn_address: qty, change_address: total - qty - fee})

    def get_empty_addresses(self, amt):
        """
        get empty addresses available or return
        an array with #(amt) getnewaddress

        :param amt the amount of empty addresses
        """

        empty = []
        for group in self.rpc.listaddressgroupings():
            for i in group:
                if i[1] == 0:
                    empty.append(i[0])
                    if len(empty) >= amt:
                        return empty

        while len(empty) < amt:
            empty.append(self.rpc.getnewaddress())

        return empty




