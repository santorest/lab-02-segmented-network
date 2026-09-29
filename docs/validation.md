# Validating the firewall policy

The checker proves, from inside each zone, that every flow in `policy/policy.yaml` is allowed or blocked as
designed. It only opens ordinary TCP connections and sends small UDP datagrams to the lab's own hosts, and
refuses any address outside the policy's `lab_networks`.

## 1. Prepare the probe hosts
Probe hosts are minimal Debian 13 VMs (1 vCPU, 512 MB): `probe-users` (10.10.30.250), `probe-guest`
(10.10.40.250), `probe-branch` (10.20.30.250) and `probe-internet` (203.0.113.100). For the DMZ and MGMT
zones, run the checker on `web01` and `jump01`.

On each of them:

```bash
sudo apt install -y python3 python3-yaml git
git clone https://github.com/santorest/lab-02-segmented-network.git
cd lab-02-segmented-network
```

## 2. Start the listeners on the targets
An allowed flow can only be proven if something answers on the destination port. Run the command for each
target host from [listeners.md](listeners.md) (generated from the policy); hosts whose real services already
listen (the Windows machines, Wazuh and the firewalls) need nothing. Leave the listeners running during the test.

## 3. Run the checker in every zone
```bash
python3 -m labtools.checker --zone USERS      # on probe-users
python3 -m labtools.checker --zone GUEST      # on probe-guest
python3 -m labtools.checker --zone DMZ        # on web01
python3 -m labtools.checker --zone MGMT       # on jump01
python3 -m labtools.checker --zone BR-USERS   # on probe-branch
python3 -m labtools.checker --zone WAN        # on probe-internet
```

Each run prints a table and writes `tests/results/checker-<ZONE>.csv`. The exit code is 0 only if every flow
behaved as expected. Verdicts:

| Verdict | Meaning | Usual cause |
|---|---|---|
| PASS | Behaved as the policy says | — |
| FAIL (blocked) | Should be allowed, but didn't connect | Missing rule, listener not running, service down |
| FAIL (allowed) | Should be blocked, but connected | A rule is too broad, or rule order lets it through |

## 4. Collect the results
Copy the six CSV files to your workstation's `tests/results/`, fill in the manual checks in
[../tests/test-plan.md](../tests/test-plan.md), and share both for the write-up's results section.
