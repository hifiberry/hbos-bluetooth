# Config

## Syntax
**hifiberry-bluetooth** uses the [toml](https://toml.io/en/) format.


## Location
**hifiberry-bluetooth** creates the config file for you.
The file can be found under `~/.config/hifiberry/bluetooth.conf`.


## Example config
An example config will be created if you delete the existing file.
Alternatively, you can look at the example below.

```toml
[Bluetooth]
capability=NoInputNoOutput

discoverable=true
discoverable_timeout=0

pairable=true
pairable_timeout=0
```


## Bluetooth
In this section of the file, the bluetooth settings are defined.


### Capability
This is how you connect to the device.

If you, for example, want to automatically connect the device
without any confirmation

Possible options:

- `capability=DisplayOnly`
- `capability=KeyboardYesNo`
- `capability=KeyboardDisplay`
- `capability=KeyboardOnly`
- `capability=NoInputNoOutput`

#### `DisplayOnly`, `DisplayYesNo` and `KeyboardDisplay`
The user gets displayed a code from the RPi
and needs to type the code into
the device that wants to connect to the RPi (for example a phone).

**for developers:**
Both use the `RequestConfirmation()` function in [Agent.py](../src/Agent.py).


#### `KeyboardOnly`
The user gets displayed a code on
the device that wants to connect to the RPi (for example a phone).
He then needs to type in that code into the RPi.

**for developers:**
This uses the function `RequestPasskey()` function in [Agent.py](../src/Agent.py).

#### `NoInputNoOutput`
The user doesn't need to confirm anything.
If he wants to connect to the RPi, the device (for example a phone)
will automatically do that for him.


### Discoverable
Should the RPi be discoverable?

Possible options:

- `discoverable=True`
- `discoverable=Falsee`

### Discoverable timeout
The discoverable timeout in seconds. A value of zero means that the timeout is
disabled and it will stay in discoverable/limited mode forever.

Valid options:
- `discoverable_timeout=0`
- `discoverable_timeout=160`

### Pairable
Switch an RPi to pairable or non-pairable.

Possible options:
- `pairable=True`
- `pairable=False`

### Pairable timeout
The pairable timeout in seconds. A value of zero means that the timeout is
disabled and it will stay in pairable mode forever.

Valid options:
- `pairable_timeout=0`
- `pairable_timeout=160`
