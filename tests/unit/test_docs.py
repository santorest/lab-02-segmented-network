"""The OPNsense rule guide must cover every allowed flow in the policy."""

from pathlib import Path

from labtools.policy import load_policy

ROOT = Path(__file__).resolve().parents[2]


def test_every_allow_flow_is_in_the_firewall_rules_guide():
    guide = (ROOT / "docs" / "opnsense" / "02-firewall-rules.md").read_text(encoding="utf-8")
    flows = load_policy(ROOT / "policy" / "policy.yaml").flows
    missing = [f"{f.src_zone}->{f.dst_host} {f.proto}/{f.port}" for f in flows
               if f.action == "allow" and f"{f.dst_host} {f.proto}/{f.port}" not in guide]
    assert not missing, f"allow flows missing from 02-firewall-rules.md: {missing}"


def test_every_guide_names_the_pinned_opnsense_version():
    for guide in sorted((ROOT / "docs" / "opnsense").glob("*.md")):
        assert "26.7" in guide.read_text(encoding="utf-8"), guide.name
