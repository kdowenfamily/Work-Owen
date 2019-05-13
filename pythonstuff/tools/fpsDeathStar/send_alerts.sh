#!/bin/bash

START=`date '+%s'`

# time keeping variables
MARK=$START
NOW=$START
SEC_SINCE_MARK=0
INTERVAL=60

# read the command argument
ORIGARG=$1
LOGIQ=$1
TNAME=$$	# target name (start with just the PID)
if [ -e ${LOGIQ} ]
then
    # It's a file path.
    TNAME=`basename $LOGIQ |cut -d. -f1`  # Use its name for your output-file name.
    LOGIQ=$(< $ORIGARG)
fi

# set defaults
ct_file="/tmp/${LOGIQ}_${TNAME}_alert_log.txt"  # file for sent-alert counts
is_dcd_file="/tmp/${TNAME}_DCD.txt"		# touch file - if there, target is a DCD
use_https_file="/tmp/${TNAME}_HTTPS.txt"	# touch file - if there, send over HTTPS
PROTO=""	# protocol/port for htSender
FPSPATH=""	# -f ('Alert Path' in BIG-IP FPS profile) for htSender
ct_alerts=0	# total alerts successfully sent by htSender
avg_latency=0   # average latency

# send alerts forever
while true
do 
    # if the alert_log file went away, restart our alert count
    if [[ ! -e ${ct_file} ]]
    then
        ct_alerts=0
        echo "$NOW $ct_alerts" >${ct_file}
    fi

    # Re-read the target file (if it exists) in case the target's IP address changed.
    if [ -e "$ORIGARG" ]
    then
        TNAME=`basename $ORIGARG |cut -d. -f1`  # It's a file path. Use its name for your output-file name.
        LOGIQ=$(< $ORIGARG)
        ct_file="/tmp/${LOGIQ}_${TNAME}_alert_log.txt"

        # Use a special alert path if this is a VIP
        if [[ ! -e ${is_dcd_file} ]]
        then
            # special path for VIPs
            FPSPATH="-f /stats"
        fi

        # set HTTP or HTTPS
        if [[ -e ${use_https_file} ]]
        then
            PROTO="--protocol https"
        else
            PROTO="--protocol http"
        fi
    fi

    # invoke htSender and add in its count of successful alerts
    new_alerts=`python htSender_ad.py --log-iq $LOGIQ -R /tmp/rate -U /tmp/threads $PROTO $FPSPATH --path qadata`
    while read -r line
    do
        if [[ $line =~ ^[0-9]+$ ]]
        then
            ct_alerts=$((ct_alerts + line))
        elif [[ $line =~ Average ]]
        then
            avg_latency=`echo $line |sed -e 's/[^0-9]//g'`
        fi
    done <<< "$new_alerts"
    new_alerts=`python htSender_ad.py --log-iq $LOGIQ -R /tmp/rate -U /tmp/threads $PROTO $FPSPATH --path qausername-update`
    while read -r line
    do
        if [[ $line =~ ^[0-9]+$ ]]
        then
            ct_alerts=$((ct_alerts + line))
        elif [[ $line =~ Average ]]
        then
            avg_next=`echo $line |sed -e 's/[^0-9]//g'`
            avg_latency=$(( (avg_latency + avg_next)/2 ))
        fi
    done <<< "$new_alerts"

    # record the time it ended
    NOW=`date '+%s'`
    SEC_SINCE_MARK=$(($NOW-$MARK))

    # keep count of successful alerts if we are at a mark
    if [ "$SEC_SINCE_MARK" -ge "$INTERVAL" ] || [ "$ct_alerts" -eq 0 ]
    then
        echo "$NOW $ct_alerts $avg_latency" >>${ct_file}
        MARK=$NOW
    fi
done
