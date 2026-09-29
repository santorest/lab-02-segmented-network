<!-- Generated from policy/policy.yaml by `python -m labtools.render`. Do not edit by hand. -->

# IP plan

| Site | VLAN | Zone | Subnet | Hosts |
|---|---|---|---|---|
| Branch | 30 | BR-USERS | 10.20.30.0/24 | probe-branch (10.20.30.250) |
| Branch | 99 | BR-MGMT | 10.20.99.0/24 | fw-br-mgmt (10.20.99.1) |
| HQ | 20 | SERVERS | 10.10.20.0/24 | wazuh01 (10.10.20.10), dc01 (10.10.20.11), srv01 (10.10.20.12) |
| HQ | 30 | USERS | 10.10.30.0/24 | ws01 (10.10.30.21), probe-users (10.10.30.250) |
| HQ | 40 | GUEST | 10.10.40.0/24 | probe-guest (10.10.40.250) |
| HQ | 50 | DMZ | 10.10.50.0/24 | web01 (10.10.50.10) |
| HQ | 99 | MGMT | 10.10.99.0/24 | fw-hq-mgmt (10.10.99.1), jump01 (10.10.99.20) |
| Internet | 0 | WAN | 203.0.113.0/24 | probe-internet (203.0.113.100) |
