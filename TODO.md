# TODO

## Agent rejects every RequestAuthorization

`Agent.RequestAuthorization` in `hifiberry_bluetooth/Agent.py` asks for
confirmation with `input("Authorize? (yes/no): ")`. The service runs as a
daemon without a terminal, so `input()` hits EOF and the request is rejected.
bluetoothd calls this method for incoming Just Works pairings that need
authorization, and for re-pairing when `JustWorksRepairing = confirm` is set,
so `confirm` cannot work today. Decide what the agent should do (accept, or
accept only while pairable) and implement it without `input()`; then
`confirm` becomes a real alternative to the `always` set by postinst.

## bluez upgrades and the modified main.conf

postinst writes `JustWorksRepairing = always` into `/etc/bluetooth/main.conf`,
a conffile of bluez. A bluez upgrade that ships a changed `main.conf` will
then raise a dpkg conffile prompt. The update runner in configurator
(`configurator/extensions/runner.py`) only sets `DEBIAN_FRONTEND=noninteractive`,
which does not answer that prompt, so such an upgrade would fail. Missing:
pass `-o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold`
on the apt calls there (and on any other system-update path), which keeps
local changes to every conffile, not just this one.
