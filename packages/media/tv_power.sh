#!/bin/sh
#
# Read or set the power status of the TV connected to the HDMI CEC controller
# Raspberry Pi at ${HDMI_CEC_LR_HOST}.
#
# When called without arguments, returns the current power status. When called
# with a single argument, sets the new status ('on' or 'standby').

if [ "$#" -gt "1" ]; then
    echo "Usage: $0 [command]"
    exit 1
fi

if [ "$#" -eq "0" ]; then
    ssh hass@${HDMI_CEC_LR_HOST} "echo 'pow 0' | cec-client -s -d 1" | grep status | awk -F': ' '{print $2}'
else
    ssh hass@${HDMI_CEC_LR_HOST} "echo '$1 0' | cec-client -s -d 1"
fi
