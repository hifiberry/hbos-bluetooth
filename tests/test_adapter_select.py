import dbus
import pytest

from hifiberry_bluetooth.Adapter import Adapter, choose_adapter, default_name_base

BUILTIN = ("/org/bluez/hci0", "00:11:22:33:44:55")
STICK = ("/org/bluez/hci1", "AA:BB:CC:DD:EE:FF")


def test_no_adapter():
    assert choose_adapter({}, "") == (None, [])


def test_without_a_choice_the_first_is_used_and_others_left_alone():
    assert choose_adapter(dict([BUILTIN, STICK]), "") == (BUILTIN[0], [])


def test_the_configured_adapter_is_used_and_the_others_powered_off():
    assert choose_adapter(dict([BUILTIN, STICK]), STICK[1]) == (STICK[0], [BUILTIN[0]])


def test_the_address_is_matched_without_case():
    assert choose_adapter(dict([BUILTIN, STICK]), STICK[1].lower())[0] == STICK[0]


def test_a_missing_configured_adapter_falls_back_to_the_first():
    # The stick is unplugged: use what is there, power nothing off.
    assert choose_adapter(dict([BUILTIN]), STICK[1]) == (BUILTIN[0], [])


def test_the_stick_alone_is_used_when_it_is_hci0():
    # Built-in Bluetooth disabled in config.txt: the stick becomes hci0.
    stick0 = ("/org/bluez/hci0", STICK[1])
    assert choose_adapter(dict([stick0]), STICK[1]) == (stick0[0], [])


@pytest.mark.parametrize("alias,base", [
    ("speaker #2", "speaker"),
    ("my speaker #10", "my speaker"),
    ("speaker", None),
    ("HiFiBerry-speaker", None),
    ("#2", None),
    ("", None),
])
def test_default_name_base(alias, base):
    assert default_name_base(alias) == base


class FakeProps:
    def __init__(self, powered, alias="speaker"):
        self.values = {"Powered": powered, "Alias": alias}

    def Get(self, iface, name):
        return self.values[name]

    def Set(self, iface, name, value):
        self.values[name] = value


class FakeConfig:
    adapter = STICK[1]
    discoverable = False
    discoverable_timeout = 60
    pairable = True
    pairable_timeout = 0


@pytest.fixture
def adapter(monkeypatch):
    props = {BUILTIN[0]: FakeProps(True), STICK[0]: FakeProps(False, alias="speaker #2")}
    a = Adapter.__new__(Adapter)
    a.ready_timeout = 1
    a.path = None
    a.adapter_props = None
    a._lock = __import__("threading").RLock()
    a.config_file_manager = FakeConfig()
    monkeypatch.setattr(a, "_adapters", lambda: dict([BUILTIN, STICK]))
    monkeypatch.setattr(a, "_props", lambda path: props[path])
    a.props = props
    return a


def test_select_powers_the_chosen_on_and_the_other_off(adapter):
    adapter.select()
    assert adapter.path == STICK[0]
    assert bool(adapter.props[STICK[0]].values["Powered"]) is True
    assert bool(adapter.props[BUILTIN[0]].values["Powered"]) is False
    assert adapter.props[STICK[0]].values["DiscoverableTimeout"] == 60
    assert "Discoverable" not in adapter.props[BUILTIN[0]].values


def test_select_back_to_the_first_leaves_the_other_powered(adapter):
    adapter.select()
    adapter.config_file_manager.adapter = ""
    adapter.select()
    assert adapter.path == BUILTIN[0]
    assert bool(adapter.props[BUILTIN[0]].values["Powered"]) is True
    # Not chosen, but not powered off either: the behaviour without a choice.
    assert bool(adapter.props[STICK[0]].values["Powered"]) is True


def test_an_adapter_that_cannot_be_powered_off_does_not_stop_the_choice(adapter):
    def refuse(iface, name, value):
        raise dbus.exceptions.DBusException("Blocked", name="org.bluez.Error.Failed")
    adapter.props[BUILTIN[0]].Set = refuse
    adapter.select()
    assert adapter.path == STICK[0]


def test_the_chosen_stick_loses_the_default_suffix(adapter):
    adapter.select()
    assert adapter.props[STICK[0]].values["Alias"] == "speaker"
    assert adapter.props[BUILTIN[0]].values["Alias"] == "speaker"


def test_a_chosen_name_is_kept(adapter):
    adapter.props[STICK[0]].values["Alias"] = "Living room"
    adapter.select()
    assert adapter.props[STICK[0]].values["Alias"] == "Living room"
