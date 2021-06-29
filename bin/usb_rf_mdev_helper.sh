#!/bin/sh

# Takes care of /dev/ttyACMx devices.
#
# The mdev.conf file does not provide the ability to create persistent device
# names based on vendor and product IDs. This script looks for the Zigbee and
# Zwave sticks and assigns them to /dev/zigbee and /dev/zwave respectively.
# 
# Add an mdev.conf entry to call this script as below:
# ttyACM[0-9]*	root:dialout 0660 */home/hass/config/bin/usb_rf_mdev_helper.sh
#

logger -t mdev -p info "Running $0 for ${MDEV} - ${ACTION}"

sys_path=`find /sys/devices -iname "${MDEV}" | sed -e "s|/${SUBSYSTEM}/${MDEV}||g"`

logger -t mdev -p debug "Found device path for ${MDEV} at ${sys_path}"

[ -f "${sys_path}/../idProduct" ] || return 1
[ -f "${sys_path}/../idVendor" ] || return 1

idProduct=`cat ${sys_path}/../idProduct`
idVendor=`cat ${sys_path}/../idVendor`
devId="${idVendor}:${idProduct}"

logger -t mdev -p debug "Found USB ID for ${MDEV} as ${devId}"

path=""
case "${devId}" in
    "0451:16a8")
        path="/dev/zigbee"
    ;;
    "0658:0200")
        path="/dev/zwave"
    ;;
esac

if [[ "z${path}" != "z" ]] ; then
    case "${ACTION}" in
        'add')
            ln -s "${MDEV}" "${path}"
            logger -t mdev -p info "Created link to ${MDEV} (${devId}) as ${path}"
            return 0
        ;;
        'remove')
            [ -f "${path}" ] && rm "${path}"
            logger -t mdev -p info "Removed link to ${MDEV} (${devId}) from ${path}"
            return 0
        ;;
    esac
fi

logger -t mdev -p info "No symlink found for ${devId}"
