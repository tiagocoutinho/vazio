"""
VarianDUAL simulator helper classes

To create a VarianDUAL device use the following configuration as
a starting point:

.. code-block:: yaml

    devices:
    - class: VarianDual
      package: vazio.simulator.variandual
      transports:
      - type: serial
        url: /tmp/variandual1

A simple *nc* client can be used to connect to the instrument:

    $ nc 0 10001

"""
import random

from sinstruments.simulator import BaseDevice

from ..variandual import Remote, HVDeviceNumber, GaugeDeviceNumber, SerialDeviceNumber
from ..protocol.multigauge import Channel, Command, encode_reply, HEADER_REQ


def funiform(a, b):
    return lambda: '{:7.1E}'.format(random.uniform(a, b))


def iuniform(a, b):
    return lambda: '{:05d}'.format(random.randint(a, b))


state = {
    Command.Remote: {
        Channel.NoChannel: Remote.Local,
    },
    Command.RemoteError: {
        Channel.NoChannel: '0',
    },
    Command.InterlockStatus: {
        Channel.NoChannel: b'\x00',
    },
    Command.MicroControllerFirmwareVersion: {
        Channel.NoChannel: "VPo 1 0 24/04/98"
    },
    Command.DSPFirmwareVersion: {
        Channel.NoChannel: "VPd 1 0 24/04/98"
    },
    Command.Voltage: {
        Channel.HighVoltage1: iuniform(30, 50),
        Channel.HighVoltage2: iuniform(90, 120),
    },
    Command.Current: {
        Channel.HighVoltage1: funiform(5e-1, 9e2),
        Channel.HighVoltage2: funiform(5e-1, 9e2),
    },
    Command.Pressure: {
        Channel.HighVoltage1: funiform(5e-9, 9e-3),
        Channel.HighVoltage2: funiform(5e-9, 9e-3),
        Channel.Gauge1: funiform(5e-9, 9e-3),
        Channel.Gauge2: funiform(5e-9, 9e-3),
    },
    Command.DeviceType: {
        Channel.HighVoltage1: HVDeviceNumber.SCTr_300,
        Channel.HighVoltage2: HVDeviceNumber.DiodeND_150,
        Channel.Gauge1: GaugeDeviceNumber.MiniBA,
        Channel.Gauge2: GaugeDeviceNumber.ColdCathode,
        Channel.Serial: SerialDeviceNumber.RS232
    },
    Command.ErrorStatus: {
        Channel.NoChannel: "0",
        Channel.HighVoltage1: "0",
        Channel.HighVoltage2: "0",
        Channel.Gauge1: "0",
        Channel.Gauge2: "0",
        Channel.Serial: "0",
    },
    Command.HighVoltage: {
        Channel.HighVoltage1: "0",  # 0-off, 1-start/step, 2-start/fixed, ...
        Channel.HighVoltage2: "1"
    },
    Command.FixedStep: {
        Channel.HighVoltage1: "0",  # 0-fixed, 1-step
        Channel.HighVoltage2: "1"
    },
    Command.StartProtect: {
        Channel.HighVoltage1: "0",  # 0-start, 1-protect
        Channel.HighVoltage2: "1"
    },
    Command.CurrentProtect: {
        Channel.HighVoltage1: "20",  # [10:100:10] (mA)
        Channel.HighVoltage2: "50"
    },
    Command.SetPoint1: {
        Channel.HighVoltage1: "2.3E-7",  # [1.0E-9:1.0E1] (Torr)
        Channel.HighVoltage2: "5.1E-2"
    },
    Command.SetPoint2: {
        Channel.HighVoltage1: "4.1E-8",  # [1.0E-9:1.0E1] (Torr)
        Channel.HighVoltage2: "7.2E-3"
    }
}


class VarianDual(BaseDevice):

    DEFAULT_NEWLINE = b"\r"

    def handle_line(self, line):
        self._log.debug("processing line %r", line)
        line = line.decode()
        assert line.startswith(HEADER_REQ)
        channel, command = Channel(line[1]), Command(line[2:4])
        is_query = line[-1] == '?'
        if is_query:
            data = state[command][channel]
        else:
            # TODO!
            pass
        if callable(data):
            data = data()
        reply = encode_reply(channel, command, data)
        self._log.debug("reply %r", reply)
        return reply
