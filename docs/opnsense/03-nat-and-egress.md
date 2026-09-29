# 3. NAT and egress control

Applies to **OPNsense 26.7.x**.

## 3.1 Port forward: the only published service
**Firewall ▸ NAT ▸ Port Forward** on fw-hq:

| Interface | Protocol | Destination | Port | Redirect target | Redirect port | Filter rule |
|---|---|---|---|---|---|---|
| WAN | TCP | WAN address | 443 | 10.10.50.10 (`h_web01`) | 443 | *Pass* (creates the linked WAN rule) |

Why: only HTTPS on the web server is reachable from the internet; SSH on web01 (22) is deliberately **not**
forwarded, and the checker's `WAN → web01 tcp/22 deny` flow proves it.

## 3.2 Outbound NAT
**Firewall ▸ NAT ▸ Outbound**: switch to **Manual** mode (Hybrid would keep the automatic rules that translate
*every* internal subnet) and create only these rules:

| Interface | Source | Translation |
|---|---|---|
| WAN | 10.10.30.0/24 (USERS) | Interface address |
| WAN | 10.10.40.0/24 (GUEST) | Interface address |
| WAN | 10.10.50.10 (web01, updates only) | Interface address |

SERVERS and MGMT get no outbound NAT. The **filter rules** are what actually stop them reaching the internet
(guide 2: both zones end with *Block + log*); missing NAT is a second layer, because an untranslated private
address can't get replies from the internet anyway. Together they remove a whole class of data-exfiltration and
command-and-control paths. Their updates come through a temporarily enabled, logged rule.

## 3.3 Egress for the DMZ
Create an alias `update_mirrors` (type **Host(s)**, FQDNs of the Debian mirrors web01 uses, e.g.
`deb.debian.org`, `security.debian.org`) and switch web01's apt sources to **https://** (apt uses port 80 by
default). The DMZ rule *Pass TCP 443 → update_mirrors* is the only outbound
traffic web01 may start; everything else is blocked and logged
([02-firewall-rules.md](02-firewall-rules.md)).

## 3.4 Branch
fw-br translates BR_USERS to its own WAN address for internet access. Traffic to 10.10.0.0/16 is **not**
translated: it goes through the IPsec tunnel ([06-ipsec-site-to-site.md](06-ipsec-site-to-site.md)), so HQ
sees the real branch addresses in its logs.
