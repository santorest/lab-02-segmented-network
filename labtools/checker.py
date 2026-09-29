"""Check that the firewall enforces policy/policy.yaml, from the zone this host sits in.

    python3 -m labtools.checker --zone USERS

Only ordinary TCP connects and UDP echo probes are sent, and only to the lab's own hosts declared in the
policy; targets outside `lab_networks` are refused. Start `python3 -m labtools.listener` on each target first
so that allowed flows have something to answer (see docs/validation.md).
"""

import argparse
import csv
import secrets
import socket
import sys
from dataclasses import dataclass
from ipaddress import IPv4Address
from pathlib import Path

from labtools.policy import Flow, Policy, load_policy

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = b"lab02-probe"


@dataclass(frozen=True)
class Result:
    flow: Flow
    ip: str
    reachable: bool

    @property
    def passed(self) -> bool:
        return self.reachable == (self.flow.action == "allow")

    @property
    def verdict(self) -> str:
        if self.passed:
            return "PASS"
        return "FAIL (blocked)" if self.flow.action == "allow" else "FAIL (allowed)"


def dns_query() -> bytes:
    """A minimal DNS query (root NS, recursion desired) with a random transaction ID."""
    header = bytes.fromhex("0100" "0001" "0000" "0000" "0000")  # flags RD, 1 question
    question = bytes.fromhex("00" "0002" "0001")  # root, type NS, class IN
    return secrets.token_bytes(2) + header + question


def probe(ip: str, proto: str, port: int, timeout: float, dns: bool = False) -> bool:
    """True if a TCP connection opens, or a UDP datagram gets an answer, within the timeout.

    UDP needs a reply to be told apart from "blocked": the listener echoes the payload back. For DNS
    (dns=True) a real query is sent and any reply carrying the same transaction ID counts, which works
    both against a real DNS server (e.g. the domain controller) and against the echoing listener.
    """
    if proto == "tcp":
        try:
            with socket.create_connection((ip, port), timeout=timeout):
                return True
        except OSError:
            return False
    payload = dns_query() if dns else PAYLOAD
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout)
        try:
            sock.sendto(payload, (ip, port))
            data, _ = sock.recvfrom(4096)
        except OSError:
            return False
    return data[:2] == payload[:2] if dns else data == payload


def run(policy: Policy, zone: str, timeout: float = 2.0, allow_outside_lab: bool = False,
        prober=probe) -> list[Result]:
    results = []
    for flow in policy.flows_from(zone):
        ip = flow.via or policy.hosts[flow.dst_host].ip
        if not allow_outside_lab and not policy.in_lab(IPv4Address(ip)):
            raise ValueError(f"{flow.dst_host} ({ip}) is outside the lab networks; refusing to probe it")
        dns = flow.proto == "udp" and flow.port == 53
        results.append(Result(flow, str(ip), prober(str(ip), flow.proto, flow.port, timeout, dns)))
    return results


def to_markdown(results: list[Result]) -> str:
    lines = ["| From | To | Service | Expected | Actual | Result |", "|---|---|---|---|---|---|"]
    for r in results:
        actual = "reachable" if r.reachable else "blocked"
        lines.append(f"| {r.flow.src_zone} | {r.flow.dst_host} ({r.ip}) | {r.flow.proto}/{r.flow.port} | "
                     f"{r.flow.action} | {actual} | {r.verdict} |")
    return "\n".join(lines) + "\n"


def to_csv(results: list[Result], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["from", "to", "ip", "proto", "port", "expected", "reachable", "result"])
        for r in results:
            writer.writerow([r.flow.src_zone, r.flow.dst_host, r.ip, r.flow.proto, r.flow.port, r.flow.action,
                             r.reachable, r.verdict])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--zone", required=True, help="zone this host sits in, e.g. USERS")
    parser.add_argument("--policy", type=Path, default=ROOT / "policy" / "policy.yaml")
    parser.add_argument("--out", type=Path, default=ROOT / "tests" / "results")
    parser.add_argument("--timeout", type=float, default=2.0)
    args = parser.parse_args(argv)

    policy = load_policy(args.policy)
    if args.zone not in policy.zones:
        print(f"Unknown zone {args.zone!r}; zones: {', '.join(policy.zones)}", file=sys.stderr)
        return 2
    try:
        results = run(policy, args.zone, args.timeout)
    except ValueError as exc:
        print(f"Refusing to run: {exc}", file=sys.stderr)
        return 2
    if not results:
        print(f"No flows defined for zone {args.zone}")
        return 0
    print(to_markdown(results))
    to_csv(results, args.out / f"checker-{args.zone}.csv")
    failed = sum(not r.passed for r in results)
    print(f"{len(results) - failed}/{len(results)} flows as expected")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
