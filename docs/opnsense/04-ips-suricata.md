# 4. Intrusion prevention with Suricata

Applies to **OPNsense 26.7.x** (Suricata is built in).

## 4.1 Enable IPS
**Services ▸ Intrusion Detection ▸ Administration ▸ Settings**:

| Setting | Value | Why |
|---|---|---|
| Enabled | ✔ | |
| IPS mode | ✔ | Drop matching traffic instead of only alerting |
| Promiscuous mode | ✘ | Not needed with VLAN interfaces |
| Pattern matcher | Hyperscan (if the CPU supports it), otherwise Aho-Corasick | Performance |
| Interfaces | WAN, USERS | Inspect traffic from the internet and from the zone most likely to be compromised |
| Home networks | 10.10.0.0/16, 10.20.0.0/16 | So rules know which side is "inside" |
| Log package payload | ✘ | Keeps personal data out of the logs |

IPS mode needs a NIC that supports netmap; with VirtIO on Proxmox, disable hardware offloading first
(**Interfaces ▸ Settings**: tick *Disable hardware checksum offload*, *TSO* and *LRO*, then reboot).

## 4.2 Rule sets
**Download** tab: enable the **ET open** categories relevant to a small office (e.g. `emerging-malware`,
`emerging-exploit`, `emerging-scan`, `emerging-web_client`, `emerging-policy`), then **Download & Update
Rules**. **Schedule** tab: update daily.

**Policy** tab: create a policy *"IPS drop high-confidence"* that sets action **Drop** for rules in the
enabled categories with signature severity *Major* or *Critical*; everything else stays *Alert*. Why: dropping
every ET rule causes false positives that break legitimate traffic; start with alerts and promote rules to
drop once they're proven quiet.

## 4.3 Validation (harmless)
From `probe-users`, request a page that is designed to trigger a well-known IDS test signature without doing
anything harmful:

```bash
curl http://testmynids.org/uid/index.html
```

It returns the text of a `uid=0(root)` response, which matches the classic *"ATTACK_RESPONSE id check
returned root"* signature. Expected: an alert (or drop) in **Services ▸ Intrusion Detection ▸ Administration ▸
Alerts**, and the same event in Wazuh through syslog ([08-admin-hardening.md](08-admin-hardening.md)). Record
the result in [../../tests/test-plan.md](../../tests/test-plan.md).

This needs the optional update uplink (guide 1.4) because the test page is on the real internet. Without it,
skip this check and note it in the test plan.
