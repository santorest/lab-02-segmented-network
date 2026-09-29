from pathlib import Path

from labtools.policy import load_policy

POLICY = Path(__file__).resolve().parents[2] / "policy" / "policy.yaml"


def test_repo_policy_is_valid_and_covers_every_zone():
    p = load_policy(POLICY)
    for zone in ("USERS", "GUEST", "DMZ", "MGMT", "BR-USERS", "WAN"):
        assert p.flows_from(zone), f"no flows tested from {zone}"


def test_guest_and_dmz_are_denied_everything_internal():
    p = load_policy(POLICY)
    internal = {"SERVERS", "USERS", "MGMT", "BR-USERS"}
    for zone in ("GUEST", "DMZ"):
        for f in p.flows_from(zone):
            if p.hosts[f.dst_host].zone in internal:
                assert f.action == "deny", f


def test_internet_reaches_only_the_web_server_on_443():
    p = load_policy(POLICY)
    allowed = [(f.dst_host, f.port) for f in p.flows_from("WAN") if f.action == "allow"]
    assert allowed == [("web01", 443)]


def test_firewall_management_is_reachable_only_from_mgmt():
    p = load_policy(POLICY)
    for f in p.flows:
        if f.dst_host == "fw-hq-mgmt" and f.action == "allow":
            assert f.src_zone == "MGMT", f
