import dbus
import pytest

from hifiberry_bluetooth.Adapter import Adapter


class FakeProps:
    """Adapter1 properties that reject the first `busy` Sets as busy."""

    def __init__(self, busy=0, error="org.bluez.Error.Failed", message="Busy"):
        self.busy = busy
        self.error = error
        self.message = message
        self.calls = []
        self.values = {}

    def Set(self, iface, name, value):
        self.calls.append(name)
        if self.busy:
            self.busy -= 1
            raise dbus.exceptions.DBusException(self.message, name=self.error)
        self.values[name] = value


def adapter_with(props):
    a = Adapter.__new__(Adapter)
    a.adapter_props = props
    return a


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr("hifiberry_bluetooth.Adapter.time.sleep", lambda s: None)


def test_applies_all_four_properties():
    props = FakeProps()
    adapter_with(props)._apply_config()
    assert props.calls == ["Discoverable", "DiscoverableTimeout", "Pairable", "PairableTimeout"]


@pytest.mark.parametrize("error", ["org.bluez.Error.Failed", "org.bluez.Error.Busy"])
def test_busy_is_retried(error):
    props = FakeProps(busy=3, error=error)
    adapter_with(props)._apply_config()
    assert props.calls[:4] == ["Discoverable"] * 4
    assert set(props.values) == {"Discoverable", "DiscoverableTimeout", "Pairable", "PairableTimeout"}


def test_busy_gives_up_after_the_retries():
    props = FakeProps(busy=Adapter.BUSY_RETRIES + 1)
    with pytest.raises(dbus.exceptions.DBusException):
        adapter_with(props)._apply_config()
    assert props.calls == ["Discoverable"] * (Adapter.BUSY_RETRIES + 1)


def test_other_errors_are_not_retried():
    props = FakeProps(busy=1, message="Not Powered")
    with pytest.raises(dbus.exceptions.DBusException):
        adapter_with(props)._apply_config()
    assert props.calls == ["Discoverable"]
