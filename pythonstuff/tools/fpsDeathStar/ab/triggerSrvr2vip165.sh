#!/bin/bash
SPEED_FILE=$1
SPEED=0

# make Apached Bench blast out that number of alerts all at once, then sleep
while true;
do
    # re-read the desired speed, in case it changed
    if [ -e ${SPEED_FILE} ]
    then
       # It's a file path.
       SPEED=$(< $SPEED_FILE)
    else
       echo "'$SPEED_FILE' does not exist.  Using a speed/concurrency of 1."
       SPEED=1
    fi

    # run Apache Bench at the desired speed, in the background so we don't depend on the speed of ab itself
    #ab -k -c $SPEED -n $SPEED -H "Content-Type: application/x-www-form-urlencoded" -p ./fps_gen_alert_vcrypt http://10.30.22.165/login.aspx &
    ab -c $SPEED -n $SPEED -H "Content-Type: application/x-www-form-urlencoded" -p ./fps_gen_alert_vcrypt https://10.30.22.165/login.aspx &

    sleep 1.0;
done
