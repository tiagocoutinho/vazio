import pytest

from vacuum.protocol.multigauge import (
    HEADER_REQ, HEADER_REP, Command, Channel, Packet,
    encode, encode_packet, decode, decode_packet)


CHANNEL = 2, "2", b"2", Channel.HighVoltage2
COMMAND = 30, "30", b"30", Command.HighVoltage
DATA = '?', b'?'


@pytest.mark.parametrize('channel', CHANNEL,
                         ids=('ch_int', 'ch_str', 'ch_bytes', 'ch_enum'))
@pytest.mark.parametrize('command', COMMAND,
                         ids=('cmd_int', 'cmd_str', 'cmd_bytes', 'cmd_enum'))
@pytest.mark.parametrize('data', DATA,
                         ids=('data_str', 'data_bytes'))
def test_encode(channel, command, data):
    expected_request = b'#230?\r'
    expected_reply = b'>230?\r'
    assert encode(HEADER_REQ, channel, command, data) == expected_request
    assert encode(HEADER_REP, channel, command, data) == expected_reply

    packet = Packet(HEADER_REQ, channel, command, data)
    assert encode_packet(packet) == expected_request
    assert packet.encode() == expected_request

    packet = Packet(HEADER_REP, channel, command, data)
    assert encode_packet(packet) == expected_reply
    assert packet.encode() == expected_reply


def test_decode():
    request = b'#230?\r'
    expected_reply = HEADER_REQ, Channel.HighVoltage2, Command.HighVoltage, '?'
    expected_packet = Packet(*expected_reply)
    assert decode(request) == expected_reply
    assert decode_packet(request) == expected_packet
    assert Packet.decode(request) == expected_packet
