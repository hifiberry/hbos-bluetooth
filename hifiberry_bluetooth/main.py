import dbus
import dbus.mainloop.glib
from gi.repository import GLib
from watchdog.observers import Observer
from .Agent import Agent
from .Adapter import Adapter
from .ConfigFileManager import ConfigFileManager
from .ConfigWatcher import ConfigWatcher
import os

BUS_NAME = "org.bluez"
AGNT_MNGR_IFACE = "org.bluez.AgentManager1"
AGENT_PATH = "/com/hifiberry/btagent"
AGNT_MNGR_PATH = "/org/bluez"

# Initialize config manager
config_file_manager = ConfigFileManager()

# Setup D-Bus main loop
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SystemBus()

# Setup main loop
mainloop = GLib.MainLoop()


def properties_changed(interface, changed, invalidated, path=None):
    if interface == Adapter.ADAPTER_IFACE and "Discoverable" in changed:
        if not changed["Discoverable"]:
            config_file_manager.logger.info(
                "Discoverable timed out, setting config value to False"
            )
            config_file_manager.set_config_value("Bluetooth", "discoverable", "False")


def main():
    # Initialize agent and agent manager
    agent = Agent(bus, AGENT_PATH)
    agnt_mngr = dbus.Interface(bus.get_object(BUS_NAME, AGNT_MNGR_PATH), AGNT_MNGR_IFACE)
    agnt_mngr.RegisterAgent(AGENT_PATH, config_file_manager.capability)
    agnt_mngr.RequestDefaultAgent(AGENT_PATH)
    config_file_manager.logger.info(f"[Main] Agent registered with capability: {config_file_manager.capability}")

    # Initialize Adapter
    adapter = Adapter()

    bus.add_signal_receiver(
        properties_changed,
        dbus_interface=dbus.PROPERTIES_IFACE,
        signal_name="PropertiesChanged",
        arg0=Adapter.ADAPTER_IFACE,
        path_keyword="path",
    )

    # Start config watcher
    observer = Observer()
    watcher = ConfigWatcher(agent, agnt_mngr, config_file_manager, adapter)
    observer.schedule(watcher, path=os.path.dirname(os.path.abspath(config_file_manager.config_file)) or ".", recursive=False)
    observer.start()

    try:
        mainloop.run()
    except KeyboardInterrupt:
        config_file_manager.logger.info("[Main] Shutting down...")
        try:
            agnt_mngr.UnregisterAgent(AGENT_PATH)
        except dbus.exceptions.DBusException:
            pass
        observer.stop()
        observer.join()
        mainloop.quit()


if __name__ == "__main__":
    main()
