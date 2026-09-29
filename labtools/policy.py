"""Load and validate the lab's policy matrix (policy/policy.yaml).

    python -m labtools.policy policy/policy.yaml
"""

import sys
from dataclasses import dataclass, field
from ipaddress import IPv4Address, IPv4Network
from pathlib import Path

import yaml


class PolicyError(ValueError):
    pass


@dataclass(frozen=True)
class Zone:
    name: str
    site: str
    vlan: int
    subnet: IPv4Network


@dataclass(frozen=True)
class Host:
    name: str
    zone: str
    ip: IPv4Address
    all_real: bool = False  # its own services answer on every probed port (no listener needed)
    real_ports: frozenset[int] = frozenset()  # ports answered by its own services (listener for the rest)

    def answers_itself(self, port: int) -> bool:
        return self.all_real or port in self.real_ports


@dataclass(frozen=True)
class Flow:
    src_zone: str
    dst_host: str
    proto: str
    port: int
    action: str
    why: str
    via: IPv4Address | None = None  # address actually probed, e.g. the WAN address in front of a port forward


@dataclass
class Policy:
    lab_networks: list[IPv4Network]
    zones: dict[str, Zone]
    hosts: dict[str, Host]
    flows: list[Flow] = field(default_factory=list)

    def flows_from(self, zone: str) -> list[Flow]:
        return [f for f in self.flows if f.src_zone == zone]

    def in_lab(self, ip: IPv4Address) -> bool:
        return any(ip in net for net in self.lab_networks)


def _real_services(host: str, value) -> tuple[bool, frozenset[int]]:
    """real_services: true (every port), false/absent (none) or a list of port numbers."""
    if value is True or value is False:
        return value, frozenset()
    if isinstance(value, list) and all(isinstance(p, int) and not isinstance(p, bool) for p in value):
        return False, frozenset(value)
    raise PolicyError(f"host {host}: real_services must be true, false or a list of port numbers")


def _zones_and_hosts(raw: dict) -> tuple[list[IPv4Network], dict[str, Zone], dict[str, Host]]:
    lab = [IPv4Network(n) for n in raw["lab_networks"]]
    zones = {n: Zone(n, str(z["site"]), int(z["vlan"]), IPv4Network(z["subnet"])) for n, z in raw["zones"].items()}
    hosts = {}
    for name, h in raw["hosts"].items():
        if h["zone"] not in zones:
            raise PolicyError(f"host {name}: unknown zone {h['zone']!r}")
        all_real, real_ports = _real_services(name, h.get("real_services", False))
        host = Host(name, h["zone"], IPv4Address(h["ip"]), all_real, real_ports)
        if host.ip not in zones[host.zone].subnet:
            raise PolicyError(f"host {name}: {host.ip} is not in zone {host.zone} ({zones[host.zone].subnet})")
        if not any(host.ip in net for net in lab):
            raise PolicyError(f"host {name}: {host.ip} is outside lab_networks")
        hosts[name] = host
    return lab, zones, hosts


def validate(raw: dict) -> Policy:
    try:
        lab, zones, hosts = _zones_and_hosts(raw)
    except PolicyError:
        raise
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise PolicyError(f"malformed policy: {exc!r}") from exc

    flows, seen = [], set()
    for i, f in enumerate(raw.get("flows") or [], 1):
        where = f"flow {i}"
        if f.get("from") not in zones:
            raise PolicyError(f"{where}: unknown zone {f.get('from')!r}")
        if f.get("to") not in hosts:
            raise PolicyError(f"{where}: unknown host {f.get('to')!r}")
        if hosts[f["to"]].zone == f["from"]:
            raise PolicyError(f"{where}: source and destination are in the same zone ({f['from']})")
        if f.get("proto") not in ("tcp", "udp"):
            raise PolicyError(f"{where}: proto must be tcp or udp")
        if not isinstance(f.get("port"), int) or not 1 <= f["port"] <= 65535:
            raise PolicyError(f"{where}: port must be 1-65535")
        if f.get("action") not in ("allow", "deny"):
            raise PolicyError(f"{where}: action must be allow or deny")
        if not str(f.get("why") or "").strip():
            raise PolicyError(f"{where}: missing justification (why)")
        via = None
        if f.get("via") is not None:
            try:
                via = IPv4Address(f["via"])
            except ValueError as exc:
                raise PolicyError(f"{where}: via is not an IPv4 address") from exc
            if not any(via in net for net in lab):
                raise PolicyError(f"{where}: via {via} is outside lab_networks")
        key = (f["from"], f["to"], f["proto"], f["port"], via)
        if key in seen:
            raise PolicyError(f"{where}: duplicate of an earlier flow {key}")
        seen.add(key)
        flows.append(Flow(f["from"], f["to"], f["proto"], f["port"], f["action"], str(f["why"]).strip(), via))
    return Policy(lab, zones, hosts, flows)


def load_policy(path: Path) -> Policy:
    return validate(yaml.safe_load(Path(path).read_text(encoding="utf-8")))


def main(argv=None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: python -m labtools.policy POLICY_FILE", file=sys.stderr)
        return 2
    try:
        p = load_policy(Path(args[0]))
    except PolicyError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print(f"OK: {len(p.zones)} zones, {len(p.hosts)} hosts, {len(p.flows)} flows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
