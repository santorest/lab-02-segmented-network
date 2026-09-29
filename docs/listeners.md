<!-- Generated from policy/policy.yaml by `python -m labtools.render`. Do not edit by hand. -->

# Listener commands

Run on each target before the checker, so allowed flows have something to answer. Skip ports where the real service already listens.

| Host | IP | Command |
|---|---|---|
| wazuh01 | 10.10.20.10 | none: its real services answer (tcp 443 1514 1515) |
| dc01 | 10.10.20.11 | none: its real services answer (tcp 53 88 135 389 445 464 3268 3389, udp 53 88 123 389 464) |
| srv01 | 10.10.20.12 | none: its real services answer (tcp 22) |
| ws01 | 10.10.30.21 | none: its real services answer (tcp 445) |
| web01 | 10.10.50.10 | none: its real services answer (tcp 22 443) |
| fw-hq-mgmt | 10.10.99.1 | none: its real services answer (tcp 22 443) |
| jump01 | 10.10.99.20 | none: its real services answer (tcp 22) |
| fw-br-mgmt | 10.20.99.1 | none: its real services answer (tcp 443) |
