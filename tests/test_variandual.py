import pytest

from vacuum.protocol.multigauge import HEADER_REQ, ACK, Command, Channel, encode_reply
from vacuum.variandual import (
    VarianDual,
    Remote,
    HighVoltage,
    Unit,
    FixedStep,
    InterlockStatus,
)


class Connection:

    remote = "0"
    ctrl_firmware_version = "VPo 1 0 24/04/98"
    dsp_firmware_version = "VPd 1 0 24/04/98"
    serial_config = "0"
    interlock_status = "\x00"
    hv1 = "0"
    hv2 = "1"
    unit = "0"
    hv1_voltage = "14"
    hv2_voltage = "15"

    hv1_fixed_step = "0"
    hv2_fixed_step = "1"

    def write_readline(self, data):
        assert type(data) == bytes
        data = data.decode()
        assert data[0] == HEADER_REQ
        assert data[-1] == "\r"
        channel, cmd = Channel(data[1]), Command(data[2:4])
        if data[-2] == "?":
            if cmd == Command.Remote:
                assert channel == Channel.NoChannel
                data = self.remote
            elif cmd == Command.Unit:
                assert channel == Channel.NoChannel
                data = self.unit
            elif cmd == Command.MicroControllerFirmwareVersion:
                assert channel == Channel.NoChannel
                data = self.ctrl_firmware_version
            elif cmd == Command.DSPFirmwareVersion:
                assert channel == Channel.NoChannel
                data = self.dsp_firmware_version
            elif cmd == Command.SerialConfig:
                assert channel == Channel.NoChannel
                data = self.serial_config
            elif cmd == Command.InterlockStatus:
                assert channel == Channel.NoChannel
                data = self.interlock_status

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
            elif cmd == Command.FixedStep:
                if channel == Channel.HighVoltage1:
                    data = self.hv1_fixed_step
                elif channel == Channel.HighVoltage2:
                    data = self.hv2_fixed_step
            return encode_reply(channel, cmd, data)
        else:
            if cmd == Command.Remote:
                assert channel == Channel.NoChannel
                self.remote = data[-2]
            elif cmd == Command.Unit:
                assert channel == Channel.NoChannel
                self.unit = data[-2]
            elif cmd == Command.SerialConfig:
                assert channel == Channel.NoChannel
                self.serial_config = data[-2]

            elif cmd == Command.HighVoltage:
                if channel == Channel.HighVoltage1:
                    self.hv1 = data[-2]
                elif channel == Channel.HighVoltage2:
                    self.hv2 = data[-2]
            return (ACK + "\r").encode()


def test_variandual():
    conn = Connection()

    ctrl = VarianDual(conn)

    assert ctrl.remote == Remote.Local

    ctrl.remote = Remote.Remote

    assert ctrl.remote == Remote.Remote
    assert conn.remote == "1"

    assert ctrl.ctrl_firmware_version == conn.ctrl_firmware_version
    assert ctrl.dsp_firmware_version == conn.dsp_firmware_version

    assert ctrl.hv1.high_voltage == HighVoltage.Off
    assert ctrl.hv2.high_voltage == HighVoltage.On

    ctrl.hv1.high_voltage = HighVoltage.On
    assert ctrl.hv1.high_voltage == HighVoltage.On
    assert conn.hv1 == "1"

    assert ctrl.hv1.voltage == 14
    assert ctrl.hv2.voltage == 15

    with pytest.raises(AttributeError):
        ctrl.hv1.voltage = 55

    with pytest.raises(AttributeError):
        ctrl.hv2.voltage = 55

    assert ctrl.unit == Unit.torr
    ctrl.unit = Unit.mbar
    assert ctrl.unit == Unit.mbar
    assert conn.unit == "1"

    assert ctrl.hv1.fixed_step == FixedStep.Fixed
    assert ctrl.hv2.fixed_step == FixedStep.Step

    assert ctrl.serial_config is False
    ctrl.serial_config = True
    assert ctrl.serial_config is True
    assert conn.serial_config == "1"

    assert not ctrl.interlock_status
    conn.interlock_status = chr(128)
    assert ctrl.interlock_status == InterlockStatus.HV2Cable
