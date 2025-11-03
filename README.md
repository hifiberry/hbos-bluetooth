# hbos bluetooth service

This is the service that manages the bluetooth connections.
It reads the config file and adjusts the BlueZ settings.

For example, you can set the different 
[bluetooth agent capability](https://github.com/arcathrax/hbos-bluetooth-service/blob/main/docs/config.md#capability).

## Requirements
To use this service, you need to have the following packages installed:

**archlinux**
```bash
sudo pacman -Syyu python3 python-dbus python-gobject python-watchdog
```
