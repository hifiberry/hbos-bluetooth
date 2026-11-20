import logging
import re
import threading
import time

import dbus

from .ConfigFileManager import ConfigFileManager


def default_name_base(alias):
    """BlueZ names a second adapter "<host> #2": the name without " #N".

    None for any other name, which someone may have chosen and is kept.
    """
    match = re.fullmatch(r"(.+) #\d+", alias or "")
    return match.group(1) if match else None


def choose_adapter(adapters, configured):
    """Which adapter to use, and which to power off.

    `adapters` maps object path to address, `configured` is the address from
    the config ("" for none). Returns (path, others_to_power_off).

    With a configured address that is present, that adapter is used and all
    others are powered off, so a phone sees one device. Without one, or when
    the configured adapter is missing (a USB stick not plugged in), the first
    adapter is used and the others are left alone, as before there was a
    choice. Returns (None, []) without any adapter.
    """
    if not adapters:
        return None, []
    configured = (configured or "").strip().upper()
    for path, address in sorted(adapters.items()):
        if configured and address.upper() == configured:
            return path, sorted(p for p in adapters if p != path)
    return sorted(adapters)[0], []


class Adapter:
    BUS_NAME = "org.bluez"
    ADAPTER_IFACE = "org.bluez.Adapter1"

    # bluez throws these when the adapter is rfkill-blocked or otherwise
    # not ready yet at boot. They're transient — retry instead of crashing.
    _TRANSIENT_BLUEZ_ERRORS = (
        "org.bluez.Error.NotReady",
        "org.bluez.Error.Failed",  # raised as "Not Powered" / "Blocked"
        "org.bluez.Error.Busy",
    )

    # How often, and how far apart, a property change that bluetoothd
    # rejects as busy is tried again. A mode change goes through the
    # kernel, which on some controllers (a Realtek USB stick with LE
    # advertising running) takes long enough that a second change sent
    # right after the first is rejected with "Busy".
    BUSY_RETRIES = 10
    BUSY_DELAY = 0.3

    config_file_manager = ConfigFileManager()

    def __init__(self, ready_timeout=30.0):
        self.bus = dbus.SystemBus()
        self.ready_timeout = ready_timeout
        self.path = None
        self.adapter_props = None
        # The config watcher's timer thread and the main loop's adapter
        # signals both select and configure the adapter.
        self._lock = threading.RLock()
        self.select()

    def _adapters(self):
        """Every Bluetooth adapter BlueZ knows: object path -> address."""
        manager = dbus.Interface(self.bus.get_object(self.BUS_NAME, "/"),
                                 "org.freedesktop.DBus.ObjectManager")
        return {
            str(path): str(ifaces[self.ADAPTER_IFACE].get("Address", ""))
            for path, ifaces in manager.GetManagedObjects().items()
            if self.ADAPTER_IFACE in ifaces
        }

    def _props(self, path):
        return dbus.Interface(self.bus.get_object(self.BUS_NAME, path),
                              dbus.PROPERTIES_IFACE)

    def select(self):
        """Choose the adapter from the config, power it on and configure it.

        Run at start, after a change of the config file, and when an adapter
        appears or goes. The adapters not chosen are powered off.
        """
        with self._lock:
            adapters = self._adapters()
            path, others = choose_adapter(adapters, self.config_file_manager.adapter)
            if path is None:
                raise RuntimeError("No Bluetooth adapter found")
            if path != self.path:
                logging.info("[Adapter] using %s (%s)", path, adapters[path])
            for other in others:
                self._power_off(other, adapters[other])
            self.path = path
            self.adapter_props = self._props(path)
            self._wait_until_powered(timeout=self.ready_timeout)
            self._name()
            self._apply_config()

    def _name(self):
        """Give the adapter the name the first adapter would have.

        A USB stick next to the built-in adapter gets BlueZ's default name
        for a second adapter, "<host> #2", which phones would then show.
        """
        try:
            alias = str(self.adapter_props.Get(self.ADAPTER_IFACE, "Alias"))
            base = default_name_base(alias)
            if base:
                logging.info("[Adapter] renaming %r to %r", alias, base)
                self._set("Alias", dbus.String(base))
        except dbus.exceptions.DBusException as e:
            logging.warning("[Adapter] could not rename the adapter: %s", e)

    def _power_off(self, path, address):
        props = self._props(path)
        try:
            if bool(props.Get(self.ADAPTER_IFACE, "Powered")):
                logging.info("[Adapter] powering off %s (%s): not the chosen adapter",
                             path, address)
                self._set_on(props, "Powered", dbus.Boolean(False))
        except dbus.exceptions.DBusException as e:
            # An adapter that went away meanwhile, or refuses: it is not ours.
            logging.warning("[Adapter] could not power off %s: %s", path, e)

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

    @staticmethod
    def _is_busy(error):
        name = error.get_dbus_name() if hasattr(error, "get_dbus_name") else ""
        if name == "org.bluez.Error.Busy":
            return True
        return name == "org.bluez.Error.Failed" and "Busy" in str(error)

    def _set_on(self, props, name, value):
        """Set one adapter property, retrying while bluetoothd is busy."""
        for attempt in range(self.BUSY_RETRIES + 1):
            try:
                props.Set(self.ADAPTER_IFACE, name, value)
                return
            except dbus.exceptions.DBusException as e:
                if not self._is_busy(e) or attempt == self.BUSY_RETRIES:
                    raise
                logging.info("[Adapter] %s: adapter busy, retrying", name)
                time.sleep(self.BUSY_DELAY)

    def _set(self, name, value):
        self._set_on(self.adapter_props, name, value)

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
        self.select()
