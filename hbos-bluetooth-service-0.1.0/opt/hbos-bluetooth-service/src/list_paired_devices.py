import dbus

BUS_NAME = "org.bluez"
INTERFACE_NAME = "org.bluez.Device1"

# Connect to the system bus
bus = dbus.SystemBus()

# BlueZ object manager
manager = dbus.Interface(
    bus.get_object(BUS_NAME, "/"),
    "org.freedesktop.DBus.ObjectManager"
)

# Get all objects
objects = manager.GetManagedObjects()

# Filter for devices
devices = []
for path, interfaces in objects.items():
    if INTERFACE_NAME in interfaces:
        dev = interfaces[INTERFACE_NAME]
        name = dev.get("Name", "Unknown")
        addr = dev.get("Address", "Unknown")
        path = path
        connected = dev.get("Connected", False)
        devices.append((name, addr, connected, path))

# Print paired devices
for name, addr, connected, path in devices:
    print("path: " + path)
    print(name + "(" + addr + ") - Connected: " + str(connected))
