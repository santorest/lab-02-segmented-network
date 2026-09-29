import socket
import threading

from labtools.checker import probe
from labtools.listener import serve


def free_port(kind):
    s = socket.socket(socket.AF_INET, kind)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def test_listener_makes_tcp_and_udp_flows_reachable():
    tcp, udp = free_port(socket.SOCK_STREAM), free_port(socket.SOCK_DGRAM)
    stop = threading.Event()
    ready = serve([tcp], [udp], bind="127.0.0.1", stop=stop)
    assert ready.wait(2)
    try:
        assert probe("127.0.0.1", "tcp", tcp, 1.0) is True
        assert probe("127.0.0.1", "udp", udp, 1.0) is True
    finally:
        stop.set()


def test_busy_port_raises_cleanly_and_releases_ports_already_bound():
    import pytest
    busy = socket.socket()
    busy.bind(("127.0.0.1", 0))
    busy.listen()
    busy_port = busy.getsockname()[1]
    free = free_port(socket.SOCK_STREAM)
    try:
        with pytest.raises(OSError):
            serve([free, busy_port], [], bind="127.0.0.1")
        again = socket.socket()
        again.bind(("127.0.0.1", free))  # must be free again: nothing leaked
        again.close()
    finally:
        busy.close()


def test_cli_reports_busy_port_without_traceback(capsys):
    from labtools.listener import main
    busy = socket.socket()
    busy.bind(("127.0.0.1", 0))
    busy.listen()
    try:
        assert main(["--tcp", str(busy.getsockname()[1]), "--bind", "127.0.0.1"]) == 1
    finally:
        busy.close()
    assert "already in use" in capsys.readouterr().err
