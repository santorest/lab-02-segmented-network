# 7. Remote access: OpenVPN with TOTP

Applies to **OPNsense 26.7.x** (**VPN ▸ OpenVPN ▸ Instances**).

## 7.1 Two-factor authentication server
**System ▸ Access ▸ Servers ▸ +**: type **Local + Timebased One Time Password**, name `local-totp`, token
length 6, time window 30 s. Tick **Reverse token order** so users type their password first and the 6-digit code
after it (`password123456`); with it unticked, OPNsense expects the code **first** (`123456password`). Whichever
you choose, tell users the order; a wrong order is the most common cause of failed logins.

For each remote user: **System ▸ Access ▸ Users ▸ edit ▸ OTP seed ▸ Generate**, and have the
user scan the QR code with an authenticator app. Store nothing about the seed outside the firewall.

## 7.2 Server instance
| Setting | Value | Why |
|---|---|---|
| Role | Server | |
| Protocol / port | UDP 1194 on WAN | UDP performs better for tunnels |
| Tunnel network | 10.10.60.0/24 | Remote users get their own subnet, visible as a separate source in logs |
| Certificate | server certificate from `lab02-ca` | Clients verify they reach the real firewall |
| Verify client certificate | Required | Device must hold a client certificate **and** the user must know password + TOTP |
| Authentication | `local-totp` | Username + password + one-time code |
| Data ciphers | AES-256-GCM | Authenticated encryption |
| TLS static key | tls-crypt | Hides and authenticates the TLS handshake; drops unauthenticated packets early |
| Redirect gateway | Off | Split tunnel: only 10.10.0.0/16 and 10.20.0.0/16 go through the VPN |
| Local networks | 10.10.20.0/24 | Remote staff reach servers, nothing else |

## 7.3 Firewall rules
On the **OpenVPN** interface give remote users the same access as USERS (the USERS rows in
[02-firewall-rules.md](02-firewall-rules.md) with source 10.10.60.0/24), then *Block + log any*. The pool is
inside 10.10.0.0/16, so it is already covered by `net_internal` and by the policy's `lab_networks`.

## 7.4 Client export and validation
**VPN ▸ OpenVPN ▸ Client Export**: export a profile for a test user. From a machine on the simulated internet
(`probe-internet`):
1. Connect with password + current TOTP code → succeeds; `dc01` TCP 445 reachable.
2. Connect with the password but a wrong or missing code → refused (**System ▸ Log Files ▸ General** shows the
   failed authentication).
3. Record both outcomes in the test plan.
