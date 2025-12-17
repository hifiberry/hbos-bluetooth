from watchdog.events import FileSystemEventHandler
import dbus
AGENT_PATH = "/com/hifiberry/btagent"
import os

class ConfigWatcher(FileSystemEventHandler):
    """Watch the config file for changes and reload agent capability."""

    def __init__(self, agent, agent_manager, config_manager, adapter):
        self.agent = agent
        self.agent_manager = agent_manager
        self.config_manager = config_manager
        self.adapter = adapter
        self.current_capability = config_manager.capability

    def reload_agent(self):
        self.config_manager.load_config_values()
        new_capability = self.config_manager.capability
        if new_capability != self.current_capability:
            self.config_manager.logger.info(
                f"[ConfigWatcher] Updating agent capability: {self.current_capability} to {new_capability}"
            )
            try:
                self.agent_manager.UnregisterAgent(AGENT_PATH)
            except dbus.exceptions.DBusException as e:
                self.config_manager.logger.warning(f"Could not unregister agent: {e}")

            self.agent_manager.RegisterAgent(AGENT_PATH, new_capability)
            self.agent_manager.RequestDefaultAgent(AGENT_PATH)
            self.current_capability = new_capability

        self.config_manager.logger.info("[ConfigWatcher] Updating adapter properties...")
        self.adapter.update_properties()

    def on_modified(self, event):
        if os.path.abspath(event.src_path) == os.path.abspath(self.config_manager.config_file):
            self.config_manager.logger.info("[ConfigWatcher] Config file modified, reloading agent...")
            self.reload_agent()
