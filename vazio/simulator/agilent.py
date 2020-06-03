"""
Agilent 4UHV simulator helper classes

To create an Agilent 4UHV device use the following configuration as
a starting point:

.. code-block:: yaml

    devices:
    - class: Agilent4UHV
      package: vazio.simulator.agilent
      transports:
      - type: serial
        url: /tmp/agilent4uhv00
"""

import enum
import random
import operator
import functools

from sinstruments.simulator import BaseDevice, MessageHandler


def funiform(a, b):
    return lambda: '{: 10.1E}'.format(random.uniform(a, b))


def iuniform(a, b, x=1):
    return lambda: '{:05d}'.format(x*random.randint(a, b))


state = {
}

# protocol
# MESSAGE: <STX>+<ADDR>+<WIN>+<COM>+<DATA>+<ETX>+<CRC>

STX = b"\x02"
ETX = b"\x03"
ACK = b"\x06"
NACK = b"\x15"
UNKNOWN_WINDOW = b"\x32"
DATA_TYPE_ERROR = b"\x33"
WINDOW_DISABLED = b"\x35"
RS232_ADDR = b"\x80"


class Command(enum.Enum):
    READ = b"\x30"
    WRITE = b"\31"


class Window(enum.Enum):
    LocalMode = b"008"
    HV1_ON = b"011"
    HV2_ON = b"012"
    HV3_ON = b"013"
    HV4_ON = b"014"
    Status = b"205"
    ErrorCode = b"206"
    Model = b"319"

    SerialNumber = b"323"
    SerialType = b"504"
    Channel = b"505"
    Unit = b"600"
    Mode = b"601"
    Protect = b"602"
    FixedStep = b"603"

    Dev1 = b"610"
    Power1 = b"612"
    Vt1 = b"613"
    IProt1 = b"614"
    SP1 = b"615"

    Dev2 = b"620"
    Power2 = b"622"
    Vt2 = b"623"
    IProt2 = b"624"
    SP2 = b"625"

    Dev3 = b"630"
    Power3 = b"632"
    Vt3 = b"633"
    IProt3 = b"634"
    SP3 = b"635"

    Dev4 = b"640"
    Power4 = b"642"
    Vt4 = b"643"
    IProt4 = b"644"
    SP4 = b"645"

    Temp1 = b"801"
    Temp2 = b"802"
    Temp3 = b"808"
    Temp4 = b"809"

    Ilock = b"803"
    StatusSP = b"804"

    V1 = b"810"
    I1 = b"811"
    P1 = b"812"

    V2 = b"820"
    I2 = b"821"
    P2 = b"822"

    V3 = b"830"
    I3 = b"831"
    P3 = b"832"

    V4 = b"840"
    I4 = b"841"
    P4 = b"842"


def crc(msg):
    return functools.reduce(operator.xor, msg)


def crc_ascii(msg):
    return "{:X}".format(crc(msg)).encode()


def decode_message(msg):
    assert msg[0:1] == STX, "invalid start byte"
    addr = msg[1] - RS232_ADDR[0]
    wnd = Window(msg[2:5])
    cmd = Command(msg[5:6])
    data = msg[5:-3]
    assert msg[-3:-2] == ETX, "invalid end byte"
    assert crc_ascii(msg[1:-2]) == msg[-2:], "invalid crc"
    return addr, wnd, cmd, data


def encode_answer(wnd, data=ACK, addr=0):
    if isinstance(data, str):
        data = data.encode()
    addr = chr(ord(RS232_ADDR) + addr).encode()
    msg = STX + addr + wnd.value + data + ETX
    msg += crc_ascii(msg[1:])
    return msg


class Protocol(MessageHandler):

    def char_stream(self):
        while True:
            c = self.fobj.read(1)
            if not c:
                break
            yield c

    def read_messages(self):
        buff = b""
        stream = self.char_stream()
        for char in stream:
            # ignore messages until we receive STX
            if not buff and char != STX:
                continue
            buff += char
            if char == ETX:
                # read CRC and yield
                buff += next(stream) + next(stream)
                yield buff
                buff = b""


state = {
    Window.LocalMode: "000001",      # SERIAL:000000, REMOTE:000001, LOCAL:000002
    Window.ErrorCode: b"000000",
    Window.Model: b"4UHV",
    Window.P1: funiform(5e-9, 9e-7),
    Window.P2: funiform(5e-9, 9e-7),
    Window.P3: funiform(5e-9, 9e-7),
    Window.P4: funiform(5e-9, 9e-7),
    Window.I1: funiform(5e-3, 9e-2),
    Window.I2: funiform(5e-3, 9e-2),
    Window.I3: funiform(5e-3, 9e-2),
    Window.I4: funiform(5e-3, 9e-2),
    Window.V1: iuniform(5, 68, 100),
    Window.V2: iuniform(50, 68, 100),
    Window.V3: iuniform(50, 68, 100),
    Window.V4: iuniform(50, 68, 100),
}


class Agilent4UHV(BaseDevice):

    message_handler = Protocol

    def handle_line(self, line):
        self._log.info("processing line %r", line)
        addr, wnd, cmd, data = decode_message(line)
        if cmd == Command.READ:
            data = state[wnd]
            if callable(data):
                data = data()
            reply = encode_answer(wnd, data)
            self._log.info("reply with %r", reply)
            return reply
