<!-- Generated from policy/policy.yaml by `python -m labtools.render`. Do not edit by hand. -->

# Policy flows

Everything not listed as `allow` is denied by default. `deny` rows are listed so the checker proves them.

| From | To | Service | Action | Why |
|---|---|---|---|---|
| USERS | dc01 (SERVERS, 10.10.20.11) | tcp/88 | allow | Kerberos: domain logon |
| USERS | dc01 (SERVERS, 10.10.20.11) | tcp/389 | allow | LDAP: directory lookups and group policy |
| USERS | dc01 (SERVERS, 10.10.20.11) | tcp/445 | allow | SMB: department file shares and GPO files |
| USERS | dc01 (SERVERS, 10.10.20.11) | udp/53 | allow | DNS: internal name resolution |
| USERS | dc01 (SERVERS, 10.10.20.11) | tcp/53 | allow | DNS over TCP: large answers and zone lookups by the domain client |
| USERS | dc01 (SERVERS, 10.10.20.11) | udp/88 | allow | Kerberos over UDP |
| USERS | dc01 (SERVERS, 10.10.20.11) | udp/123 | allow | Time sync with the domain controller (Kerberos fails beyond 5 minutes of skew) |
| USERS | dc01 (SERVERS, 10.10.20.11) | tcp/135 | allow | RPC endpoint mapper (Netlogon, Group Policy); the dynamic RPC range 49152-65535 is allowed by the same rule |
| USERS | dc01 (SERVERS, 10.10.20.11) | udp/389 | allow | CLDAP: the domain-controller locator |
| USERS | dc01 (SERVERS, 10.10.20.11) | tcp/464 | allow | Kerberos password change |
| USERS | dc01 (SERVERS, 10.10.20.11) | udp/464 | allow | Kerberos password change |
| USERS | dc01 (SERVERS, 10.10.20.11) | tcp/3268 | allow | Global catalog lookups |
| USERS | web01 (DMZ, 10.10.50.10) | tcp/443 | allow | Staff use the company's public website |
| USERS | wazuh01 (SERVERS, 10.10.20.10) | tcp/1514 | allow | Wazuh agent on ws01 sends events to the SIEM (Lab 01) |
| USERS | wazuh01 (SERVERS, 10.10.20.10) | tcp/1515 | allow | Wazuh agent enrollment (Lab 01) |
| USERS | wazuh01 (SERVERS, 10.10.20.10) | tcp/443 | deny | SIEM dashboard is for administrators (MGMT) only |
| USERS | srv01 (SERVERS, 10.10.20.12) | tcp/22 | deny | Server administration only from MGMT |
| USERS | fw-hq-mgmt (MGMT, 10.10.99.1) | tcp/443 | deny | Firewall GUI only from MGMT |
| USERS | fw-hq-mgmt (MGMT, 10.10.99.1) | tcp/22 | deny | Firewall SSH only from MGMT |
| USERS | jump01 (MGMT, 10.10.99.20) | tcp/22 | deny | A compromised workstation must not reach admin hosts |
| GUEST | dc01 (SERVERS, 10.10.20.11) | tcp/445 | deny | Guests never reach internal file shares |
| GUEST | dc01 (SERVERS, 10.10.20.11) | udp/53 | deny | Guests use the firewall's resolver, not internal DNS |
| GUEST | srv01 (SERVERS, 10.10.20.12) | tcp/22 | deny | Guests never reach internal servers |
| GUEST | ws01 (USERS, 10.10.30.21) | tcp/445 | deny | No guest-to-staff device traffic |
| GUEST | fw-hq-mgmt (MGMT, 10.10.99.1) | tcp/443 | deny | Firewall GUI only from MGMT |
| GUEST | web01 (DMZ, 10.10.50.10) | tcp/443 | allow | Guests may browse the public website like any visitor |
| DMZ | dc01 (SERVERS, 10.10.20.11) | tcp/389 | deny | A compromised web server must not query the directory |
| DMZ | dc01 (SERVERS, 10.10.20.11) | tcp/445 | deny | No lateral movement from the DMZ |
| DMZ | srv01 (SERVERS, 10.10.20.12) | tcp/22 | deny | No lateral movement from the DMZ |
| DMZ | ws01 (USERS, 10.10.30.21) | tcp/445 | deny | No lateral movement from the DMZ |
| DMZ | fw-hq-mgmt (MGMT, 10.10.99.1) | tcp/443 | deny | Firewall GUI only from MGMT |
| MGMT | wazuh01 (SERVERS, 10.10.20.10) | tcp/443 | allow | Administrators use the SIEM dashboard |
| MGMT | srv01 (SERVERS, 10.10.20.12) | tcp/22 | allow | Server administration over SSH (keys only) |
| MGMT | dc01 (SERVERS, 10.10.20.11) | tcp/3389 | allow | Domain controller administration over RDP |
| MGMT | web01 (DMZ, 10.10.50.10) | tcp/22 | allow | Web server administration over SSH (keys only) |
| MGMT | fw-br-mgmt (BR-MGMT, 10.20.99.1) | tcp/443 | allow | Branch firewall administered from HQ over the tunnel |
| BR-USERS | dc01 (SERVERS, 10.10.20.11) | tcp/88 | allow | Kerberos: branch staff log on to the HQ domain |
| BR-USERS | dc01 (SERVERS, 10.10.20.11) | tcp/445 | allow | SMB: branch staff use HQ file shares |
| BR-USERS | dc01 (SERVERS, 10.10.20.11) | udp/53 | allow | DNS: internal name resolution over the tunnel |
| BR-USERS | dc01 (SERVERS, 10.10.20.11) | tcp/389 | allow | LDAP: directory lookups and group policy |
| BR-USERS | dc01 (SERVERS, 10.10.20.11) | tcp/53 | allow | DNS over TCP: large answers and zone lookups by the domain client |
| BR-USERS | dc01 (SERVERS, 10.10.20.11) | udp/88 | allow | Kerberos over UDP |
| BR-USERS | dc01 (SERVERS, 10.10.20.11) | udp/123 | allow | Time sync with the domain controller (Kerberos fails beyond 5 minutes of skew) |
| BR-USERS | dc01 (SERVERS, 10.10.20.11) | tcp/135 | allow | RPC endpoint mapper (Netlogon, Group Policy); the dynamic RPC range 49152-65535 is allowed by the same rule |
| BR-USERS | dc01 (SERVERS, 10.10.20.11) | udp/389 | allow | CLDAP: the domain-controller locator |
| BR-USERS | dc01 (SERVERS, 10.10.20.11) | tcp/464 | allow | Kerberos password change |
| BR-USERS | dc01 (SERVERS, 10.10.20.11) | udp/464 | allow | Kerberos password change |
| BR-USERS | dc01 (SERVERS, 10.10.20.11) | tcp/3268 | allow | Global catalog lookups |
| BR-USERS | srv01 (SERVERS, 10.10.20.12) | tcp/22 | deny | Server administration only from MGMT |
| BR-USERS | wazuh01 (SERVERS, 10.10.20.10) | tcp/443 | deny | SIEM dashboard is for administrators only |
| BR-USERS | fw-hq-mgmt (MGMT, 10.10.99.1) | tcp/443 | deny | Firewall GUI only from MGMT |
| WAN | web01 (DMZ, 10.10.50.10) via 203.0.113.1 | tcp/443 | allow | The only published service: HTTPS forwarded to the web server |
| WAN | web01 (DMZ, 10.10.50.10) via 203.0.113.1 | tcp/80 | deny | No plain-HTTP service is published |
| WAN | web01 (DMZ, 10.10.50.10) via 203.0.113.1 | tcp/22 | deny | SSH is never exposed to the internet |
| WAN | dc01 (SERVERS, 10.10.20.11) via 203.0.113.1 | tcp/445 | deny | Internal services are never exposed |
| WAN | dc01 (SERVERS, 10.10.20.11) via 203.0.113.1 | tcp/3389 | deny | Remote desktop is never exposed |
