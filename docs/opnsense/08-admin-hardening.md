# 8. Administration hardening, logging and backups

Applies to **OPNsense 26.7.x**.

## 8.1 Where the firewall can be managed from
**System ▸ Settings ▸ Administration**:

| Setting | Value | Why |
|---|---|---|
| Protocol | HTTPS only, certificate from `lab02-ca` | No cleartext admin sessions |
| Listen interfaces | MGMT only | The GUI isn't even reachable from other zones |
| Anti-lockout | enabled; confirm in **Firewall ▸ Rules ▸ MGMT** that the automatic anti-lockout rule sits on MGMT | Keeps MGMT access if a rule mistake happens |
| HTTP Strict Transport Security | ✔ | Browsers never downgrade to HTTP |
| Disable logging of web GUI successful logins | **Leave unticked** | Successful admin logins must stay in the audit trail |
| Session timeout | 15 min | Idle admin sessions close |
| Authentication server | `local-totp` (from guide 7) | Admin logins require a one-time code |
| Secure Shell | enabled, listen on MGMT only, **root login off**, **password login off** | Keys only |

Create a named admin account (not `root`) with an SSH key and a TOTP seed; keep `root` for console recovery
only.

On fw-br do the same with BR_MGMT; it is administered from HQ's MGMT network over the tunnel.

## 8.2 Time
**System ▸ Settings ▸ General**: time servers `pool.ntp.org` via the update uplink. **Services ▸ Network Time**
serves time to the zones; dc01 syncs from the firewall (10.10.20.1, allowed in guide 2) and the domain members
sync from dc01. In a lab with no uplink, the firewall is the reference clock. Why: log correlation across the
firewall, Wazuh and Windows needs consistent clocks, and Kerberos fails beyond 5 minutes of skew.

## 8.3 Logs to the SIEM (Lab 01)
**System ▸ Settings ▸ Logging ▸ Remote ▸ +**:

| Setting | Value |
|---|---|
| Transport | UDP(4) |
| Applications | filter (firewall), suricata, openvpn, ipsec, audit (admin logins) |
| Levels | info and above |
| Hostname | 10.10.20.10 (wazuh01) |
| Port | 514 |

On **fw-br**, set the remote target's **Source address** to **BR_MGMT** (10.20.99.1): the default source is the
WAN address, which doesn't match the IPsec tunnel's networks, so the logs would leave unencrypted and be dropped
at HQ. fw-hq's IPsec rule 3 (guide 2) lets 10.20.99.1 → wazuh01 UDP 514 through. On wazuh01, accept syslog from
10.10.20.1 and 10.20.99.1 (see Lab 01, `configs/wazuh`). Why: denied
connections, IPS alerts, VPN logins and admin logins are correlated with endpoint events in one place.

## 8.4 Backups
**System ▸ Configuration ▸ Backups**: enable the scheduled backup to a location you control with
**encryption** enabled, and keep the encryption password in your password manager. Test a restore on a
spare VM once. Never publish a raw `config.xml`; see [../sanitize-config.md](../sanitize-config.md).

## 8.5 Validation
- From `probe-users`: `curl -k https://10.10.99.1` and `ssh 10.10.99.1` both fail (the checker's
  `USERS → fw-hq-mgmt` deny flows).
- From `jump01`: GUI login asks for the TOTP code; SSH works only with the key.
- In Wazuh: a failed admin login on the firewall appears as an event.
