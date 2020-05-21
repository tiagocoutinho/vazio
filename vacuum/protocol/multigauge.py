"""
MultiGauge protocol

header command = '#'
header response = '>'
terminator = '\r'

Host to controller command format:
[header command(1)] [channel(1)] [command(2)] [data] [terminator(1)]

Controller to Host reply format:
[header response(1)] [channel(1)] [command(2)] [data] [terminator(1)]
"""

import enum


HEADER_REQ = "#"
HEADER_REP = ">"
ACK = '\x06'


class Enum(enum.Enum):

    @staticmethod
    def _size():
        return 1

    @classmethod
    def decode(cls, data):
        if isinstance(data, bytes):
            data = data.decode()
        elif isinstance(data, int):
            data = '{{:0{}}}'.format(cls._size()).format(data)
        return cls(data)


class Channel(Enum):
    NoChannel = "0"
    HighVoltage1 = "1"
    HighVoltage2 = "2"
    Gauge1 = "3"
    Gauge2 = "4"
    Serial = "5"


class Command(Enum):
    Remote = "10"
    HighVoltage = "30"
    Unit = "03"
    MicroControllerFirmwareVersion = "05"
    DSPFirmwareVersion = "04"
    DeviceNumber = "01"
    DeviceType = "11"
    Voltage = "07"
    Current = "08"
    Pressure = "02"
    ErrorStatus = "19"
    SerialReset = "06"
    RemoteError = "12"
    InterlockStatus = "13"
    FixedStep = "60"
    StartProtect = "61"
    Polarity = "62"
    VoltageMax = "63"
    CurrentMax = "64"
    PowerMax = "65"
    CurrentProtect = "66"
    VoltageStep1 = "67"
    CurrentStep1 = "68"
    VoltageStep2 = "69"
    CurrentStep2 = "70"
    SetPoint1 = "71"
    SetPoint2 = "72"
    RemoteOutput = "73"
    RemoteInput = "74"
    SerialConfig = "80"

    @staticmethod
    def _size():
        return 2


def encode(header, channel, command, data):
    channel = Channel.decode(channel).value
    command = Command.decode(command).value
    if isinstance(data, bytes):
        data = data.decode()
    if isinstance(data, enum.Enum):
        data = data.value
    return '{}{}{}{}\r'.format(header, channel, command, data).encode()


def encode_request(channel, command, data):
    return encode(HEADER_REQ, channel, command, data)


def encode_reply(channel, command, data):
    return encode(HEADER_REP, channel, command, data)


def decode(data):
    data = data.decode()
    assert data[-1] == '\r'
    return (
        data[0],
        Channel.decode(data[1:2]),
        Command.decode(data[2:4]),
        data[4:-1]
    )


def decode_reply(data):
    result = decode(data)
    assert result[0] == HEADER_REP
    return result
