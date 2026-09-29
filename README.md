# Lab 02 — Segmented SMB network on OPNsense

Segmented network for a fictional 40-person company (head office + branch) on OPNsense 26.7: default-deny
zones, Suricata IPS, DNS filtering, site-to-site IPsec, OpenVPN with TOTP, hardened administration and an
automated, harmless validation of the firewall policy.

**Category:** Network Security & Administration · **Status:** reference design — ready to build

## Repository layout
```
policy/policy.yaml        single source of truth: zones, hosts, flows (+ why)
docs/ip-plan.md           ┐
docs/rules.md             ├ generated from the policy (python -m labtools.render)
docs/listeners.md         ┘
docs/opnsense/            step-by-step OPNsense 26.7 configuration guides (01–08)
docs/validation.md        how to run the reachability checker in every zone
docs/sanitize-config.md   how to publish a firewall config without secrets
labtools/                 policy model, renderer, checker, listener (Python stdlib + PyYAML)
tests/unit/               pytest suite (run in CI)
```

## Development
```bash
python -m pip install -r requirements-dev.txt
python -m pytest
python -m labtools.render --check   # docs match the policy
```

> All testing is performed only in an isolated lab environment I own.

## License
[MIT](LICENSE)
