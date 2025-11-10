import dbus
import dbus.service

class Agent(dbus.service.Object):
    BUS_NAME = "org.bluez"
    AGENT_IFACE = "org.bluez.Agent1"
    DEVICE_IFACE = "org.bluez.Device1"

    """
    Initialize a new BlueZ Bluetooth Agent object.

    This constructor registers the Agent on the provided D-Bus connection
    and exposes its methods to the BlueZ daemon (`bluetoothd`) via the
    `org.bluez.Agent1` interface. The agent is used to handle pairing,
    authentication, and authorization requests from Bluetooth devices.

    :param bus: The D-Bus connection (typically a `dbus.SystemBus` instance) on which the Agent should be exported.
    :type bus: dbus.bus.BusConnection

    :param path: The D-Bus object path at which this Agent will be exported. For example, `/my/app/agent`.
    :type path: str

    :raises dbus.exceptions.DBusException: If exporting the object to D-Bus fails.
    """
    def __init__(self, bus, path):
        super().__init__(bus, path)
        self.bus = bus

    """
    This method gets called when **bluetoothd** unregisters the agent

    An agent can use it to do cleanup tasks. There is no need to unregister
    the agent, because when this method gets called it has already been unregistered.
    """
    @dbus.service.method(AGENT_IFACE, in_signature="", out_signature="")
    def Release(self):
        print("Release")

    """
    This method gets called when **bluetoothd** needs to get the passkey for an
    authentication.

    The return value should be a string of 1-16 characters length. The string can be
    alphanumeric.

    :param device: D-Bus object path to the bluetooth device that is requesting pairing
    :type device: dbus.ObjectPath

    :raises org.bluez.Error.Rejected: If the request is rejected.
    :raises org.bluez.Error.Canceled: If the request is canceled.

    :returns: The set pin code in the code, currently set to "0000".
    :rtype: str
    """
    @dbus.service.method(AGENT_IFACE, in_signature='o', out_signature='s')
    def RequestPinCode(self, device):
        print(f'RequestPinCode {device}')
        pincode = "0000"
        return pincode

    """
    This method gets called when **bluetoothd** needs to display a pin code 
    for an authentication.

    An empty reply should be returned. When the pin code needs no longer to be
    displayed, the `Cancel` method of the agent will be called.

    This is used during the pairing process of keyboards that don't support
    Bluetooth 2.1 Secure Simple Pairing, in contrast to `DisplayPasskey` which is used
    for those that do.

    This method will only ever be called once since older keyboards do not support
    typing notification.

    Note that the PIN will always be a 6-digit number, zero-padded to 6 digits. This
    is for harmony with the later specification.

    :param device: D-Bus object path to the bluetooth device that is requesting pairing
    :type device: dbus.ObjectPath
    :param passkey: The passkey as a string
    :type passkey: dbus.String

    :raises org.bluez.Error.Rejected: If the request is rejected.
    :raises org.bluez.Error.Canceled: If the request is canceled.
    """
    @dbus.service.method(AGENT_IFACE, in_signature="os", out_signature="")
    def DisplayPinCode(self, device, pincode):
        print("DisplayPinCode (%s, %s)" % (device, pincode))

    """
    This method gets called when **bluetoothd** needs to get the passkey for an
    authentication.

    The return value should be a numeric value between 0-999999.

    :param device: D-Bus object path to the bluetooth device that is requesting pairing
    :type device: dbus.ObjectPath

    :raises org.bluez.Error.Rejected: If the request is rejected.
    :raises org.bluez.Error.Canceled: If the request is canceled.

    :returns: The entered passkey
    :rtype: dbus.UInt32
    """
    @dbus.service.method(AGENT_IFACE, in_signature="o", out_signature="u")
    def RequestPasskey(self, device):
        print("RequestPasskey (%s)" % (device))
        self.set_trusted(device)
        passkey = input("Enter passkey: ")
        return dbus.UInt32(passkey)

    """
    This method gets called when **bluetoothd** needs to display a passkey for
    an authentication.

    The entered parameter indicates the number of already typed keys on the remote
    side.

    An empty reply should be returned. When the passkey needs no longer to be
    displayed, the `Cancel` method of the agent will be called.

    During the pairing process this method might be called multiple times to update
    the entered value.

    Note that the passkey will always be a 6-digit number, so the display should be
    zero-padded at the start if the value contains less than 6 digits.


    :param device: D-Bus object path to the bluetooth device that is requesting pairing
    :type device: dbus.ObjectPath
    :param passkey: The passkey that is given
    :type passkey: dbus.UInt32
    :param entered: The number of already typed keys on the remote side.
    :type entered: dbus.UInt16
    """
    @dbus.service.method(AGENT_IFACE, in_signature="ouq", out_signature="")
    def DisplayPasskey(self, device, passkey, entered):
        print("DisplayPasskey (%s, %06u entered %u)" %
              (device, passkey, entered))
        dbus.UInt16

    """
    This method gets called when **bluetoothd** needs to confirm a passkey for
    an authentication.

    To confirm the value, it should return an empty reply or an error if
    the passkey is invalid.

    Note that the passkey will always be a 6-digit number, so the display should be
    zero-padded at the start if the value contains less than 6 digits.

    :param device: D-Bus object path to the bluetooth device that is requesting pairing
    :type device: dbus.ObjectPath
    :param passkey: The passkey that should be displayed
    :type passkey: dbus.UInt32

    :raises org.bluez.Error.Rejected: If the request is rejected.
    :raises org.bluez.Error.Canceled: If the request is canceled.
    """
    @dbus.service.method(AGENT_IFACE, in_signature="ou", out_signature="")
    def RequestConfirmation(self, device, passkey):
        print("RequestConfirmation (%s, %06d)" % (device, passkey))
        self.set_trusted(device)
        return

    """
    This method gets called to request the user to authorize an incoming pairing
    attempt which would in other circumstances trigger the just-works model, or when
    the user plugged in a device that implements cable pairing. In the latter case,
    the device would not be connected to the adapter via Bluetooth yet.

    :param device: D-Bus object path to the bluetooth device that is requesting pairing
    :type device: dbus.ObjectPath

    :raises org.bluez.Error.Rejected: If the request is rejected.
    :raises org.bluez.Error.Canceled: If the request is canceled.
    """
    @dbus.service.method(AGENT_IFACE, in_signature="o", out_signature="")
    def RequestAuthorization(self, device):
        print("RequestAuthorization (%s)" % (device))
        auth = input("Authorize? (yes/no): ")
        if (auth == "yes"):
            return
        raise Rejected("Pairing rejected")

    """
    This method gets called when **bluetoothd** needs to authorize a
    connection/service request.

    :param device: D-Bus object path to the bluetooth device that is requesting pairing
    :type device: dbus.ObjectPath
    :param uuid: The uuid string of the connected device
    :type uuid: dbus.String

    :raises org.bluez.Error.Rejected: If the request is rejected.
    :raises org.bluez.Error.Canceled: If the request is canceled.
    """
    @dbus.service.method(AGENT_IFACE, in_signature="os", out_signature="")
    def AuthorizeService(self, device, uuid):
        print(f"AuthorizeService ({device}, {uuid})")
        return

    """
    This method gets called to indicate that the agent request failed before a reply.
    """
    @dbus.service.method(AGENT_IFACE, in_signature="", out_signature="")
    def Cancel(self):
        print("Cancelled")
        return

    """
    This method sets a device to the trusted list of devices.
    """
    def set_trusted(self, path):
        props = dbus.Interface(self.bus.get_object(self.BUS_NAME, path), dbus.PROPERTIES_IFACE)
        props.Set(self.DEVICE_IFACE, "Trusted", True)
