from slickrpc import Proxy; 
from time import sleep

p = Proxy(service_url='http://poliscoreuser:fklafkldsjkllkfjajkfdsajlfsddafsfafsdsadffds@127.0.0.1:24127');

#print(p.masternode("outputs"))

def get_collat(p, unspent, pw):
    '''
    take a list of unspent outputs and return a list of 
    tx to make at least 1 collateral sized output
    If it's not possible return empty list
    '''
    p.walletpassphrase(pw, 1) 
    inputs = []
    total = 0
    keychain = []
    keys = []
    for u in unspent:
        inputs.append({'txid':u['txid'], 'vout':u['vout']})
        total += u['amount']
        privkey = p.dumpprivkey(r['address'])
        keychain.append(privkey) 
        if privkey in keys:
            keys[privkey] += 1
        else:
            keys[privkey] = 1

        if collat > MN_COLLAT:
            return [inputs, keychain]
    return []

def prepare_tx (p, output_address, address, qty, inputs, fee, keychain):
    '''
    send tx

    address = "PR85hfZMxU7i58gkTBADVAdsiPxsb4JDZh"
    '''
    change = total - qty- fee
    outputs ={ results[0]['address'] : COLATMN, address : change}
    print( outputs)

    tx = p.createrawtransaction(inputs, outputs)
    print(tx)

    decoded = p.decoderawtransaction(tx)
    print(decoded) 

    print(keychain)
    signed = p.signrawtransaction(tx, inputs, keychain)
    print(signed)

def create_mn_output():
    '''
    call get_collat, tend send TX, get the resulting output
    call masternode privkey to generate private key
    retrn line for use in masternode.conf

    '''

    password = "PASSSWORD for encrypted wallet"

    output_address = p.getnewaddress()


    MN_COLLAT = 1000
    fee = 0.001
    #check if theres already mn capable unspent output
    [inputs,keychain] = p.listunspent()

    '''
    Get inputs from this function, then create the tx with  
    then send it here.
    '''

    get_collat(p,unspent,password)
    prepare_tx(p,output_address,address,MN_COLLAT,inputs,fee,keychain)

#to be continued
    send_tx.....

    '''
    scrap code...
    '''
    txs = p.listtransactions()
    print("List transactions:")
    for tx in txs:
        print(f"{tx['amount']} polis : {tx['confirmations']} confirmations")
    print(f"Got {len(unspent)} unspent outputs: ")

    return
balance = 0 
possible_mn = 0
for u in unspent:
    balance += u['amount']
    print(f"Unlocked unspent: {u['amount']}")
    if u['amount'] == MN_COLLAT:
        print(f"Already have output: {u['txid']} {u['vout']}")
    if balance > MN_COLLAT:
        possible_mn += 1

print ( f"Got balance: {balance}")
print ( f"Total possible MN: {possible_mn}")
print ( p.getstakingstatus())
exit(1)
if balance > MN_COLLAT:
    print("Enough unspent tx for new mn")
    print("Creating unspent mn output ")
    mn_address = p.getnewaddress()
    print(f"Got address: {mn_address}")

    pw = ''
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


exit


results =  p.listunspent()
#print(results)
#{'txid': '1c2725d0ea138f31a2437b5ec11c93c2d83ea6c8d30da3823e21c1f02ad184fe', 'vout': 2, 'address': 'PQCuVujf3TYJJdDTmxb8xMeDnCTH4CrmVP', 'account': 'mn10b', 'scriptPubKey': '76a914ab4bcacd306ccd1f149f05ad96085d3c23b028dc88ac', 'amount': 14.4, 'confirmations': 13150, 'spendable': True, 'solvable': True, 'ps_rounds': -2}


'''
list of addresses to send coins to:
    - first is the new mn address,
    - second is change, freshly created 
'''

COLATMN = 1000
total =0
inputs = []
keychain= []

pw = '<CHANGE-Walletpassword>'
p.walletpassphrase(pw, 1)
keys= {}
for r in results:
    if total < COLATMN:
        inputs.append({'txid':r['txid'], 'vout':r['vout']})
        total += r['amount']
        privkey = p.dumpprivkey(r['address'])
        keychain.append(privkey)
        if privkey in keys:
            keys[privkey] += 1
        else:
            keys[privkey] = 1


print(keys)
print (total)

address = "PR85hfZMxU7i58gkTBADVAdsiPxsb4JDZh"
FEE=0.001
outputs ={ results[0]['address'] : COLATMN, address : total-COLATMN-FEE }
print( outputs)



tx = p.createrawtransaction(inputs, outputs)
print(tx)

decoded = p.decoderawtransaction(tx)
print(decoded)


print(keychain)
signed = p.signrawtransaction(tx, inputs, keychain)
print(signed)
'''



