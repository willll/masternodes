import argparse
from enum import Enum

# project imports
import upgrade
import control

'''
main
'''

class MasernodeCmd(Enum):
    current = 'current'
    genkey = 'genkey'
    status = 'status'
    list = 'list'

    def __str__(self):
        return self.value


def main():
    global default_wallet_dir
    global default_wallet_conf_file

    # CLI arguments
    parser = argparse.ArgumentParser(description='Masternodes upgrade script')

    subparsers = parser.add_subparsers(description='Masternodes upgrade script', dest='command')
    parser_masternode = subparsers.add_parser('mn')
    parser_masternode.add_argument('-c', '--config', nargs='?', default="config.json", help='config file in Json format')
    parser_masternode.add_argument('-deploy', action='store_true', help='deploy a new version')
    parser_masternode.add_argument('-cleanConfig', action='store_true', help='clean up to config files')
    parser_masternode.add_argument('-addNodes', action='store_true', help='edit the config file to add addnode entries')
    parser_masternode.add_argument('-r', '--reindex', action='store_true', help='reindex the masternodes')
    parser_masternode.add_argument('-installVPS', action='store_true', help='install the VPSs')
    parser_masternode.add_argument('-installBootstrap', action='store_true', help='install the bootstrap')
    parser_masternode.add_argument('-installSentinel', action='store_true', help='install sentinel')
    parser_masternode.add_argument('-deployConfig', action='store_true', help='deploy polis.conf')
    parser_masternode.add_argument('-s', '--startDaemon', action='store_true', help='start the daemon')
    parser_masternode.add_argument('-masternodeConf', action='store_true', help='output the masternode.conf content')
    parser_masternode.add_argument('-ls', '--masternodeStatus', action='store_true', help='output the masternode status')
    parser_masternode.add_argument('-masternodeDiagnostic', action='store_true', help='output diagnostics')
    parser_masternode.add_argument('-grep', '--masternodeList', nargs='+', type=int, help='filter mastenodes by id')
    parser_masternode.add_argument('-mv', '--masternodeMove', nargs=2, type=int, help='move masternodes from one id to another')
    #parser_masternode.set_defaults(func=mn)

    parser_rpc = subparsers.add_parser('rpc')
    parser_rpc.add_argument('-c', '--config', nargs='?', default="config.json",
                                   help='config file in Json format')
    #== Wallet ==
    parser_rpc.add_argument('-lstx', action='store_true',
                            help='list inputs')
    parser_rpc.add_argument('-listunspent', action='store_true',
                                   help='list unspent')
    parser_rpc.add_argument('-listlockunspent', action='store_true',
                            help='list of temporarily unspendable outputs')
    parser_rpc.add_argument('-listaccounts', action='store_true',
                            help='Returns Object that has account names as keys, account balances as values.')
    parser_rpc.add_argument('-getbalance', action='store_true',
                            help='returns the server\'s total available balance.')
    #== Polis ==
    parser_rpc.add_argument('-get-masternode-current', action='store_true',
                            help='Print info on current masternode winner to be paid the next block (calculated locally)')
    parser_rpc.add_argument('-get-masternode-genkey', action='store_true',
                            help='Generate new masternodeprivkey')
    parser_rpc.add_argument('-get-masternode-outputs', action='store_true',
                            help='Print masternode compatible outputs')
    parser_rpc.add_argument('-masternode-start-alias', action='store_true',
                            help='Start single remote masternode by assigned alias configured in masternode.conf')
    #parser_rpc.add_argument('-masternode-start-<mode> ', action='store_true',
    #                        help='Start remote masternodes configured in masternode.conf (<mode>: 'all', 'missing', 'disabled')')
    parser_rpc.add_argument('-get-masternode-status', action='store_true',
                            help='Print masternode status information')
    parser_rpc.add_argument('-get-masternode-list', action='store_true',
                            help='Print list of all known masternodes (see masternodelist for more info)')
    parser_rpc.add_argument('-get-masternode-winner', action='store_true',
                            help='Print info on next masternode winner to vote for')
    parser_rpc.add_argument('-get-masternode-winners', action='store_true',
                            help='Print list of masternode winners')
    parser_rpc.add_argument('-masternode', nargs=1, type=MasernodeCmd, choices=list(MasernodeCmd),
                            help='masternode command')



    args = parser.parse_args()

    if args.command == 'mn':
        upgrade.masternode(args)
    elif args.command == 'rpc':
        control.rpc_control(args)


if __name__ == '__main__':
    main()