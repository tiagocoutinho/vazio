import pytest

from vazio.protocol.multigauge import (
    HEADER_REQ,
    HEADER_REP,
    Command,
    Channel,
    encode,
    encode_request,
    decode,
    decode_reply,
)


CHANNEL = 2, "2", b"2", Channel.HighVoltage2
COMMAND = 30, "30", b"30", Command.HighVoltage
DATA = "?", b"?"


@pytest.mark.parametrize(
    "channel", CHANNEL, ids=("ch_int", "ch_str", "ch_bytes", "ch_enum")
)
@pytest.mark.parametrize(
    "command", COMMAND, ids=("cmd_int", "cmd_str", "cmd_bytes", "cmd_enum")
)
@pytest.mark.parametrize("data", DATA, ids=("data_str", "data_bytes"))
def test_encode(channel, command, data):
    expected_request = b"#230?\r"
    expected_reply = b">230?\r"
    assert encode(HEADER_REQ, channel, command, data) == expected_request
    assert encode(HEADER_REP, channel, command, data) == expected_reply


@pytest.mark.parametrize(
    "channel", CHANNEL, ids=("ch_int", "ch_str", "ch_bytes", "ch_enum")
)
@pytest.mark.parametrize(
    "command", COMMAND, ids=("cmd_int", "cmd_str", "cmd_bytes", "cmd_enum")
)
@pytest.mark.parametrize("data", DATA, ids=("data_str", "data_bytes"))
def test_encode_request(channel, command, data):
    expected_request = b"#230?\r"
    assert encode_request(channel, command, data) == expected_request


def test_decode():
    request = b"#230?\r"
    expected_reply = HEADER_REQ, Channel.HighVoltage2, Command.HighVoltage, "?"
    assert decode(request) == expected_reply


def test_decode_reply():
    request = b">230?\r"
    expected_reply = HEADER_REP, Channel.HighVoltage2, Command.HighVoltage, "?"
    assert decode_reply(request) == expected_reply
