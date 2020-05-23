import serial
from tango.server import Device, attribute, command, device_property

from vacuum.variandual import VarianDual as _VarianDual


def serial_for_url(url, *args, **kwargs):
    conn = serial.serial_for_url(url, *args, **kwargs)

    def write_readline(data):
        conn.write(data)
        return conn.readline()

    conn.write_readline = write_readline
    return conn


class VarianDual(Device):

    address = device_property(dtype=str)

    def init_device(self):
        super().init_device()
        conn = serial_for_url(self.address)
        self.ctrl = _VarianDual(conn)

    @attribute(dtype=int, unit="V", format="%05d", description="Channel 1 voltage")
    def v1(self):
        return self.ctrl.hv1.voltage

    @attribute(dtype=int, unit="V", format="%05d", description="Channel 2 voltage")
    def v2(self):
        return self.ctrl.hv2.voltage

    @attribute(dtype=float, unit="mA", format="%5.2e", description="Channel 1 current")
    def i1(self):
        return self.ctrl.hv1.current

    @attribute(dtype=float, unit="V", format="%5.2e", description="Channel 2 current")
    def i2(self):
        return self.ctrl.hv2.current

    @attribute(dtype=float, unit="mA", format="%5.2e", description="Channel 1 pressure")
    def p1(self):
        return self.ctrl.hv1.pressure

    @attribute(dtype=float, unit="V", format="%5.2e", description="Channel 2 pressure")
    def p2(self):
        return self.ctrl.hv2.pressure

    @attribute(dtype=[str])
    def ionpumpsconfig(self):
        return self.ctrl.hv1.device_type, self.ctrl.hv2.device_type

    @attribute(dtype=bool)
    def interlock(self):
        return bool(self.ctrl.interlock_status)

    @command
    def on(self):
        pass


if __name__ == "__main__":
    VarianDual.run_server()
