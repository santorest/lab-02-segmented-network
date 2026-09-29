# Sanitizing an OPNsense configuration before publishing

`config.xml` (**System ▸ Configuration ▸ Backups ▸ Download**) contains secrets. The repository's
`.gitignore` blocks `config*.xml` so a raw export can't be committed by accident; publish only a sanitized
copy named `configs/fw-hq.sanitized.xml.txt` (or similar).

## What to remove or replace
| Element | Where in the XML | Replace with |
|---|---|---|
| User password hashes | `<system><user><password>` | `REDACTED` |
| TOTP / OTP seeds | `<otp_seed>` | `REDACTED` |
| SSH authorized keys | `<authorizedkeys>` | `REDACTED` |
| Private keys | `<prv>` inside `<cert>` and `<ca>` | `REDACTED` |
| Certificates (optional) | `<crt>` | keep the CA's public certificate only if you want; otherwise `REDACTED` |
| IPsec / OpenVPN static keys | `<tls>`, `<psk>`, `<pre-shared-key>` | `REDACTED` |
| API keys | `<apikeys>` | remove the element |
| Backup encryption / cloud credentials | `<backup>` section | remove the section |
| Serial numbers, UUIDs you consider identifying | `<uuid>`, hardware serials | optional |

Real public IP addresses and hostnames must not appear either; this lab only uses the ranges in
`policy/policy.yaml`.

## Checklist
1. Export, then work on a **copy** outside the repository.
2. Replace every element in the table.
3. Search the copy for `BEGIN`, `PRIVATE`, `$2y$`, `$6$`, `otp`, `psk`, `key` and review each hit.
4. Run `gitleaks detect --no-git --source <copy>` locally; it must report no leaks.
5. Only then copy it into `configs/` and commit. CI runs gitleaks on every push as a safety net.
