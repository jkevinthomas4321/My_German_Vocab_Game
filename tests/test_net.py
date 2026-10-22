import socket

import pytest

from webapp.net import free_port


def test_a_busy_port_is_skipped():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as busy:
        busy.bind(("0.0.0.0", 0))
        busy.listen()
        taken = busy.getsockname()[1]
        assert free_port(taken) != taken


def test_a_free_port_is_returned_as_is():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("0.0.0.0", 0))
        port = probe.getsockname()[1]
    assert free_port(port) == port


def test_gives_up_when_nothing_is_free():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as busy:
        busy.bind(("0.0.0.0", 0))
        busy.listen()
        with pytest.raises(OSError):
            free_port(busy.getsockname()[1], attempts=1)
