#setup polis watcher cron job
crontab -l > tempcron
cat <<EOF > /root/polischk.sh
#!/bin/bash
if (( $(ps -ef | grep -v grep | grep polisd | wc -l) > 0 ))
then
echo "$service is running!!!"
else
/root/wallets/polis/polisd -datadir=/root/wallets/polis/.wallet
fi
EOF
chmod 755 /root/polischk.sh
echo "* * * * * /bin/sh /root/polischk.sh >/dev/null 2>&1" >> tempcron
crontab tempcron
rm tempcron
