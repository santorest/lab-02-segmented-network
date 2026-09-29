import socket
import threading

import pytest

from labtools.checker import main, probe, run, to_markdown
from labtools.policy import validate
from tests.unit.test_policy import BASE


def policy_with(flows):
    return validate({**BASE, "flows": flows})


def flow(action, port=22, proto="tcp"):
    return {"from": "USERS", "to": "srv01", "proto": proto, "port": port, "action": action, "why": "test"}


@pytest.mark.parametrize(("action", "reachable", "passed"), [
    ("allow", True, True), ("allow", False, False), ("deny", False, True), ("deny", True, False)])
def test_results_compare_expected_and_actual(action, reachable, passed):
    results = run(policy_with([flow(action)]), "USERS", prober=lambda *a: reachable)
    assert [(r.reachable, r.passed) for r in results] == [(reachable, passed)]


def test_zone_without_flows_returns_empty_list():
    assert run(policy_with([flow("deny")]), "SERVERS", prober=lambda *a: True) == []


def test_targets_outside_lab_networks_are_refused():
    p = policy_with([flow("deny")])
    p.lab_networks.clear()
    with pytest.raises(ValueError, match="outside the lab"):
        run(p, "USERS", prober=lambda *a: False)


@pytest.mark.parametrize(("action", "reachable", "verdict"), [
    ("allow", False, "FAIL (blocked)"), ("deny", True, "FAIL (allowed)"), ("deny", False, "PASS")])
def test_markdown_marks_each_verdict_explicitly(action, reachable, verdict):
    results = run(policy_with([flow(action)]), "USERS", prober=lambda *a: reachable)
    assert f"| {verdict} |" in to_markdown(results)


def test_cli_reports_zone_without_flows(tmp_path, capsys):
    import yaml
    path = tmp_path / "policy.yaml"
    path.write_text(yaml.safe_dump({**BASE}), encoding="utf-8")
    assert main(["--zone", "SERVERS", "--policy", str(path), "--out", str(tmp_path)]) == 0
    assert "No flows defined for zone SERVERS" in capsys.readouterr().out


def test_cli_rejects_unknown_zone(tmp_path):
    import yaml
    path = tmp_path / "policy.yaml"
    path.write_text(yaml.safe_dump({**BASE}), encoding="utf-8")
    assert main(["--zone", "NOPE", "--policy", str(path), "--out", str(tmp_path)]) == 2


def test_real_tcp_probe_against_local_listener():
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen()
    port = server.getsockname()[1]
    threading.Thread(target=lambda: server.accept()[0].close(), daemon=True).start()
    assert probe("127.0.0.1", "tcp", port, 1.0) is True
    server.close()
    assert probe("127.0.0.1", "tcp", port, 0.5) is False


def test_real_udp_probe_needs_an_echo():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]

    def echo():
        data, addr = sock.recvfrom(64)
        sock.sendto(data, addr)

    threading.Thread(target=echo, daemon=True).start()
    assert probe("127.0.0.1", "udp", port, 1.0) is True
    sock.close()
    assert probe("127.0.0.1", "udp", port, 0.5) is False


# --- Final review fixes ---------------------------------------------------------------------------------------

def _dns_like_responder():
    """A UDP server that answers like a real DNS server: same transaction ID, different bytes (no echo)."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", 0))

    def answer():
        data, addr = sock.recvfrom(512)
        sock.sendto(data[:2] + b"\x81\x80" + b"\x00" * 8, addr)  # header only: QR=1, RCODE=0

    threading.Thread(target=answer, daemon=True).start()
    return sock


def test_udp_53_probe_accepts_a_real_dns_answer():
    sock = _dns_like_responder()
    port = sock.getsockname()[1]
    try:
        assert probe("127.0.0.1", "udp", port, 1.0, dns=True) is True
    finally:
        sock.close()


def test_udp_53_flows_are_probed_as_dns():
    seen = []
    p = validate({**BASE, "flows": [flow("allow", port=53, proto="udp")]})
    run(p, "USERS", prober=lambda ip, proto, port, timeout, dns=False: seen.append(dns) or True)
    assert seen == [True]


def test_flow_via_address_is_the_one_probed():
    data = {**BASE,
            "lab_networks": ["10.10.0.0/16", "203.0.113.0/24"],
            "zones": {**BASE["zones"], "WAN": {"site": "Internet", "vlan": 0, "subnet": "203.0.113.0/24"}},
            "flows": [{"from": "WAN", "to": "srv01", "via": "203.0.113.1", "proto": "tcp", "port": 22,
                       "action": "deny", "why": "SSH is never published"}]}
    probed = []
    results = run(validate(data), "WAN", prober=lambda ip, *a, **k: probed.append(ip) or False)
    assert probed == ["203.0.113.1"] and results[0].ip == "203.0.113.1"


def test_checker_cli_reports_out_of_lab_target_without_traceback(tmp_path, capsys):
    import yaml
    data = {**BASE, "flows": [flow("deny")]}
    path = tmp_path / "policy.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    from labtools import checker
    orig = checker.load_policy

    def load_and_empty_lab(p):
        pol = orig(p)
        pol.lab_networks.clear()
        return pol

    checker.load_policy = load_and_empty_lab
    try:
        assert main(["--zone", "USERS", "--policy", str(path), "--out", str(tmp_path)]) == 2
    finally:
        checker.load_policy = orig
    assert "outside the lab" in capsys.readouterr().err
