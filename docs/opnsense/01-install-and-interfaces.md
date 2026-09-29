# 1. Install OPNsense and create the interfaces

Applies to **OPNsense 26.7.x** on Proxmox VE. Menu paths can move slightly between minor releases.

## 1.1 Proxmox networking
Create two Linux bridges on the Proxmox host (**Datacenter ▸ node ▸ System ▸ Network**):

| Bridge | VLAN aware | Purpose |
|---|---|---|
| `vmbr10` | Yes | HQ internal network; VLANs 20, 30, 40, 50, 99 are tagged on it |
| `vmbr11` | Yes | Branch internal network; VLANs 30 and 99 |
| `vmbr20` | No | Simulated internet (203.0.113.0/24) shared by both firewalls and `probe-internet` |

No bridge has a physical port, except an optional uplink on fw-hq for package updates (section 1.4).
Why: the lab stays isolated from the home network; only the firewall decides what leaves it.

## 1.2 Firewall VMs
| VM | vCPU / RAM / disk | NIC 1 | NIC 2 |
|---|---|---|---|
| fw-hq | 2 / 4 GB / 32 GB | `vmbr20` (WAN) | `vmbr10` (trunk) |
| fw-br | 2 / 4 GB / 32 GB | `vmbr20` (WAN) | `vmbr11` (trunk) |

Use the **VirtIO** NIC model and install from the OPNsense 26.7 DVD image with ZFS. After the first boot,
update to the latest 26.7.x patch (**System ▸ Firmware ▸ Status ▸ Check for updates**).

## 1.3 VLANs and interface addresses
**Interfaces ▸ Devices ▸ VLAN**: create one VLAN device per zone on the trunk NIC, then assign each one in
**Interfaces ▸ Assignments**, enable it and give it the gateway address (`.1`) of its subnet.

| Firewall | Interface | VLAN tag | Address |
|---|---|---|---|
| fw-hq | SERVERS | 20 | 10.10.20.1/24 |
| fw-hq | USERS | 30 | 10.10.30.1/24 |
| fw-hq | GUEST | 40 | 10.10.40.1/24 |
| fw-hq | DMZ | 50 | 10.10.50.1/24 |
| fw-hq | MGMT | 99 | 10.10.99.1/24 |
| fw-hq | WAN | — | 203.0.113.1/24 |
| fw-br | BR_USERS | 30 | 10.20.30.1/24 |
| fw-br | BR_MGMT | 99 | 10.20.99.1/24 |
| fw-br | WAN | — | 203.0.113.2/24 |

On both WAN interfaces keep **Block private networks** enabled, but turn **Block bogon networks** off: the
simulated internet uses 203.0.113.0/24, a documentation range that the bogon list would drop. This is a lab-only
exception; on a real internet link keep both enabled.

## 1.4 Optional update uplink
To download packages and rule sets, add a third NIC on fw-hq connected to your real network and set it as a
second WAN used **only by the firewall itself** (no NAT for lab zones through it except the explicit update
rules in [03-nat-and-egress.md](03-nat-and-egress.md)).

## 1.5 DHCP and DNS for the zones
**Services ▸ Dnsmasq DNS & DHCP** (or ISC DHCP if you prefer): enable DHCP on USERS, GUEST and BR_USERS only.
Servers, DMZ and MGMT hosts use the static addresses from [../ip-plan.md](../ip-plan.md). DNS servers to hand
out: **dc01 (10.10.20.11)** in USERS and BR_USERS, because domain-joined Windows machines must resolve the
domain through the domain controller; **the firewall's own address** in GUEST. dc01 forwards everything outside
`lab.local` to the firewall, so the filtering in [05-dns-filtering.md](05-dns-filtering.md) still applies.
