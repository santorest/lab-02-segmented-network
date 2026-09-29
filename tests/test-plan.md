# Test plan

## Automated
Run `python3 -m labtools.checker --zone <ZONE>` from each zone (see [../docs/validation.md](../docs/validation.md))
and keep the CSV files from `tests/results/`.

| Zone | Probe host | Flows | Passed | CSV |
|---|---|---|---|---|
| USERS | probe-users | | | |
| GUEST | probe-guest | | | |
| DMZ | web01 | | | |
| MGMT | jump01 | | | |
| BR-USERS | probe-branch | | | |
| WAN | probe-internet | | | |

## Manual
| # | Check | Guide | Expected | Result | Evidence |
|---|---|---|---|---|---|
| M1 | IPsec phase 1 and 2 up on both firewalls | 06 | Both *installed* | | |
| M2 | Packet capture on fw-hq WAN while BR-USERS reaches dc01 | 06 | Only ESP / UDP 4500, no inner TCP 445 | | |
| M3 | OpenVPN login with password + TOTP | 07 | Connected; dc01 TCP 445 reachable | | |
| M4 | OpenVPN login with password, wrong or no TOTP | 07 | Refused and logged | | |
| M5 | IPS test signature from probe-users | 04 | Alert (or drop) in OPNsense and in Wazuh | | |
| M6 | Lookup of a blocklisted domain via dc01 and via the GUEST resolver | 05 | 0.0.0.0 / NXDOMAIN | | |
| M7 | DNS query to an outside resolver from USERS | 05 | Times out (blocked) | | |
| M8 | Firewall GUI login from jump01 | 08 | Requires the TOTP code | | |
| M9 | Failed firewall admin login | 08 | Event visible in Wazuh | | |
| M10 | Encrypted configuration backup restored on a spare VM | 08 | Restore succeeds | | |
