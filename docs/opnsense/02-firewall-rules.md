# 2. Firewall rules (default deny)

Applies to **OPNsense 26.7.x**. Every flow in the policy, with the reason for it, is generated in
[../rules.md](../rules.md) from `policy/policy.yaml`. This guide turns every **allow** flow into a rule; every
flow not allowed hits the explicit block rule at the end of each interface.

## 2.1 Principles
- **Rules live on the interface where traffic enters.** For traffic arriving through a VPN that is the
  **IPsec** or **OpenVPN** interface, not the LAN-side interface it is going to. OPNsense evaluates rules
  top-down; the first match wins.
- **Default deny:** each internal interface ends with *Block, any → any, Log*. OPNsense already blocks by
  default, but an explicit logged rule makes denied traffic visible in the logs and in Wazuh.
- **"Internet"** below means destination `net_internal` **inverted** *and* not the firewall itself; OPNsense's
  *This Firewall* alias is excluded by adding a *Block → This Firewall* rule above the internet rule where noted.
- **Aliases** keep rules readable: create them in **Firewall ▸ Aliases**.

| Alias | Type | Content |
|---|---|---|
| `h_dc01` | Host | 10.10.20.11 |
| `h_srv01` | Host | 10.10.20.12 |
| `h_wazuh01` | Host | 10.10.20.10 |
| `h_web01` | Host | 10.10.50.10 |
| `h_fw_br_mgmt` | Host | 10.20.99.1 |
| `net_internal` | Network | 10.10.0.0/16, 10.20.0.0/16 |
| `p_ad_tcp` | Port | 53, 88, 135, 389, 445, 464, 3268, 49152:65535 (dynamic RPC) |
| `p_ad_udp` | Port | 53, 88, 123, 389, 464 |

Why the AD port list: a Windows domain client needs more than logon (Kerberos 88) and file shares (445). It
also locates domain controllers over CLDAP (UDP 389), syncs time (UDP 123; Kerberos fails beyond 5 minutes of
clock skew), changes passwords (464), queries the global catalog (3268) and uses RPC (135 plus the dynamic
range) for Netlogon and Group Policy. Missing any of these breaks logon in ways that are hard to diagnose.

## 2.2 Rules on fw-hq
Create them in **Firewall ▸ Rules ▸ <interface>**, in this order.

### USERS
| # | Action | Proto | Destination | Port | Covers flow |
|---|---|---|---|---|---|
| 1 | Pass | TCP | `h_dc01` | `p_ad_tcp` | dc01 tcp/53, dc01 tcp/88, dc01 tcp/135, dc01 tcp/389, dc01 tcp/445, dc01 tcp/464, dc01 tcp/3268 |
| 2 | Pass | UDP | `h_dc01` | `p_ad_udp` | dc01 udp/53, dc01 udp/88, dc01 udp/123, dc01 udp/389, dc01 udp/464 |
| 3 | Pass | TCP | `h_web01` | 443 | web01 tcp/443 |
| 4 | Pass | TCP | `h_wazuh01` | 1514, 1515 | wazuh01 tcp/1514, wazuh01 tcp/1515 (Lab 01 agents) |
| 5 | Block + log | TCP/UDP | any | 53, 853 | no DNS except through dc01 (guide 5) |
| 6 | Block + log | any | This Firewall | any | the firewall's own addresses, including its WAN address |
| 7 | Pass | TCP | Internet (inverted `net_internal`) | 80, 443 | web browsing (NAT, guide 3) |
| 8 | Block + log | any | any | any | everything else, incl. MGMT, the SIEM dashboard and server SSH |

### GUEST
| # | Action | Proto | Destination | Port | Covers flow |
|---|---|---|---|---|---|
| 1 | Pass | TCP/UDP | GUEST address (the firewall) | 53 | DNS through the filtered resolver only |
| 2 | Pass | TCP | `h_web01` | 443 | web01 tcp/443 |
| 3 | Block + log | any | `net_internal` | any | guests never reach internal networks |
| 4 | Block + log | any | This Firewall | any | no access to the firewall's other addresses |
| 5 | Block + log | TCP/UDP | any | 53, 853 | no outside DNS |
| 6 | Pass | TCP | Internet | 80, 443 | internet only |
| 7 | Block + log | any | any | any | — |

### SERVERS
| # | Action | Proto | Destination | Port | Covers flow |
|---|---|---|---|---|---|
| 1 | Pass | TCP/UDP | SERVERS address (the firewall) | 53 | dc01 forwards external DNS to the filtered resolver |
| 2 | Pass | UDP | SERVERS address (the firewall) | 123 | dc01 syncs time from the firewall (guide 8) |
| 3 | Block + log | any | any | any | servers start no other connections to other zones or the internet |

Traffic *between* servers (for example agents on dc01 and srv01 → wazuh01) stays inside VLAN 20 and never
crosses the firewall.

### DMZ
| # | Action | Proto | Destination | Port | Covers flow |
|---|---|---|---|---|---|
| 1 | Pass | TCP/UDP | DMZ address (the firewall) | 53 | web01 resolves names through the filtered resolver |
| 2 | Block + log | any | `net_internal` | any | no lateral movement from the web server |
| 3 | Pass | TCP | `update_mirrors` alias | 443 | OS updates only; apt sources must use **https** (guide 3) |
| 4 | Block + log | any | any | any | no other outbound traffic |

### MGMT
| # | Action | Proto | Destination | Port | Covers flow |
|---|---|---|---|---|---|
| 1 | Pass | TCP/UDP | MGMT address (the firewall) | 53 | DNS for the jump host |
| 2 | Pass | TCP | `h_wazuh01` | 443 | wazuh01 tcp/443 |
| 3 | Pass | TCP | `h_srv01` | 22 | srv01 tcp/22 |
| 4 | Pass | TCP | `h_dc01` | 3389 | dc01 tcp/3389 |
| 5 | Pass | TCP | `h_web01` | 22 | web01 tcp/22 |
| 6 | Pass | TCP | `h_fw_br_mgmt` | 443 | fw-br-mgmt tcp/443 (leaves through the IPsec tunnel) |
| 7 | Block + log | any | any | any | — |

The firewall's own GUI/SSH on 10.10.99.1 is reached through the anti-lockout rule on MGMT
([08-admin-hardening.md](08-admin-hardening.md)).

### WAN
| # | Action | Proto | Source | Destination | Port | Covers flow |
|---|---|---|---|---|---|---|
| 1 | Pass | TCP | any | `h_web01` (created by the port forward, guide 3) | 443 | web01 tcp/443 — the only published service |
| 2 | Pass | UDP | 203.0.113.2 (fw-br) | WAN address | 500, 4500 | IPsec key exchange, only from the peer |
| 3 | Pass | ESP | 203.0.113.2 (fw-br) | WAN address | — | IPsec data (no NAT between the sites, so ESP is used) |
| 4 | Pass | UDP | any | WAN address | 1194 | OpenVPN remote access |

Disable **Firewall ▸ Settings ▸ Advanced ▸ Disable auto-added VPN rules** → tick it, so rules 2–3 above are the
only IPsec rules and the "only from the peer" restriction actually holds. Everything else on WAN is dropped by
the implicit deny (not logged, to avoid log noise from the internet).

### IPsec — traffic arriving from the branch
| # | Action | Proto | Source | Destination | Port | Covers flow |
|---|---|---|---|---|---|---|
| 1 | Pass | TCP | 10.20.30.0/24 | `h_dc01` | `p_ad_tcp` | dc01 tcp/53, tcp/88, tcp/135, tcp/389, tcp/445, tcp/464, tcp/3268 from BR-USERS |
| 2 | Pass | UDP | 10.20.30.0/24 | `h_dc01` | `p_ad_udp` | dc01 udp/53, udp/88, udp/123, udp/389, udp/464 from BR-USERS |
| 3 | Pass | UDP | 10.20.99.1 (fw-br) | `h_wazuh01` | 514 | fw-br's syslog to the SIEM (guide 8) |
| 4 | Block + log | any | any | any | any | — |

## 2.3 Rules on fw-br
### BR_USERS
| # | Action | Proto | Destination | Port | Why |
|---|---|---|---|---|---|
| 1 | Pass | TCP | 10.10.20.11 | `p_ad_tcp` | domain services at HQ, over the tunnel |
| 2 | Pass | UDP | 10.10.20.11 | `p_ad_udp` | domain services at HQ, over the tunnel |
| 3 | Block + log | TCP/UDP | any | 53, 853 | no outside DNS |
| 4 | Block + log | any | 10.10.0.0/16 | any | nothing else at HQ |
| 5 | Pass | TCP | Internet | 80, 443 | local internet breakout |
| 6 | Block + log | any | any | any | — |

### IPsec — traffic arriving from HQ
| # | Action | Proto | Source | Destination | Port | Why |
|---|---|---|---|---|---|---|
| 1 | Pass | TCP | 10.10.99.0/24 (MGMT) | 10.20.99.1 | 443 | HQ administrators manage fw-br (fw-br-mgmt tcp/443) |
| 2 | Block + log | any | any | any | any | — |

### WAN (fw-br)
Mirror of fw-hq's WAN rules 2–3 with source 203.0.113.1; no published services.

## 2.4 Check your work
1. **Firewall ▸ Log Files ▸ Live View**, filter on *block*: generate traffic from a probe host and confirm the
   drops you expect.
2. Run the checker from every zone ([../validation.md](../validation.md)); every row must read **PASS**.
