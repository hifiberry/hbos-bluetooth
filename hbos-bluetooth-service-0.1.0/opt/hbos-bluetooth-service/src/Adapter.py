import dbus
from ConfigFileManager import ConfigFileManager

class Adapter:
    BUS_NAME = "org.bluez"
    ADAPTER_ROOT = "/org/bluez/hci"
    ADAPTER_IFACE = "org.bluez.Adapter1"

    config_file_manager = ConfigFileManager()
    def __init__(self, idx=0):
        bus = dbus.SystemBus()
        self.path = f'{self.ADAPTER_ROOT}{idx}'
        self.adapter_object = bus.get_object(self.BUS_NAME, self.path)
        self.adapter_props = dbus.Interface(self.adapter_object, dbus.PROPERTIES_IFACE)
        self.adapter_props.Set(self.ADAPTER_IFACE, 'Discoverable',
                               self.config_file_manager.discoverable)
        self.adapter_props.Set(self.ADAPTER_IFACE, 'DiscoverableTimeout',
                               dbus.UInt32(self.config_file_manager.discoverable_timeout))
        self.adapter_props.Set(self.ADAPTER_IFACE, 'Pairable',
                               self.config_file_manager.pairable)
        self.adapter_props.Set(self.ADAPTER_IFACE, 'PairableTimeout',
                               dbus.UInt32(self.config_file_manager.pairable_timeout))

    def update_properties(self):
        self.config_file_manager.load_config_values()
        self.adapter_props.Set(self.ADAPTER_IFACE, 'Discoverable',
                                 self.config_file_manager.discoverable)
        self.adapter_props.Set(self.ADAPTER_IFACE, 'DiscoverableTimeout',
                                 dbus.UInt32(self.config_file_manager.discoverable_timeout))
        self.adapter_props.Set(self.ADAPTER_IFACE, 'Pairable',
                                 self.config_file_manager.pairable)
        self.adapter_props.Set(self.ADAPTER_IFACE, 'PairableTimeout',
                                 dbus.UInt32(self.config_file_manager.pairable_timeout))
