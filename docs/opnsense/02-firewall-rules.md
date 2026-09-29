# 2. Firewall rules (default deny)

Applies to **OPNsense 26.7.x**. The full list of tested flows, with the reason for each, is generated in
[../rules.md](../rules.md) from `policy/policy.yaml`. This guide turns every **allow** flow into a rule; every
flow not allowed hits the explicit block rule at the end of each interface.

## 2.1 Principles
- **Rules live on the interface where traffic enters** (the source zone). OPNsense evaluates them top-down;
  the first match wins.
- **Default deny:** each internal interface ends with *Block, any → any, Log*. OPNsense already blocks by
  default, but an explicit logged rule makes denied traffic visible in the logs and in Wazuh.
- **Aliases** keep rules readable: create them in **Firewall ▸ Aliases**.

| Alias | Type | Content |
|---|---|---|
| `h_dc01` | Host | 10.10.20.11 |
| `h_srv01` | Host | 10.10.20.12 |
| `h_wazuh01` | Host | 10.10.20.10 |
| `h_web01` | Host | 10.10.50.10 |
| `h_fw_br_mgmt` | Host | 10.20.99.1 |
| `net_internal` | Network | 10.10.0.0/16, 10.20.0.0/16 |
| `p_domain_tcp` | Port | 88, 389, 445 |

## 2.2 Rules per interface
Create them in **Firewall ▸ Rules ▸ <interface>**, in this order. "Internet" means destination
*not* `net_internal` (tick **Invert** on the destination).

### USERS
| # | Action | Proto | Destination | Port | Covers flow |
|---|---|---|---|---|---|
| 1 | Pass | TCP | `h_dc01` | `p_domain_tcp` | dc01 tcp/88, dc01 tcp/389, dc01 tcp/445 |
| 2 | Pass | UDP | `h_dc01` | 53 | dc01 udp/53 |
| 3 | Pass | TCP | `h_web01` | 443 | web01 tcp/443 |
| 4 | Pass | TCP | `h_wazuh01` | 1514, 1515 | wazuh01 tcp/1514, wazuh01 tcp/1515 (Lab 01 agents) |
| 5 | Pass | TCP/UDP | Internet (inverted `net_internal`) | 80, 443 | web browsing (NAT, see guide 3) |
| 6 | Block + log | any | any | any | everything else, incl. MGMT, the SIEM dashboard and server SSH |

### SERVERS
| # | Action | Proto | Destination | Port | Covers flow |
|---|---|---|---|---|---|
| 1 | Pass | TCP/UDP | SERVERS address (the firewall) | 53 | dc01 forwards external DNS to the filtered resolver |
| 2 | Block + log | any | any | any | servers start no other connections to other zones or the internet |

Traffic *between* servers (for example agents on dc01 and srv01 → wazuh01) stays inside VLAN 20 and never
crosses the firewall.

### GUEST
| # | Action | Proto | Destination | Port | Covers flow |
|---|---|---|---|---|---|
| 1 | Pass | TCP | `h_web01` | 443 | web01 tcp/443 |
| 2 | Pass | UDP | GUEST address (the firewall) | 53 | DNS through the filtered resolver only |
| 3 | Block + log | any | `net_internal` | any | guests never reach internal networks |
| 4 | Pass | TCP/UDP | Internet | 80, 443 | internet only |

### DMZ
| # | Action | Proto | Destination | Port | Covers flow |
|---|---|---|---|---|---|
| 1 | Block + log | any | `net_internal` | any | no lateral movement from the web server |
| 2 | Pass | TCP | update mirror alias | 443 | OS updates only (see guide 3) |
| 3 | Block + log | any | any | any | no other outbound traffic |

### MGMT
| # | Action | Proto | Destination | Port | Covers flow |
|---|---|---|---|---|---|
| 1 | Pass | TCP | `h_wazuh01` | 443 | wazuh01 tcp/443 |
| 2 | Pass | TCP | `h_srv01` | 22 | srv01 tcp/22 |
| 3 | Pass | TCP | `h_dc01` | 3389 | dc01 tcp/3389 |
| 4 | Pass | TCP | `h_web01` | 22 | web01 tcp/22 |
| 5 | Pass | TCP | `h_fw_br_mgmt` | 443 | fw-br-mgmt tcp/443 (over the IPsec tunnel) |
| 6 | Block + log | any | any | any | — |

The firewall's own GUI/SSH on 10.10.99.1 is reached through OPNsense's anti-lockout rule, which is bound to
MGMT in [08-admin-hardening.md](08-admin-hardening.md).

### WAN (fw-hq)
| # | Action | Proto | Destination | Port | Covers flow |
|---|---|---|---|---|---|
| 1 | Pass | TCP | `h_web01` (via port forward) | 443 | web01 tcp/443 — the only published service |
| 2 | Pass | UDP | WAN address | 500, 4500 | IPsec from fw-br only (source 203.0.113.2) |
| 3 | Pass | UDP | WAN address | 1194 | OpenVPN remote access |

Everything else on WAN is dropped by OPNsense's implicit deny (not logged, to avoid log noise from the
internet).

### IPsec (fw-hq) — traffic arriving from the branch
| # | Action | Proto | Source | Destination | Port | Covers flow |
|---|---|---|---|---|---|---|
| 1 | Pass | TCP | 10.20.30.0/24 | `h_dc01` | 88, 445 | dc01 tcp/88, dc01 tcp/445 from BR-USERS |
| 2 | Pass | UDP | 10.20.30.0/24 | `h_dc01` | 53 | dc01 udp/53 from BR-USERS |
| 3 | Block + log | any | any | any | any | — |

On **fw-br**, the BR_USERS interface passes traffic to 10.10.20.11 (TCP 88/445, UDP 53) and to the internet,
and blocks the rest; BR_MGMT passes TCP 443 from 10.10.99.0/24 arriving over IPsec (fw-br-mgmt tcp/443).

## 2.3 Check your work
1. **Firewall ▸ Log Files ▸ Live View**, filter on *block*: generate traffic from a probe host and confirm the
   drops you expect.
2. Run the checker from every zone ([../validation.md](../validation.md)); every row must read **PASS**.
