#!/bin/bash
sudo DEBIAN_FRONTEND=noninteractive apt update -yq
sudo DEBIAN_FRONTEND=noninteractive apt upgrade -yq
sudo DEBIAN_FRONTEND=noninteractive apt install build-essential git vim screen curl libtool libzmq-dev libminiupnpc-dev  autotools-dev automake pkg-config libssl-dev libevent-dev bsdmainutils  libboost-system-dev libboost-filesystem-dev libboost-chrono-dev libboost-program-options-dev libboost-test-dev libboost-thread-dev libboost-all-dev software-properties-common -yq 
sudo DEBIAN_FRONTEND=noninteractive add-apt-repository ppa:bitcoin/bitcoin -y
sudo DEBIAN_FRONTEND=noninteractive apt-get update -yq
sudo DEBIAN_FRONTEND=noninteractive apt-get install libdb4.8-dev libdb4.8++-dev -yq
