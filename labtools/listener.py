"""Answer the checker's probes on a target host: accept TCP connections and echo UDP datagrams.

    sudo python3 -m labtools.listener --tcp 22 443 --udp 53     # ports below 1024 need root

Run it on every host that appears as a destination in policy/policy.yaml, with the ports its flows use
(docs/validation.md lists the command per host). Without a listener, an allowed flow would look "blocked".
Stop with Ctrl+C. Do not run it on ports where the real service is already listening; it isn't needed there.
"""

import argparse
import os
import socket
import sys
import threading


def _tcp(sock: socket.socket, stop: threading.Event) -> None:
    sock.settimeout(0.2)
    while not stop.is_set():
        try:
            conn, _ = sock.accept()
            conn.close()
        except TimeoutError:
            continue
        except OSError:
            break
    sock.close()


def _udp(sock: socket.socket, stop: threading.Event) -> None:
    sock.settimeout(0.2)
    while not stop.is_set():
        try:
            data, addr = sock.recvfrom(64)
            sock.sendto(data, addr)
        except TimeoutError:
            continue
        except OSError:
            break
    sock.close()


def serve(tcp_ports, udp_ports, bind: str = "0.0.0.0", stop: threading.Event | None = None) -> threading.Event:  # noqa: S104  # nosec B104 - must answer probes from other zones
    """Bind every port first, then start one thread each; return an Event set once all are listening.

    If any port can't be bound (e.g. a real daemon already holds it) every socket opened so far is closed and
    the OSError is raised, so nothing is left half-running.
    """
    stop = stop or threading.Event()
    ready = threading.Event()
    bound: list[tuple[socket.socket, object]] = []
    try:
        for port in tcp_ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            bound.append((sock, _tcp))
            if os.name != "nt":  # on Windows SO_REUSEADDR would let us steal a port that is in use
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((bind, port))
            sock.listen()
        for port in udp_ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            bound.append((sock, _udp))
            sock.bind((bind, port))
    except OSError:
        for sock, _ in bound:
            sock.close()
        raise
    for sock, handler in bound:
        threading.Thread(target=handler, args=(sock, stop), daemon=True).start()
    ready.set()
    return ready


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tcp", type=int, nargs="*", default=[])
    parser.add_argument("--udp", type=int, nargs="*", default=[])
    parser.add_argument("--bind", default="0.0.0.0")  # noqa: S104  # nosec B104 - see serve()
    args = parser.parse_args(argv)
    if not (args.tcp or args.udp):
        parser.error("give at least one --tcp or --udp port")
    stop = threading.Event()
    try:
        serve(args.tcp, args.udp, args.bind, stop)
    except OSError as exc:
        print(f"Can't listen: {exc}. A port is probably already in use by a real service - leave that port out "
              "(see docs/listeners.md), or run with sudo for ports below 1024.", file=sys.stderr)
        return 1
    print(f"Listening on tcp {args.tcp} udp {args.udp}; Ctrl+C to stop")
    try:
        stop.wait()
    except KeyboardInterrupt:
        stop.set()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
