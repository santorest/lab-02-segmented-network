import copy

import pytest

from labtools.policy import PolicyError, validate

BASE = {
    "version": 1,
    "lab_networks": ["10.10.0.0/16"],
    "zones": {
        "USERS": {"site": "HQ", "vlan": 30, "subnet": "10.10.30.0/24"},
        "SERVERS": {"site": "HQ", "vlan": 20, "subnet": "10.10.20.0/24"},
    },
    "hosts": {"srv01": {"zone": "SERVERS", "ip": "10.10.20.12"}},
    "flows": [
        {"from": "USERS", "to": "srv01", "proto": "tcp", "port": 22, "action": "deny", "why": "no SSH from users"},
    ],
}


def raw(**changes):
    data = copy.deepcopy(BASE)
    data.update(changes)
    return data


def test_valid_policy_loads():
    p = validate(raw())
    assert p.flows_from("USERS")[0].dst_host == "srv01"
    assert p.flows_from("SERVERS") == []


@pytest.mark.parametrize(("flow_change", "message"), [
    ({"from": "NOPE"}, "unknown zone"),
    ({"to": "ghost"}, "unknown host"),
    ({"why": ""}, "justification"),
    ({"proto": "icmp"}, "proto"),
    ({"port": 70000}, "port"),
    ({"action": "maybe"}, "action"),
    ({"from": "SERVERS"}, "same zone"),
])
def test_invalid_flows_are_rejected(flow_change, message):
    flow = {**BASE["flows"][0], **flow_change}
    with pytest.raises(PolicyError, match=message):
        validate(raw(flows=[flow]))


def test_host_outside_its_zone_subnet_is_rejected():
    with pytest.raises(PolicyError, match="not in zone"):
        validate(raw(hosts={"srv01": {"zone": "SERVERS", "ip": "10.10.30.5"}}))


def test_host_outside_lab_networks_is_rejected():
    zones = {**BASE["zones"], "WAN": {"site": "-", "vlan": 0, "subnet": "8.8.8.0/24"}}
    with pytest.raises(PolicyError, match="outside lab_networks"):
        validate(raw(zones=zones, hosts={"dns": {"zone": "WAN", "ip": "8.8.8.8"}}, flows=[]))


def test_duplicate_flow_is_rejected():
    with pytest.raises(PolicyError, match="duplicate"):
        validate(raw(flows=BASE["flows"] * 2))


def test_malformed_policy_is_a_policy_error():
    with pytest.raises(PolicyError, match="malformed"):
        validate({"zones": {}})
