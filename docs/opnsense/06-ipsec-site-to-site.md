# 6. Site-to-site IPsec (HQ ↔ branch)

Applies to **OPNsense 26.7.x** (**VPN ▸ IPsec ▸ Connections**, the swanctl-based interface).

## 6.1 Certificates instead of a pre-shared key
On fw-hq, **System ▸ Trust ▸ Authorities**: create an internal CA `lab02-ca` (RSA 4096 or ECDSA P-384,
10-year lifetime). **System ▸ Trust ▸ Certificates**: issue a server certificate for each firewall with the
SAN set to its WAN address (`203.0.113.1`, `203.0.113.2`). Import the CA and fw-br's certificate + key on fw-br.

Why: a pre-shared key is one static secret shared by both sides and often reused; certificates identify each
firewall individually and can be revoked.

## 6.2 Parameters
| Setting | Value | Why |
|---|---|---|
| IKE version | IKEv2 | Simpler, more robust negotiation than IKEv1; required for modern cipher suites |
| Phase 1 encryption | AES-256-GCM | Authenticated encryption; no separate integrity algorithm needed |
| Phase 1 PRF | SHA-384 | Matches the 192-bit security level of the key exchange |
| Phase 1 DH group | 20 (ECP-384) | Strong, widely supported elliptic-curve group |
| Phase 1 lifetime | 28 800 s (8 h) | Common default; limits how long one key is used |
| Authentication | Certificates (`lab02-ca`) | See 6.1 |
| Phase 2 protocol | ESP | Encrypts the payload (AH doesn't) |
| Phase 2 encryption | AES-256-GCM | As phase 1 |
| Phase 2 PFS group | 20 (ECP-384) | Perfect forward secrecy: a stolen phase 1 key can't decrypt past tunnels |
| Phase 2 lifetime | 3 600 s (1 h) | Re-keys data encryption hourly |
| Local / remote networks | 10.10.0.0/16 ↔ 10.20.0.0/16 | Only internal networks use the tunnel; internet traffic doesn't |
| Dead peer detection | 30 s, restart | Re-establishes the tunnel after an outage |

Create the connection on both sides with mirrored local/remote settings (**Connections ▸ +**, then add a
**Child** with the phase 2 values).

## 6.3 Firewall rules
- **WAN:** allow UDP 500 and 4500 **only from the peer's WAN address** (fw-hq allows 203.0.113.2, fw-br allows
  203.0.113.1).
- **IPsec interface:** only the flows in the policy (see the IPsec section of
  [02-firewall-rules.md](02-firewall-rules.md)); everything else from the tunnel is blocked and logged.

## 6.4 Validation
1. **VPN ▸ IPsec ▸ Status Overview**: phase 1 and phase 2 *installed* on both sides.
2. From `probe-branch`: `python3 -m labtools.checker --zone BR-USERS` — allowed flows to dc01 pass, the rest
   are blocked.
3. Capture on fw-hq's WAN (**Interfaces ▸ Diagnostics ▸ Packet Capture**, filter host 203.0.113.2) while the
   checker runs: only ESP / UDP 4500 packets appear, never the inner TCP 445 — proof the traffic is encrypted.
