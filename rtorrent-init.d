#!/bin/sh

. /lib/lsb/init-functions

PATH=$PATH:/bin:/usr/bin:/sbin:/usr/sbin
NAME=rtorrent
PIDFILE=/var/run/$NAME.screen
CHUSER=$NAME
DAEMON=/usr/bin/rtorrent
DAEMON_ARGS="-n -o try_import=/etc/rtorrent.rc"

do_start()
{
    if [ -s $PIDFILE ] && kill -0 $(cat $PIDFILE) >/dev/null 2>&1; then
        exit 0
    fi
    log_daemon_msg "Starting" $NAME
    start-stop-daemon --start --quiet --background --pidfile $PIDFILE \
        --make-pidfile --exec /bin/su -- \
        $CHUSER -c "/usr/bin/screen -D -m -- $DAEMON $DAEMON_ARGS"
    log_end_msg 0
}

do_stop()
{
    log_daemon_msg "Stopping" $NAME
    start-stop-daemon --stop --quiet --pidfile $PIDFILE --oknodo
    log_end_msg 0
}

do_status()
{
    if [ -s $PIDFILE ] && kill -0 $(cat $PIDFILE) >/dev/null 2>&1; then
        exit 0
    else
        exit 4
    fi
}

case "$1" in
    start)
        do_start
    ;;
    stop)
        do_stop
    ;;
    restart)
        do_stop
        sleep 4
        do_start
    ;;
    status)
        do_status
esac

exit 0
