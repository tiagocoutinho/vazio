"""
MultiGauge protocol

MultiGauge Compatible Protocol

header command = '#'
header response = '>'
terminator = '\r'

Host to controller command format:
[header command(1)] [channel(1)] [command(2)] [data] [terminator(1)]

Controller to Host reply format:
[header response(1)] [channel(1)] [command(2)] [data] [terminator(1)]
"""

__version__ = "0.0.1"

import enum
import collections


HEADER_REQ = "#"
HEADER_REP = ">"


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
    DspFirmwareVersion = "04"
    DeviceNumber = "01"
    DeviceType = "11"
    Voltage = "07"
    Current = "8"
    Pressure = "2"
    ErrorStatus = "19"
    SerialReset = "06"
    RemoteError = "12"
    InterlockStatus = "13"

    @staticmethod
    def _size():
        return 2


def encode(header, channel, command, data):
    channel = Channel.decode(channel).value
    command = Command.decode(command).value
    if isinstance(data, bytes):
        data = data.decode()
    return '{}{}{}{}\r'.format(header, channel, command, data).encode()


def decode(data):
    data = data.decode()
    assert data[-1] == '\r'
    return (
        data[0],
        Channel.decode(data[1:2]),
        Command.decode(data[2:4]),
        data[4:-1]
    )


Packet = collections.namedtuple('Packet', 'header, channel, command, data')


def encode_packet(packet):
    return encode(*packet)


def decode_packet(data):
    return Packet(*decode(data))


Packet.encode = encode_packet


Packet.decode = staticmethod(decode_packet)


def Request(channel, command, data):
    return Packet(HEADER_REQ, channel, command, data)


def Reply(channel, command, data):
    return Packet(HEADER_REP, channel, command, data)
