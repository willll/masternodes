#!/bin/bash
#setup polis watcher cron job

COIN=$1
COINDIR=$2
DAEMON=$3
WALLET_DIR=$4

crontab -l > tempcron
cat <<EOF > /root/${COIN}chk.sh
#!/bin/bash
if (( \$(ps -ef | grep -v grep | grep $DAEMON | wc -l) > 0 ))
then
echo "$COIN is running!!!"
else
echo "$DAEMON not found in ps, restarting"
ps -ef >> /root/${COIN}_restart.log
$COINDIR/$DAEMON -datadir=$WALLET_DIR
fi
EOF
chmod 755 /root/${COIN}chk.sh
echo "* * * * * /bin/sh /root/${COIN}chk.sh >/dev/null 2>&1" >> tempcron
crontab tempcron
rm tempcron
