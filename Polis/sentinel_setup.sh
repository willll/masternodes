#!/bin/bash

#Sentinel setup
#weird bug didnt allow virtualenv venv to work without doing following command:
# arguments:  1: https://github.com/polispay/sentinel.git  2: COINDIR 3: COIN
#
SENTINEL_GIT = $1
COINDIR = $2
COIN = $3

export LC_ALL=C
############
cd $COINDIR
sudo git clone $SENTINEL_GIT
cd sentinel
sudo apt-get install -y virtualenv
virtualenv venv
venv/bin/pip install -r requirements.txt
echo $COIN\_conf=$COINDIR/.wallet/$COIN.conf >> $COINDIR/sentinel/sentinel.conf
crontab -l > tempcron
echo "* * * * * cd $COINDIR/sentinel && ./venv/bin/python bin/sentinel.py 2>&1 >> sentinel-cron.log" >> tempcron
crontab tempcron
rm tempcron
echo "source ~/.bash_aliases"
