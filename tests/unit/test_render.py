import copy

import yaml

from labtools import render
from labtools.policy import validate
from tests.unit.test_policy import BASE


def test_rules_table_has_one_row_per_flow_with_justification():
    md = render.render_rules(validate(BASE))
    assert "| USERS | srv01 (SERVERS, 10.10.20.12) | tcp/22 | deny | no SSH from users |" in md
    assert md.endswith("\n") and "\r" not in md


def test_ip_plan_lists_zones_by_site_and_vlan():
    md = render.render_ip_plan(validate(BASE))
    assert md.index("| HQ | 20 | SERVERS") < md.index("| HQ | 30 | USERS")
    assert "srv01 (10.10.20.12)" in md


def test_check_mode_detects_drift(tmp_path):
    (tmp_path / "policy").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "policy" / "policy.yaml").write_text(yaml.safe_dump(BASE), encoding="utf-8")
    assert render.main(["--root", str(tmp_path), "--check"]) == 1  # nothing generated yet
    assert render.main(["--root", str(tmp_path)]) == 0
    assert render.main(["--root", str(tmp_path), "--check"]) == 0
    (tmp_path / "docs" / "rules.md").write_text("edited by hand\n", encoding="utf-8")
    assert render.main(["--root", str(tmp_path), "--check"]) == 1


def test_generated_files_use_lf_line_endings(tmp_path):
    (tmp_path / "policy").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "policy" / "policy.yaml").write_text(yaml.safe_dump(BASE), encoding="utf-8")
    render.main(["--root", str(tmp_path)])
    assert b"\r\n" not in (tmp_path / "docs" / "rules.md").read_bytes()


def test_listener_commands_cover_every_destination_port():
    p = validate({**BASE, "flows": BASE["flows"] + [
        {"from": "USERS", "to": "srv01", "proto": "udp", "port": 53, "action": "allow", "why": "dns"}]})
    md = render.render_listeners(p)
    assert "| srv01 | 10.10.20.12 | `sudo python3 -m labtools.listener --tcp 22 --udp 53` |" in md


def test_check_mode_covers_listener_doc(tmp_path):
    (tmp_path / "policy").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "policy" / "policy.yaml").write_text(yaml.safe_dump(BASE), encoding="utf-8")
    render.main(["--root", str(tmp_path)])
    assert (tmp_path / "docs" / "listeners.md").exists()
    (tmp_path / "docs" / "listeners.md").write_text("stale\n", encoding="utf-8")
    assert render.main(["--root", str(tmp_path), "--check"]) == 1


def test_hosts_with_real_services_get_no_listener_command():
    data = copy.deepcopy(BASE)
    data["hosts"]["srv01"]["real_services"] = True
    md = render.render_listeners(validate(data))
    assert "| srv01 | 10.10.20.12 | none: its real services answer (tcp 22) |" in md


def test_listener_commands_skip_ports_served_by_real_daemons():
    data = copy.deepcopy(BASE)
    data["hosts"]["srv01"]["real_services"] = [22]
    data["flows"].append({"from": "USERS", "to": "srv01", "proto": "tcp", "port": 8443, "action": "deny", "why": "x"})
    md = render.render_listeners(validate(data))
    assert "`sudo python3 -m labtools.listener --tcp 8443` (tcp 22 answered by its real services) |" in md


def test_rules_show_the_probed_address_for_via_flows():
    data = copy.deepcopy(BASE)
    data["lab_networks"].append("203.0.113.0/24")
    data["zones"]["WAN"] = {"site": "Internet", "vlan": 0, "subnet": "203.0.113.0/24"}
    data["flows"] = [{"from": "WAN", "to": "srv01", "via": "203.0.113.1", "proto": "tcp", "port": 22,
                      "action": "deny", "why": "never published"}]
    md = render.render_rules(validate(data))
    assert "| WAN | srv01 (SERVERS, 10.10.20.12) via 203.0.113.1 | tcp/22 | deny |" in md


def test_via_flows_need_no_listener_on_the_inner_host():
    data = copy.deepcopy(BASE)
    data["lab_networks"].append("203.0.113.0/24")
    data["zones"]["WAN"] = {"site": "Internet", "vlan": 0, "subnet": "203.0.113.0/24"}
    data["flows"] = [{"from": "WAN", "to": "srv01", "via": "203.0.113.1", "proto": "tcp", "port": 80,
                      "action": "deny", "why": "not published"}]
    assert "srv01" not in render.render_listeners(validate(data))
