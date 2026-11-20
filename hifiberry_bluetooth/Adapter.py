import logging
import time

import dbus

from .ConfigFileManager import ConfigFileManager


class Adapter:
    BUS_NAME = "org.bluez"
    ADAPTER_ROOT = "/org/bluez/hci"
    ADAPTER_IFACE = "org.bluez.Adapter1"

    # bluez throws these when the adapter is rfkill-blocked or otherwise
    # not ready yet at boot. They're transient — retry instead of crashing.
    _TRANSIENT_BLUEZ_ERRORS = (
        "org.bluez.Error.NotReady",
        "org.bluez.Error.Failed",  # raised as "Not Powered" / "Blocked"
        "org.bluez.Error.Busy",
    )

    config_file_manager = ConfigFileManager()

    def __init__(self, idx=0, ready_timeout=30.0):
        bus = dbus.SystemBus()
        self.path = f'{self.ADAPTER_ROOT}{idx}'
        self.adapter_object = bus.get_object(self.BUS_NAME, self.path)
        self.adapter_props = dbus.Interface(self.adapter_object, dbus.PROPERTIES_IFACE)

        # Power the adapter on (idempotent) before setting any other property.
        # On fresh boot bluez often reports the adapter as "off-blocked" until
        # it has finished its own rfkill/initialization dance; trying to set
        # Discoverable/Pairable in that state throws "Not Powered" and the
        # service then crash-loops to systemd's StartLimit. Power-on with
        # retry collapses both failure modes into a clean wait.
        self._wait_until_powered(timeout=ready_timeout)

        self._apply_config()

    def _wait_until_powered(self, timeout):
        deadline = time.monotonic() + timeout
        last_error = None
        while True:
            try:
                powered = bool(self.adapter_props.Get(self.ADAPTER_IFACE, "Powered"))
                if powered:
                    return
                self.adapter_props.Set(self.ADAPTER_IFACE, "Powered", dbus.Boolean(True))
                # Confirm the change took effect before continuing.
                if bool(self.adapter_props.Get(self.ADAPTER_IFACE, "Powered")):
                    logging.info("[Adapter] powered on")
                    return
            except dbus.exceptions.DBusException as e:
                last_error = e
                name = e.get_dbus_name() if hasattr(e, "get_dbus_name") else ""
                if name not in self._TRANSIENT_BLUEZ_ERRORS:
                    # Unknown error class — surface immediately rather than
                    # busy-looping forever.
                    raise
                logging.warning(
                    "[Adapter] not ready yet (%s); retrying", name or e
                )

            if time.monotonic() >= deadline:
                raise RuntimeError(
                    f"Bluetooth adapter at {self.path} did not become powered "
                    f"within {timeout:.0f}s (last error: {last_error})"
                )
            time.sleep(1.0)

    # How often, and how far apart, a property change that bluetoothd
    # rejects as busy is tried again. A mode change goes through the
    # kernel, which on some controllers (a Realtek USB stick with LE
    # advertising running) takes long enough that a second change sent
    # right after the first is rejected with "Busy".
    BUSY_RETRIES = 10
    BUSY_DELAY = 0.3

    @staticmethod
    def _is_busy(error):
        name = error.get_dbus_name() if hasattr(error, "get_dbus_name") else ""
        if name == "org.bluez.Error.Busy":
            return True
        return name == "org.bluez.Error.Failed" and "Busy" in str(error)

    def _set(self, name, value):
        """Set one adapter property, retrying while bluetoothd is busy."""
        for attempt in range(self.BUSY_RETRIES + 1):
            try:
                self.adapter_props.Set(self.ADAPTER_IFACE, name, value)
                return
            except dbus.exceptions.DBusException as e:
                if not self._is_busy(e) or attempt == self.BUSY_RETRIES:
                    raise
                logging.info("[Adapter] %s: adapter busy, retrying", name)
                time.sleep(self.BUSY_DELAY)

    def _apply_config(self):
        # Wrap booleans with explicit DBus typing (like dbus.UInt32 below), so a
        # non-bool value can never reach DBus with the wrong signature.
        # bluetoothd answers a value the adapter already has without a mode
        # change, so setting all four each time costs nothing.
        self._set('Discoverable', dbus.Boolean(self.config_file_manager.discoverable))
        self._set('DiscoverableTimeout',
                  dbus.UInt32(self.config_file_manager.discoverable_timeout))
        self._set('Pairable', dbus.Boolean(self.config_file_manager.pairable))
        self._set('PairableTimeout', dbus.UInt32(self.config_file_manager.pairable_timeout))

    def update_properties(self):
        self.config_file_manager.load_config_values()
        self._apply_config()
