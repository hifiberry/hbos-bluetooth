# hifiberry bluetooth

This is the service that manages the bluetooth connections.
It reads the config file and adjusts the BlueZ settings.

For example, you can set the different 
[bluetooth agent capability](https://github.com/arcathrax/hifiberry-bluetooth/blob/main/docs/config.md#capability).

## Requirements
### Packages
To use this service, you need to have the following packages installed:

**Arch Linux**
```bash
sudo pacman -Syyu python3 python-dbus python-gobject python-watchdog
```

**Debian**
```bash
sudo apt install python3 python3-dbus python3-gi python3-watchdog
```

### Bluetooth setup
You also need to have the bluetooth set up correctly.
Either do this by yourself or if you are using a RPi,
with a [HiFiBerry](https://www.hifiberry.com/) sound card,
you can use [this guide](https://github.com/arcathrax/hifiberry-bluetooth/blob/main/docs/setting_up_bluetooth.md).
