#!/bin/bash
### BEGIN INIT INFO
# Provides:          skeleton
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: LOL lolfly init.d script
# Description:       Symlink this file to /etc/init.d
### END INIT INFO

# --------------------------------------------------------------------------------------------
# Copyright (c) 2012 Lolapps, Inc.. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are
# permitted provided that the following conditions are met:
#
#    1. Redistributions of source code must retain the above copyright notice, this list of
#       conditions and the following disclaimer.
#
#    2. Redistributions in binary form must reproduce the above copyright notice, this list
#       of conditions and the following disclaimer in the documentation and/or other materials
#       provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY LOLAPPS, INC. ''AS IS'' AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL JAMES YATES FARRIMOND OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are those of the
# authors and should not be interpreted as representing official policies, either expressed
# or implied, of Lolapps, Inc..
# --------------------------------------------------------------------------------------------

PROGRAM='/var/www/lol-logwatcher/lolfly.py'
PROGNAME='lolfly'
PIDFILE="/var/run/$PROGNAME.pid"
ALT_PIDFILE="/var/run/$PROGNAME.sh.pid"
LOGFILE="/var/log/$PROGNAME.log"
RUN_AS_USER='root'
RUN_AS_HOME='/root'
VIRTUALENV="$RUN_AS_HOME/.virtualenvs/$PROGNAME"

function start() {
  echo "Starting $PROGRAM..."
  if [ -f $PIDFILE ]; then
    echo "$PIDFILE exists, exiting..."
    exit 1
  fi

  source $VIRTUALENV/bin/activate
  python -u $PROGRAM >> $LOGFILE 2>&1 &
  echo $! > $PIDFILE
}

function stop() {
  echo "Stopping $PROGRAM..."
  if [ -f $PIDFILE ]; then
    kill `cat $PIDFILE`
    rm $PIDFILE
  elif [ -f $ALT_PIDFILE ]; then
    kill `cat $ALT_PIDFILE`
    rm $ALT_PIDFILE
  else
    echo "$PIDFILE not found, will attempt to look at ps list"
    # DIE DIE DIE
    for pid in `ps auxwww| grep $PROGRAM | grep -v grep | grep bash | awk '{print $2}'`; do
      kill -9 $pid
    done
  fi
  rm -f $PIDFILE
}

function condrestart() {
  echo "Doing Conditional Restart..."
  if [ -f $PIDFILE ]; then
    stop
    sleep 5
    start
  else
    echo "pidfile not found, not restarting"
  fi
}

case "$1" in
  start)
    start
    ;;
  stop)
    stop
    ;;
  restart)
    stop
    sleep 5
    start
    ;;
  condrestart)
    condrestart
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|condrestart}"
esac
