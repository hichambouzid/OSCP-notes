# Troubleshooting cards — isolate the failing layer

Use your own machine and assigned lab scope only. These are diagnosis reminders, not ways to bypass authentication or access controls.

## 1. The five-minute reset

- [ ] Read the exact error and record the command, client version and timestamp privately.
- [ ] Confirm you are on the intended machine and in the intended shell.
- [ ] Check local VPN interface, routing, DNS and clock.
- [ ] Separate network connectivity from authentication and authorization.
- [ ] Compare observed facts with assumptions. Change one variable at a time.
- [ ] If an exam infrastructure problem persists, contact the proctor through official channels, not an AI or other candidate.

## 2. Error-to-layer table

| Symptom | Likely layer | What to verify |
| --- | --- | --- |
| Network unreachable / no route | Local routing | VPN status, assigned subnet, route selection. |
| Connection timed out | Transport / filtering | Correct endpoint, service status, VPN and timeout conditions; not proof of closed port. |
| Connection refused | Transport | Endpoint reached a refusal or reset; check correct port and service status. |
| Name resolution failure | DNS | Spelling, resolver, expected domain and VPN DNS configuration. |
| TLS certificate mismatch | TLS | Expected hostname, certificate identity, trust chain and clock. |
| HTTP 301/302 | Application | Destination, scheme and host; redirects are not automatic vulnerabilities. |
| HTTP 401 | Authentication | Required credentials or authentication scheme. |
| HTTP 403 | Authorization / policy | Identity, permissions and request context. |
| HTTP 404 | Application | Route, host, method or deliberately hidden resource. |
| HTTP 429 | Rate limiting | Stop repeated requests; review documented rate limits. |
| HTTP 500 | Application | Server error; not proof of a vulnerability. |
| SSH host key changed | Identity / trust | Verify against authorized source before trusting; do not blindly disable checks. |
| SMB access denied | Authorization | Correct domain identity, share and filesystem policy. |
| Kerberos clock skew | Authentication | Check time, timezone and time source. |
| Shell command not found | Local runtime | PATH, executable name, installed version and shell dialect. |
| Permission denied | OS authorization | Identity, ownership and effective permissions; do not assume administrator rights. |
| No space left | Storage | Available space and private evidence directory. |

## 3. Local-only checks on Kali

```bash
whoami
hostname
ip -br addr
ip route
date -Is
timedatectl status
cat /etc/resolv.conf
df -h
command -v python3
python3 --version
```

For an already assigned IP, `ip route get "$IP"` displays the selected local route, if IP has been set correctly. It does not establish remote access.

## 4. Check existing authorized Windows session

```powershell
whoami /all
hostname
ipconfig /all
route print
Get-Date
Get-Location
Get-Command Get-ChildItem
```

Know which machine produced the output; the prompt may be misleading after switching shells.

## 5. Web interpretation reminders

- A browser and command-line client may follow redirects differently.
- HTTP status, headers and body are different observations.
- A login page returning 200 does not mean a login succeeded.
- HTTPS encrypts transport, not necessarily the correctness of the application.
- Hostnames matter for virtual hosting and TLS identity.
- Record a harmless baseline before drawing a security conclusion.

## 6. Existing-session context reminders

- Linux UID, effective identity and group memberships are distinct.
- Windows group membership, token integrity and effective privileges are distinct.
- A successful login does not prove permission to read any file.
- A listening socket on loopback is not automatically reachable from another machine.
- Reboots or authorized reverts may invalidate earlier observations. Record what changed.

## 7. Practice journal

| Time | Observed error | Suspected layer | Evidence | Resolution or next learning task |
| --- | --- | --- | --- | --- |
| | | | | |

If stuck after a bounded investigation, write a concrete question to revisit and move to another assigned objective. During the real exam, do not ask third parties for hints.

[Back to beginner desk reference](../00-Quick-Reference/beginner-desk-reference.md)
