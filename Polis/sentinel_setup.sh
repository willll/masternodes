#!/bin/bash

#Sentinel setup
#weird bug didnt allow virtualenv venv to work without doing following command:
export LC_ALL=C
############
cd $COINDIR
sudo git clone https://github.com/polispay/sentinel.git
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
echo "Job completed successfully, Masternode private key: mn ${MY_IP}:24126 $masternodekey"
