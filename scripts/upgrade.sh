#!/bin/bash

CLI=$1
COIN_DIR="$2/"
DAEMON=$3
WALLET_DIR=$4
ADD_NODE=$5
CRON_BACKUP=/tmp/temp_cron

echo $COIN_DIR
crontab -l > ${CRON_BACKUP}
crontab -r
${COIN_DIR}${CLI} -datadir=${WALLET_DIR} stop
sleep 20
tar zxvf polis.tgz -C ${COIN_DIR}
sed -i '/^addnode/d' ${WALLET_DIR}/polis.conf
echo $ADD_NODE >> ${WALLET_DIR}/polis.conf
rm -rf ${WALLET_DIR}/{blocks,peers.dat,chainstate,mempool.dat,mncache.dat,fee_estimate.dat}
${COIN_DIR}${DAEMON} -datadir=${WALLET_DIR} -daemon -reindex
sleep 5
crontab ${CRON_BACKUP}

