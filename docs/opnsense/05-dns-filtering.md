# 5. DNS filtering with Unbound

Applies to **OPNsense 26.7.x**. Replaces the web-filtering role a commercial firewall's subscription would
play, using free public blocklists.

## 5.1 Resolver
**Services ▸ Unbound DNS ▸ General**: enable Unbound, listen on SERVERS, GUEST, DMZ and MGMT; enable
**DNSSEC**. Internal names (`lab.local`) are forwarded to dc01: **Query Forwarding** → domain `lab.local`,
server 10.10.20.11.

On **dc01**, set the DNS server's forwarder to the firewall (10.10.20.1) and disable root hints. Resulting
chain: staff machines → dc01 (domain names) → firewall Unbound (everything else, filtered). Guests ask the
firewall directly. Why: all external lookups pass through one filtered, logged resolver without breaking
Active Directory.

## 5.2 Blocklists
**Services ▸ Unbound DNS ▸ Blocklist**: enable, and select a small set of well-maintained lists (for example
the abuse.ch URLhaus and a malware/phishing list). Keep advertising lists off for staff zones unless the
company wants them, to avoid breaking business sites. Schedule the blocklist update daily.

## 5.3 Force clients through the resolver
Clients could bypass filtering by using another DNS server, so on USERS, GUEST and BR_USERS:

| Zone | # | Action | Proto | Destination | Port | Why |
|---|---|---|---|---|---|---|
| USERS, BR_USERS | 1 | Pass | UDP (and TCP) | `h_dc01` | 53 | Domain DNS (dc01 forwards to the filtered resolver) |
| GUEST | 1 | Pass | TCP/UDP | this interface's address | 53 | The filtered resolver |
| all three | 2 | Block + log | TCP/UDP | any | 53, 853 | No other DNS or DNS-over-TLS servers |

Place these above the internet-access rules from [02-firewall-rules.md](02-firewall-rules.md).

## 5.4 Validation
From `probe-users`: `dig @10.10.20.11 <a domain on the blocklist>` must return `0.0.0.0` (or NXDOMAIN),
proving the dc01 → firewall chain is filtered; `dig @8.8.8.8 example.com` must time out. From `probe-guest`,
repeat the first check against 10.10.40.1. Record the results in the test plan.
