# Setup BT audio

## Plain Raspberry Pi OS (Trixie, 64 bit)

* Install Raspberry Pi OS
* Configure BT

## Enable BT 
```
bluetoothctl <<EOF
$(sleep 1)
power on
$(sleep 1)
agent on
$(sleep 1)
default-agent
$(sleep 1)
scan on
$(sleep 20)
EOF
