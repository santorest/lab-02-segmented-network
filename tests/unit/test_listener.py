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
