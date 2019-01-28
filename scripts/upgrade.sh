#!/usr/bin/env bash

CLI=$1
COINDIR=$2
DAEMON=$3
WALLET_DIR=$4
CRONBACKUP=/tmp/temp_cron

crontab -l >  $CRONBACKUP
crontab -r
$CLI --datadir=$WALLET_DIR stop
sleep 20
tar zxvf polis.tgz $COINDIR
rm -rf $WALLET_DIR/{blocks,peers.dat,chainstate,mempool.dat,mncache.dat,fee_estimate.dat}
$DAEMON --datadir=$WALLET_DIR -daemon -reindex
sleep 5
crontab $CRONBACKUP


