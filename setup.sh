#!/usr/bin/env bash

if [ ${EUID} -ne 0 ]
then
  echo "This script needs to be run as root."
	exit 1
fi

cp -r . /opt/hbos-bluetooth-service
cp ./hbos-bluetooth.service 

rm /etc/systemd/system/hbos-bluetooth.service
cp hbos-bluetooth.service /etc/systemd/system
