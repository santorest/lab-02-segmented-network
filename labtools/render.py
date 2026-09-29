"""Render policy/policy.yaml into docs/ip-plan.md and docs/rules.md.

    python -m labtools.render            # regenerate the docs
    python -m labtools.render --check    # CI: fail if the docs don't match the policy
"""

import argparse
import sys
from pathlib import Path

from labtools.policy import Policy, load_policy

HEADER = "<!-- Generated from policy/policy.yaml by `python -m labtools.render`. Do not edit by hand. -->\n\n"


def render_ip_plan(p: Policy) -> str:
    lines = [HEADER + "# IP plan\n", "| Site | VLAN | Zone | Subnet | Hosts |", "|---|---|---|---|---|"]
    for z in sorted(p.zones.values(), key=lambda z: (z.site, z.vlan, z.name)):
        hosts = ", ".join(f"{h.name} ({h.ip})" for h in p.hosts.values() if h.zone == z.name) or "—"
        lines.append(f"| {z.site} | {z.vlan} | {z.name} | {z.subnet} | {hosts} |")
    return "\n".join(lines) + "\n"


def render_rules(p: Policy) -> str:
    lines = [
        HEADER + "# Tested flows\n",
        "Everything not listed as `allow` is denied by default. `deny` rows are listed so the checker proves them.\n",
        "| From | To | Service | Action | Why |",
        "|---|---|---|---|---|",
    ]
    for f in p.flows:
        h = p.hosts[f.dst_host]
        lines.append(f"| {f.src_zone} | {h.name} ({h.zone}, {h.ip}) | {f.proto}/{f.port} | {f.action} | {f.why} |")
    return "\n".join(lines) + "\n"


def render_listeners(p: Policy) -> str:
    """One listener command per destination host, with every port its flows (allow and deny) use."""
    lines = [
        HEADER + "# Listener commands\n",
        "Run on each target before the checker, so allowed flows have something to answer. Skip ports where the "
        "real service already listens.\n",
        "| Host | IP | Command |",
        "|---|---|---|",
    ]
    for name, host in p.hosts.items():
        tcp = sorted({f.port for f in p.flows if f.dst_host == name and f.proto == "tcp"})
        udp = sorted({f.port for f in p.flows if f.dst_host == name and f.proto == "udp"})
        if not (tcp or udp):
            continue
        if host.real_services:
            parts = [f"{proto} {' '.join(map(str, ports))}" for proto, ports in (("tcp", tcp), ("udp", udp)) if ports]
            ports = ", ".join(parts)
            lines.append(f"| {name} | {host.ip} | none: its real services answer ({ports}) |")
            continue
        args = (["--tcp", *map(str, tcp)] if tcp else []) + (["--udp", *map(str, udp)] if udp else [])
        lines.append(f"| {name} | {host.ip} | `sudo python3 -m labtools.listener {' '.join(args)}` |")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Render the policy into Markdown docs.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check", action="store_true", help="exit 1 if the docs are out of date")
    args = parser.parse_args(argv)

    policy = load_policy(args.root / "policy" / "policy.yaml")
    outputs = {
        args.root / "docs" / "ip-plan.md": render_ip_plan(policy),
        args.root / "docs" / "rules.md": render_rules(policy),
        args.root / "docs" / "listeners.md": render_listeners(policy),
    }
    drifted = []
    for path, text in outputs.items():
        if args.check:
            current = path.read_bytes().decode("utf-8") if path.exists() else None
            if current != text:
                drifted.append(path.name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(text.encode("utf-8"))  # bytes: identical output on Windows and Linux
    if drifted:
        print("Out of date (run python -m labtools.render): " + ", ".join(drifted), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
