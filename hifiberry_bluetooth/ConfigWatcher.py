import os
import threading

import dbus
from watchdog.events import FileSystemEventHandler

AGENT_PATH = "/com/hifiberry/btagent"


class ConfigWatcher(FileSystemEventHandler):
    """Watch the config file for changes and reload agent capability."""

    # A writer saving the file produces several events in a row (the web
    # interface's pairing mode, three within 80 ms). They are merged: the
    # file is read once this long after the last of them.
    SETTLE_DELAY = 0.5

    def __init__(self, agent, agent_manager, config_manager, adapter):
        self.agent = agent
        self.agent_manager = agent_manager
        self.config_manager = config_manager
        self.adapter = adapter
        self.current_capability = config_manager.capability
        self._lock = threading.Lock()
        self._timer = None

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

    def _reload_logged(self):
        """Reload, logging a failure instead of raising it.

        An exception raised in the watchdog thread used to end that thread,
        and with it every later reload until the service was restarted.
        Now a failure is logged and the next change of the file tries again.
        """
        with self._lock:
            self._timer = None
        try:
            self.reload_agent()
        except Exception:
            self.config_manager.logger.exception(
                "[ConfigWatcher] Applying the config failed; waiting for the next change"
            )

    def schedule_reload(self):
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self.SETTLE_DELAY, self._reload_logged)
            self._timer.daemon = True
            self._timer.start()

    def _is_config(self, path):
        return os.path.abspath(path) == os.path.abspath(self.config_manager.config_file)

    def on_modified(self, event):
        if self._is_config(event.src_path):
            self.config_manager.logger.info("[ConfigWatcher] Config file modified, reloading agent...")
            self.schedule_reload()

    def on_moved(self, event):
        # A writer that saves through a temporary file and a rename.
        if self._is_config(getattr(event, "dest_path", "")):
            self.config_manager.logger.info("[ConfigWatcher] Config file replaced, reloading agent...")
            self.schedule_reload()
