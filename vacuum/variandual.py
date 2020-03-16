import enum
import functools

from vacuum.protocol.multigauge import encode_request, decode_reply, Command, Channel


class Remote(enum.Enum):
    Local = "0"
    Remote = "1"
    Serial = "2"

    @classmethod
    def encode(cls, value):
        return cls(value).value


class HighVoltage(enum.Enum):
    Off = "0"
    OnStartStep = "1"
    On = "1"
    OnStartFixed = "2"
    OnProtectStep = "3"
    OnProtectFixed = "4"
    OffPanelInterlock = "-3"
    OffRemoteInterlock = "-4"
    OffHVOverTemperature = "-8"
    OffRemoteFault = "-7"
    OffHVProtect = "-6"
    OffHVShortCircuit = "-5"

    @classmethod
    def encode(cls, value):
        return cls(value).value


class Unit(enum.Enum):
    torr = "0"
    mbar = "1"
    pascal = "2"

    @classmethod
    def encode(cls, value):
        return cls(value).value


class HVDeviceNumber(enum.Enum):
    Spare = "0"
    SCTr_500 = "1"
    SCTr_300 = "2"
    SCTr_150 = "3"
    SCTr_75_55_40 = "4"
    SCTr_20 = "4"
    DiodeND_500 = "6"
    DiodeND_300 = "7"
    DiodeND_150 = "8"
    DiodeND_75_55_40 = "9"
    DiodeND_20 = ":"


class GaugeDeviceNumber(enum.Enum):
    Convector = "0"
    MiniBA = "1"
    ColdCathode = "2"


class SerialDeviceNumber(enum.Enum):
    RS232 = "0"
    RS485 = "1"


ProtocolErrors = {
    # If incongruencies are detected in the composition of the
    # data packet sent to the Dual controller (in other words a
    # correct reception but an incorrect data format), the Dual
    # controller will reply with an error code identified by the
    # .!. (21h) command according to the following table.
    "1": "Reserved (checksum error)",
    "2": "Non existent command code",
    "3": "Channel not valid for the selected command",
    "4": "Write mode not allowed for the selected command",
    "5": "Unvalid or non-congruent data transmitted",
    "6": "Write value exceeding the allowed limits or step not allowed",
    "7": "Data format not recognized on the protocols implemented",
    "8": "Write not allowed to channel ON",
    "9": "Write not allowed to channel OFF",
    ":": "Write allowed in Serial Configuration Mode only",
}


ControllerErrors = {
    # Value  Error type  Error reference
    # High Voltage errors
    "HV": {
        "1": "High Voltage off due to front panel interlock activation Panel Interlock",
        "2": "High Voltage off due to Remote I/O interlock activation Remote Interlock",
        "3": "High Voltage off due to Cable HV interlock activation Cable Interlock",
        "4": "Dual fault HV not found",
        "5": "High Voltage off due to a general DSP determined fault HV Fault",
        "6": "High Voltage off due to an HV module overtemperature determined by the DSP HV Overtemperature",
        "7": "Remote I/O card not present or faulty R.I/O not found",
        "8": "Remote I/O card present, but faulty R.I/O fault",
        "9": "High Voltage off due to the protect function activation Protect",
        "10": "High Voltage off due to shortcircuit protection activation Short Circuit",
        "11": "High Voltage off due to an HV module overvoltage or overcurrent determined by the DSP Over Volt/Curr",
        "12": "High Voltage off due to the zero measurement protection activation Zero Meas MiniGauge errors ",
    },
    "MG": {
        "1": "MiniGauge off due to front panel interlock activation Panel Interlock",
        "2": "The selected Minigauge was not recognized Gauge not found",
        "3": "The Minigauge is signaling a Fault condition Gauge fault",
        "4": "The selected Minigauge was disconnected Gauge not connected System errors ",
    },
    "SW": {
        "1": "RAM failure: RAM diagnostics error Software Error",
        "2": "config register: incorrect value in the uC 68HC11 configuration register Software Error",
        "3": "test mode: invalid uC 68HC11 operating mode Software Error",
        "4": "copyright: violation of the signature in the ROM or the ROM was corrupted Software Error",
        "5": "eeprom fault: checksum or non-volatile memory write errors. Factory defaults are automatically loaded Software Error",
        "6": "version number: incompatible uC and Dsp versions Software Error",
        "7": "hv dsp not found: the Dsp does not respond during the uC initialization phase Software Error",
        "8": "dsp fault: the Dsp does not respond during normal operation Software Error ",
        "9": "invalid option: option card not configured correctly Software Error ",
        "10": "unknow option: generic execution error Software Error",
    },
}


class Value:
    def __init__(
        self, command, channel=Channel.NoChannel, decode=lambda x: x, encode=lambda x: x
    ):
        self.command = command
        self.channel = channel
        self.decode = decode
        self.encode = encode
        self._request = encode_request(channel, command, "?")

    def __get__(self, ctrl, owner=None):
        reply = ctrl.conn.write_readline(self._request)
        *_, value = decode_reply(reply)
        return self.decode(value)

    def __set__(self, ctrl, value):
        if self.encode is None:
            raise AttributeError(
                "can't set: {.name} on {.name}".format(self.command, self.channel)
            )
        request = encode_request(self.channel, self.command, self.encode(value))
        ctrl.conn.write_readline(request)


Int = functools.partial(Value, decode=int)
IntRO = functools.partial(Int, encode=None)
Float = functools.partial(Value, decode=float)
FloatRO = functools.partial(Float, encode=None)


class VarianDual:
    """
    VarianDual controller based on MultiGauge protocol

    conn: any object with write_readline (should be configured
          with eol='\r')
    """

    remote = Value(Command.Remote, decode=Remote, encode=Remote.encode)

    hv1 = Value(
        Command.HighVoltage,
        Channel.HighVoltage1,
        decode=HighVoltage,
        encode=HighVoltage.encode,
    )
    hv2 = Value(
        Command.HighVoltage,
        Channel.HighVoltage2,
        decode=HighVoltage,
        encode=HighVoltage.encode,
    )

    unit = Value(Command.Unit, decode=Unit, encode=Unit.encode)

    ctrl_firmware_version = Value(
        Command.MicroControllerFirmwareVersion, Channel.NoChannel, encode=None
    )
    dsp_firmware_version = Value(
        Command.DSPFirmwareVersion, Channel.NoChannel, encode=None
    )

    hv1_device_number = Value(
        Command.DeviceNumber, Channel.HighVoltage1, encode=HVDeviceNumber
    )
    hv2_device_number = Value(
        Command.DeviceNumber, Channel.HighVoltage2, encode=HVDeviceNumber
    )
    gauge1_device_number = Value(
        Command.DeviceNumber, Channel.Gauge1, encode=GaugeDeviceNumber
    )
    gauge2_device_number = Value(
        Command.DeviceNumber, Channel.Gauge2, encode=GaugeDeviceNumber
    )
    serial_device_number = Value(
        Command.DeviceNumber, Channel.Serial, encode=SerialDeviceNumber
    )

    hv1_device_type = Value(Command.DeviceNumber, Channel.HighVoltage1)
    hv2_device_type = Value(Command.DeviceNumber, Channel.HighVoltage2)
    gauge1_device_type = Value(Command.DeviceNumber, Channel.Gauge1)
    gauge2_device_type = Value(Command.DeviceNumber, Channel.Gauge2)
    serial_device_type = Value(Command.DeviceNumber, Channel.Serial)

    hv1_current = FloatRO(Command.Current, Channel.HighVoltage1)
    hv2_current = FloatRO(Command.Current, Channel.HighVoltage2)

    hv1_voltage = IntRO(Command.Voltage, Channel.HighVoltage1)
    hv2_voltage = IntRO(Command.Voltage, Channel.HighVoltage2)

    hv1_pressure = FloatRO(Command.Pressure, Channel.HighVoltage1)
    hv2_pressure = FloatRO(Command.Pressure, Channel.HighVoltage2)

    hv1_error_status = Value(Command.ErrorStatus, Channel.HighVoltage1)

    def __init__(self, conn):
        self.conn = conn
