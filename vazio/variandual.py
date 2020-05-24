import enum
import functools

from vazio.protocol.multigauge import encode_request, decode_reply, Command, Channel


class Enum(enum.Enum):
    @classmethod
    def encode(cls, value):
        return cls(value).value


class IntFlag(enum.IntFlag):
    @classmethod
    def decode(cls, data):
        return cls(ord(data))


class Remote(Enum):
    Local = "0"
    Remote = "1"
    Serial = "2"


class HighVoltage(Enum):
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


class Unit(Enum):
    torr = "0"
    mbar = "1"
    pascal = "2"


class HVDeviceNumber(Enum):
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


class GaugeDeviceNumber(Enum):
    Convector = "0"
    MiniBA = "1"
    ColdCathode = "2"


class SerialDeviceNumber(Enum):
    RS232 = "0"
    RS485 = "1"


class InterlockStatus(IntFlag):
    FrontPanel = 2
    HV1Remote = 4
    HV1Cable = 8
    HV2Remote = 64
    HV2Cable = 128


class FixedStep(Enum):
    Fixed = "0"
    Step = "1"


class StartProtect(Enum):
    Start = "0"
    Protect = "1"


class Polarity(Enum):
    Negative = "0"
    Positive = "1"


class RemoteOutput(IntFlag):
    HighVoltageEnable = 1
    SetPoint2Active = 2
    SetPoint1Active = 4
    InterlockActive = 8
    HighVoltageFault = 16
    SerialMode = 32
    ProtectMode = 64


class RemoteInput(IntFlag):
    StepMode = 4
    RemoteMode = 8
    ProtectMode = 16
    HVOutputEnable = 32
    HVConfirm = 64
    RemoteInterlock = 128


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


def nop(v):
    return v


class Value:
    def __init__(self, command, decode=nop, encode=None):
        self.command = command
        self.decode = decode
        self.encode = encode

    def _read(self, ctrl, channel):
        request = encode_request(channel, self.command, "?")
        reply = ctrl.conn.write_readline(request)
        *_, value = decode_reply(reply)
        return self.decode(value)

    def _write(self, ctrl, channel, value):
        if self.encode is None:
            raise AttributeError(
                "can't set: {.name} on {.name}".format(self.command, channel)
            )
        request = encode_request(channel, self.command, self.encode(value))
        ctrl.conn.write_readline(request)

    def __get__(self, ctrl, owner=None):
        return self._read(ctrl, Channel.NoChannel)

    def __set__(self, ctrl, value):
        self._write(ctrl, Channel.NoChannel, value)


class ChannelValue(Value):
    def __get__(self, channel, owner=None):
        return self._read(channel.ctrl, channel.channel)

    def __set__(self, channel, value):
        self._write(channel.ctrl, channel.channel, value)


class BaseChannel:

    device_type = ChannelValue(Command.DeviceType)
    error_status = ChannelValue(Command.ErrorStatus, decode=ControllerErrors.get)

    def __init__(self, channel, ctrl=None):
        self.channel = channel
        self.ctrl = ctrl

    def __get__(self, ctrl, owner=None):
        ch = ctrl._channels.get(self.channel)
        if ch is None:
            ch = type(self)(self.channel, ctrl)
            ctrl._channels[self.channel] = ch
        return ch


def EnumCV(cmd, enu, **kwargs):
    kwargs.setdefault("decode", enu)
    if hasattr(enu, "encode"):
        kwargs.setdefault("encode", enu.encode)
    return ChannelValue(cmd, **kwargs)


IntCV = functools.partial(ChannelValue, encode=int, decode=str)
IntCVRO = functools.partial(ChannelValue, decode=int)
FloatCV = functools.partial(ChannelValue, decode=float, encode=str)
FloatCVRO = functools.partial(ChannelValue, decode=float)


class HV(BaseChannel):

    high_voltage = EnumCV(Command.HighVoltage, HighVoltage)
    device_number = EnumCV(Command.DeviceNumber, HVDeviceNumber)

    voltage = IntCVRO(Command.Voltage)
    current = FloatCVRO(Command.Current)
    pressure = FloatCVRO(Command.Pressure)

    fixed_step = EnumCV(Command.FixedStep, FixedStep)
    start_protect = EnumCV(Command.StartProtect, StartProtect)
    polarity = EnumCV(Command.Polarity, Polarity)

    voltage_max = IntCV(Command.VoltageMax)  # [3000, 7000] step 100 (V)
    current_max = IntCV(Command.CurrentMax)  # [100, 400] step 10 (mA)
    power_max = IntCV(Command.PowerMax)  # [100, 400] step 10 (W)
    current_protect = IntCV(Command.CurrentProtect)  # [10, 100] step 10 (mA)
    voltage_step1 = IntCV(Command.VoltageStep1)  # [3000, 7000] step 100 (V)
    current_step1 = FloatCV(Command.CurrentStep1)  # [1e-9, 1e1] (A)
    voltage_step2 = IntCV(Command.VoltageStep2)  # [3000, 7000] step 100 (V)
    current_step2 = FloatCV(Command.CurrentStep2)  # [1e-9, 1e1] (A)
    set_point1 = FloatCV(Command.SetPoint1)  # [1e-9, 1e1] (torr) (> sp2)
    set_point2 = FloatCV(Command.SetPoint2)  # [1e-9, 1e1] (torr)
    remote_output = ChannelValue(Command.RemoteOutput, decode=RemoteOutput.decode)
    remote_input = ChannelValue(Command.RemoteInput, decode=RemoteInput.decode)


class Gauge(BaseChannel):

    device_number = ChannelValue(Command.DeviceNumber, decode=GaugeDeviceNumber)
    pressure = ChannelValue(Command.Pressure, decode=float)


class Serial(BaseChannel):

    device_number = ChannelValue(Command.DeviceNumber, decode=SerialDeviceNumber)


class VarianDual:
    """
    VarianDual controller based on MultiGauge protocol

    conn: any object with write_readline (should be configured
          with eol='\r')
    """

    remote = Value(Command.Remote, decode=Remote, encode=Remote.encode)
    unit = Value(Command.Unit, decode=Unit, encode=Unit.encode)

    error_status = Value(Command.ErrorStatus, decode=ControllerErrors.get)
    interlock_status = Value(Command.InterlockStatus, decode=InterlockStatus.decode)
    ctrl_firmware_version = Value(Command.MicroControllerFirmwareVersion)
    dsp_firmware_version = Value(Command.DSPFirmwareVersion)

    hv1 = HV(Channel.HighVoltage1)
    hv2 = HV(Channel.HighVoltage2)
    gauge1 = Gauge(Channel.Gauge1)
    gauge2 = Gauge(Channel.Gauge2)
    serial = Serial(Channel.Serial)

    serial_config = Value(
        Command.SerialConfig,
        decode=lambda v: v == "1",
        encode=lambda v: "1" if v else "0",
    )

    def __init__(self, conn):
        self.conn = conn
        self._channels = {}

        # TODO:
        # on connect:
        # - set ACK reply mode
        # - set unit to mbar
