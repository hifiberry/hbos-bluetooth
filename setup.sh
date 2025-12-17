#!/usr/bin/env bash

installation_path="/opt/hifiberry-bluetooth"

set -e

if [ ${EUID} -ne 0 ]
then
  echo "This script needs to be run as root."
	exit 1
fi

echo "Stopping old service. (if there is any)"
systemctl disable hifiberry-bluetooth.service > /dev/null || true
systemctl stop hifiberry-bluetooth.service > /dev/null || true
echo "Successfully stopped old service. (if there was any)"

echo "Removing old project files from $installation_path"
rm -rf $installation_path > /dev/null
echo "Successfully removed old leftover files. (if there were any)"

echo "Copying new project files into $installation_path."
cp -r . $installation_path > /dev/null
echo "Successfully copied new files into $installation_path."

echo "Removing old service file. (if there is any)"
rm /etc/systemd/system/hifiberry-bluetooth.service > /dev/null || true
echo "Successfully removed old service file. (if there was any)"

echo "Copying new service file."
cp ./hifiberry-bluetooth.service /etc/systemd/system > /dev/null
echo "Successfully copied new service file."

echo "Installing dependencies..."
apt-get install python3 -y > /dev/null
apt-get install python3-dbus -y > /dev/null
apt-get install python3-gi -y > /dev/null
apt-get install python3-watchdog -y > /dev/null
echo "Dependencies installed"



echo "Starting service."
systemctl enable hifiberry-bluetooth.service > /dev/null
systemctl start hifiberry-bluetooth.service > /dev/null
echo "Successfully started service."
