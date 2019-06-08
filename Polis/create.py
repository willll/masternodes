from slickrpc import Proxy
from slickrpc.exc import RpcException

proxy = Proxy(service_url='http://poliscoreuser:@192.168.56.101:24127')

'''
# Load configuration file
file = open(args.config)
config = json.load(file)
file.close()

rpc = RPC(config["Polis"]["wallet"]["username"],
          config["Polis"]["wallet"]["password"],
          config["Polis"]["wallet"]["ip"],
          config["Polis"]["wallet"]["port"])
'''
MN_COLLAT = 1000
def get_collat(p, unspent, pw):
    '''
    take a list of unspent outputs and return a list of
    tx to make at least 1 collateral sized output
    If it's not possible return empty list
    '''
    p.walletpassphrase(pw, 10)

    inputs = []
    total = 0
    keychain = []

    keys = {}

    for u in unspent:
        inputs.append({'txid': u['txid'], 'vout': u['vout']})
        total += u['amount']
        two_fa =''
        privkey = ''
        try:
            privkey = p.dumpprivkey(u['address'])
        except RpcException as e:
            """WARNING! Your one time authorization code is: dJ7W
This command exports your wallet private key. Anyone with this key has complete control over your funds. 
If someone asked you to type in this command, chances are they want to steal your coins. 
Polis team members will never ask for this command's output and it is not needed for masternode setup or diagnosis!

 Please seek help on one of our public channels. 
 Telegram: https://t.me/PolisPayOfficial
 Discord: https://discord.gg/FgfC53V
 Reddit: https://www.reddit.com/r/PolisBlockChain/
            """
            two_fa = e.message.splitlines()[0].split(': ')[1]
            privkey = p.dumpprivkey( u['address'], two_fa)

        print(f"{privkey}")
        keychain.append(privkey)

        if privkey in keys:
            keys[privkey] += 1
        else:
            keys[privkey] = 1

        if total > MN_COLLAT:
            return [inputs, keychain, keys, total]

    return []


def prepare_raw_tx(p, mn_address, change_address, qty, inputs, fee,  total):
    '''
    Create and sign a transaction to be broadcast,
    this is used to create a masternode output tx
    for example

    '''
    change = total - qty - fee
    outputs ={mn_address: qty, change_address: change}

    #inputs prepared by get_collat should work
    tx = p.createrawtransaction(inputs, outputs)

    return tx



def get_empty_addresses(p, amt):
    '''
    get empty addresses available or return
    an array with #(amt) getnewaddress

    :param amt the amount of empty addresses
    '''

    empty = []
    for group in p.listaddressgroupings():
        for i in group:
            if i[1] == 0:
                empty.append(i[0])
                if len(empty) >= amt:
                    return empty

    while len(empty) < amt:
        empty.append(p.getnewaddress())

    return empty


pw = '<FILL IN WITH PASSWORD !!!>'
lu = proxy.listunspent()

fee_max = 0.0001
'''
change_debug_address = "PGeBt6MhaqPyEP5pwv5Ezc6EKQB8Cmt5pV"
mn_debug_address = "PD1yW8b8A9LA5UfTpj8svEBHetMWEwoNYb"
'''

[inputs, keychain, keys, total] = get_collat(proxy, lu, pw)
print(f"got inputs: {inputs} and keychain: {keychain}")

[change_debug_address, mn_debug_address] = get_empty_addresses(proxy, 2)

tx = prepare_raw_tx(proxy, mn_debug_address, change_debug_address, MN_COLLAT, inputs, fee_max, total)

#not used (maybe for debug)
decoded = proxy.decoderawtransaction(tx)

'''
this part could be done on a separate "cold storage" machine with the priovate keys/ keychain
it uses keys from keychain to sign the tx 
https://bitcoin.org/en/developer-examples#complex-raw-transaction


We sign multiple times if there are several UTXOs in the input, once completely signed result
should be "complete=true", signrawtransaction does this automatically when given an array of privatekeys
the second param should be previous dependant tx for some reason it works with null.
'''
signed = proxy.signrawtransaction(tx, [], keychain)
print(f"Decoded raw transaction : {decoded}\n signed: {signed}")


'''
at this point it just needs to be broadcast
with proxy.sendrawtransaction ( signed.hex )
'''


