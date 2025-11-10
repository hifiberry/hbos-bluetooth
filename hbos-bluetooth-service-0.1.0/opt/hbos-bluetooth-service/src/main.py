import dbus
import dbus.mainloop.glib
from gi.repository import GLib
from ConfigFileManager import ConfigFileManager
from Agent import Agent
from Adapter import Adapter
from watchdog.observers import Observer
from ConfigWatcher import ConfigWatcher
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




if __name__ == "__main__":
    # Initialize agent and agent manager
    agent = Agent(bus, AGENT_PATH)
    agnt_mngr = dbus.Interface(bus.get_object(BUS_NAME, AGNT_MNGR_PATH), AGNT_MNGR_IFACE)
    agnt_mngr.RegisterAgent(AGENT_PATH, config_file_manager.capability)
    agnt_mngr.RequestDefaultAgent(AGENT_PATH)
    config_file_manager.logger.info(f"[Main] Agent registered with capability: {config_file_manager.capability}")

    # Initialize Adapter
    adapter = Adapter()

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
