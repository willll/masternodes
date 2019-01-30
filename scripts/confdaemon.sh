#!/usr/bin/env bash

COIN=$1
ADD_NODES=$2
COIN_DIR=$3
MY_IP=$4
PASSWORD=$6
DAEMON=${COIN_DIR}/${COIN}d
CLI=${COIN_DIR}/${COIN}-cli
WALLET_DIR=${COIN_DIR}/.wallet/
CONFIG=${COIN_DIR}${COIN}.conf

mkdir ${COIN_DIR}
mkdir ${WALLET_DIR}
echo -e "rpcuser=supercoinuser\nrpcpassword=${PASSWORD}\nlisten=1\nmaxconnections=256\nexternalip=${MY_IP}\n" > ${CONFIG}
echo -e "${ADD_NODES}" >> ${CONFIG}
cd ${COIN_DIR}
${DAEMON} -daemon -datadir="${WALLET_DIR}"
sleep 5
masternodekey=$(${CLI} -datadir=${WALLET_DIR} masternode genkey)
${CLI} -datadir="${WALLET_DIR}" stop
sleep 5
echo -e "masternode=1\ndaemon=1\nmasternodeprivkey=${masternodekey}" >> ${CONFIG}
${DAEMON}
echo ${masternodekey}
