# Setup BT audio

## Plain Raspberry Pi OS (Trixie, 64 bit)

* Install Raspberry Pi OS
* Configure BT

## Enable BT 
```
echo "power on" | bluetoothctl
echo "agent on" | bluetoothctl
echo "default-agent" | bluetoothctl
echo "pairable on" | bluetoothctl
echo "discoverable on" | bluetoothctl
```
