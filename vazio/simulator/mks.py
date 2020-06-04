"""
MKS simulator helper classes

To create a MKS device use the following configuration as
a starting point:

.. code-block:: yaml

    devices:
    - class: MKS937
      package: vazio.simulator.mks
      transports:
      - type: serial
        url: /tmp/mks00
"""

import random

from sinstruments.simulator import BaseDevice


def funiform(a, b):
    return lambda: '{:7.1E}'.format(random.uniform(a, b))


def iuniform(a, b):
    return lambda: '{:05d}'.format(random.randint(a, b))


state = {
    'P1': funiform(5e-9, 9e-7),
    'P2': funiform(5e-9, 9e-3),
    'P3': funiform(5e-9, 9e-7),
    'P4': funiform(5e-9, 9e-3),
    'P5': funiform(5e-9, 9e-7),
    'C1': funiform(5e-9, 9e-3),
    'C2': funiform(5e-9, 9e-7),
    'C3': funiform(5e-9, 9e-3),
    'C4': funiform(5e-9, 9e-7),
    'C5': funiform(5e-9, 9e-3),
    'GAUGES': 'CvPrCv',
    'PRO1': '4.1E-9',
    'PRO2': '5.1E-9',
    'PRO3': '6.1E-9',
    'PRO4': '7.1E-9',
    'PRO5': '8.1E-9',
    'RELAYS': 'rly11011',
    'RLY1': '4.7E-9',
    'RLY2': '5.7E-9',
    'RLY3': '6.7E-9',
    'RLY4': '7.7E-9',
    'RLY5': '8.7E-9',
    'VER': '2.59,6.17',
    'UNIT': 'mbar',
    'ECC1': 'OK',
    'ECC2': 'PROTECT!',
    'ECC4': 'PS_FAULT!',
    'XCC1': 'OK',
    'XCC2': 'OK',
    'XCC4': 'OK',
}


class MKS937(BaseDevice):

    newline = b"\r"
    baudrate = 19200   # should accept 19200 or lower

    def handle_message(self, line):
        self._log.info("processing message %r", line)
        line = line.decode()
        data = state[line]
        if callable(data):
            data = data()
        reply = data.encode() + self.newline
        self._log.debug("reply %r", reply)
        return reply
