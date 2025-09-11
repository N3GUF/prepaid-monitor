#!/bin/bash
# This script starts and stops the prepaid-monitor app
export PROFILE_EXPORTS=/usr/prod/ppol/sys-utils/bin/profile-exports.sh

if [ -f ${PROFILE_EXPORTS} ]; then
    source ${PROFILE_EXPORTS}
else
    echo 'Missing profile exports!' ${PROFILE_EXPORTS}
    exit 1
fi

export ORA_DB_DSN=us-atl-pa-ppd-db-p-n-001:1521/ppdprd
export SPLUNK_INDEX=pmts-prod-fintwist
export SPLUNK_CACHE=/tmp/pmts-prod-fintwist-splunk-cache.json
export TOKEN_FILE=${SCRIPT_HOME}/prepaid-monitor/splunkToken.txt

if [ -f ${TOKEN_FILE} ]; then
    source ${TOKEN_FILE}
else
    echo 'Missing Splunk token!' ${TOKEN_FILE}
    exit 1
fi

INSTANCE=prepaid-monitor.py

list_pids() {
        echo Currently running process id for ${LOGNAME}:
        ps axuww |grep -s ${INSTANCE} | grep -s ${LOGNAME} | grep -v grep |awk '{print $2}'
}

start_app() {
        echo "Starting ${INSTANCE}..."
        XCODE=0
        source ${SCRIPT_HOME}/prepaid-monitor/.venv/bin/activate
        nohup python ${SCRIPT_HOME}/prepaid-monitor/app/prepaid-monitor.py & 
        XCODE=$?
         
        #check the return code
        if [[ $XCODE -ne 0 ]]
        then
                echo `date "+%Y-%m-%d-%H:%M:%S"` "Error starting prepaid-monitor: " $XCODE 
        fi
}

stop_app() {
    FORCE=$1

        echo "Stopping ${INSTANCE}, forced = $FORCE..."
        # issue regular orderly shutdown kill command to java app run by user executing this script
        ps axuww |grep ${INSTANCE} | grep -s ${LOGNAME} |grep -v grep |awk '{print $2}'|xargs kill
        sleep 3
          
        #check again if any instances still running
        if [[ "${FORCE}" == "Y" ]]; then
                # is it still running after nicely asking to shutdown
                if ps -ef | grep -s ${INSTANCE} | grep -s ${LOGNAME} |grep -v grep > /dev/null 2>&1
                then
                        #its about to get real
                        echo "still running after kill command, forcing ${INSTANCE} to stop"
                        ps axuww |grep ${INSTANCE} |  grep -s ${LOGNAME} |grep -v grep |awk '{print $2}'|xargs kill -9
                        sleep 3
                fi
        fi

        if ps -ef |grep -s ${INSTANCE} |  grep -s ${LOGNAME} | grep -v grep > /dev/null 2>&1
        then
                echo "${INSTANCE} stopped"
        else
                echo "${INSTANCE} still running after kill -9"
        fi

}


case "$1" in
        "start"|"START")
                start_app
                sleep 2
                list_pids
                ;;

        "stop"|"STOP")
                #ask to shutdown orderly
                stop_app N
                list_pids
                ;;

        "force"|"FORCE")
                #force a shutdown if necessary
                stop_app Y
                list_pids
                ;;

        "restart"|"RESTART")
                #ask to shutdown orderly
                stop_app N
                start_app
                list_pids
                ;;

        *)
                echo "Usage is $0 {start|stop|restart|force}"
                list_pids
                ;;
esac

exit 0
