import pytest

from vacuum.protocol.multigauge import HEADER_REQ, ACK, Command, Channel, encode_reply
from vacuum.variandual import VarianDual, Remote, HighVoltage, Unit


class Connection:

    remote = "0"
    hv1 = "0"
    hv2 = "1"
    unit = "0"
    hv1_voltage = "14"
    hv2_voltage = "15"

    def write_readline(self, data):
        assert type(data) == bytes
        data = data.decode()
        assert data[0] == HEADER_REQ
        assert data[-1] == "\r"
        channel, cmd = Channel(data[1]), Command(data[2:4])
        if data[-2] == '?':
            if cmd == Command.Remote:
                assert channel == Channel.NoChannel
                data = self.remote
            elif cmd == Command.Unit:
                assert channel == Channel.NoChannel
                data = self.unit
            elif cmd == Command.Voltage:
                if channel == Channel.HighVoltage1:
                    data = self.hv1_voltage
                elif channel == Channel.HighVoltage2:
                    data = self.hv2_voltage
            elif cmd == Command.HighVoltage:
                if channel == Channel.HighVoltage1:
                    data = self.hv1
                elif channel == Channel.HighVoltage2:
                    data = self.hv2
            return encode_reply(channel, cmd, data)
        else:
            if cmd == Command.Remote:
                assert channel == Channel.NoChannel
                self.remote = data[-2]
            elif cmd == Command.Unit:
                assert channel == Channel.NoChannel
                self.unit = data[-2]
            elif cmd == Command.HighVoltage:
                if channel == Channel.HighVoltage1:
                    self.hv1 = data[-2]
                elif channel == Channel.HighVoltage2:
                    self.hv2 = data[-2]
            return (ACK + '\r').encode()


def test_variandual():
    conn = Connection()

    ctrl = VarianDual(conn)

    assert ctrl.remote == Remote.Local

    ctrl.remote = Remote.Remote

    assert ctrl.remote == Remote.Remote
    assert conn.remote == "1"

    assert ctrl.hv1 == HighVoltage.Off
    assert ctrl.hv2 == HighVoltage.On

    ctrl.hv1 = HighVoltage.On
    assert ctrl.hv1 == HighVoltage.On
    assert conn.hv1 == "1"

    assert ctrl.hv1_voltage == 14
    assert ctrl.hv2_voltage == 15

    with pytest.raises(AttributeError):
        ctrl.hv1_voltage = 55

    with pytest.raises(AttributeError):
        ctrl.hv2_voltage = 55

    assert ctrl.unit == Unit.torr
    ctrl.unit = Unit.mbar
    assert ctrl.unit == Unit.mbar
    assert conn.unit == "1"
