import threading
import time
from types import SimpleNamespace

from hifiberry_bluetooth.ConfigWatcher import ConfigWatcher


class FakeConfig:
    def __init__(self, path):
        self.config_file = path
        self.capability = "NoInputNoOutput"
        self.loads = 0
        self.logger = SimpleNamespace(info=lambda *a, **k: None,
                                      warning=lambda *a, **k: None,
                                      exception=self._exception)
        self.logged = []

    def _exception(self, msg, *a):
        self.logged.append(msg)

    def load_config_values(self):
        self.loads += 1


class FakeAdapter:
    def __init__(self, fail=0):
        self.fail = fail
        self.updates = 0
        self.done = threading.Event()

    def update_properties(self):
        self.updates += 1
        self.done.set()
        if self.fail:
            self.fail -= 1
            raise RuntimeError("org.bluez.Error.Failed: Busy")


def watcher(tmp_path, adapter):
    w = ConfigWatcher(None, None, FakeConfig(str(tmp_path / "bluetooth.conf")), adapter)
    w.SETTLE_DELAY = 0.05
    return w


def modified(path):
    return SimpleNamespace(src_path=str(path))


def test_a_burst_of_events_reloads_once(tmp_path):
    adapter = FakeAdapter()
    w = watcher(tmp_path, adapter)
    for _ in range(3):
        w.on_modified(modified(tmp_path / "bluetooth.conf"))
    assert adapter.done.wait(2)
    time.sleep(0.2)
    assert adapter.updates == 1
    assert w.config_manager.loads == 1


def test_other_files_are_ignored(tmp_path):
    adapter = FakeAdapter()
    w = watcher(tmp_path, adapter)
    w.on_modified(modified(tmp_path / "other.conf"))
    time.sleep(0.2)
    assert adapter.updates == 0


def test_a_rename_onto_the_file_reloads(tmp_path):
    adapter = FakeAdapter()
    w = watcher(tmp_path, adapter)
    w.on_moved(SimpleNamespace(src_path=str(tmp_path / "x.tmp"),
                               dest_path=str(tmp_path / "bluetooth.conf")))
    assert adapter.done.wait(2)


def test_a_failure_is_logged_and_the_next_change_still_applies(tmp_path):
    adapter = FakeAdapter(fail=1)
    w = watcher(tmp_path, adapter)
    w.on_modified(modified(tmp_path / "bluetooth.conf"))
    assert adapter.done.wait(2)
    time.sleep(0.1)
    assert len(w.config_manager.logged) == 1
    adapter.done.clear()
    w.on_modified(modified(tmp_path / "bluetooth.conf"))
    assert adapter.done.wait(2)
    assert adapter.updates == 2
