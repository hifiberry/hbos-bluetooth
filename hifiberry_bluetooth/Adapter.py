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

    def _apply_config(self):
        # Wrap booleans with explicit DBus typing (like dbus.UInt32 below), so a
        # non-bool value can never reach DBus with the wrong signature.
        self.adapter_props.Set(self.ADAPTER_IFACE, 'Discoverable',
                               dbus.Boolean(self.config_file_manager.discoverable))
        self.adapter_props.Set(self.ADAPTER_IFACE, 'DiscoverableTimeout',
                               dbus.UInt32(self.config_file_manager.discoverable_timeout))
        self.adapter_props.Set(self.ADAPTER_IFACE, 'Pairable',
                               dbus.Boolean(self.config_file_manager.pairable))
        self.adapter_props.Set(self.ADAPTER_IFACE, 'PairableTimeout',
                               dbus.UInt32(self.config_file_manager.pairable_timeout))

    def update_properties(self):
        self.config_file_manager.load_config_values()
        self._apply_config()
