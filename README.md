# OSCP Notes — Practical Enumeration and Lab Workflow

Hands-on notes for **authorized OSCP labs and penetration testing practice**. Commands use placeholders: replace sample addresses, domains, ports, share names and usernames with values from your assigned target.

## Enumeration — follow these steps

1. **[Host Discovery](01-Enumeration/host-discovery.md)** — Check VPN/routing, identify reachable hosts, and review UDP scan basics.
2. **[Nmap Enumeration](01-Enumeration/nmap.md)** — Scan all TCP ports, investigate UDP ports, identify versions, and triage potential vulnerabilities.
3. **[Service-Specific Enumeration](01-Enumeration/service-enumeration.md)** — Follow practical HTTP, SMB, FTP, SSH, DNS, SNMP, SMTP, NFS, RDP, and database walkthroughs.

## Web application testing

4. **[Web Application Enumeration](02-Web-Application/web-enumeration.md)** — Fingerprint web apps, discover content and virtual hosts, inspect authentication and APIs, and triage possible vulnerabilities.
5. **[Web Vulnerability Testing](02-Web-Application/web-vulnerability-testing.md)** — Validate SQLi, XSS, traversal/LFI, file uploads, authentication, access control, command injection and SSTI using controlled lab tests.

## Quick start

```bash
export IP=192.168.56.101 # Replace with assigned lab target
mkdir -p scans evidence
ip route get "$IP"
sudo nmap -Pn -sS -p- -oA scans/tcp-all "$IP"
sudo nmap -Pn -sU --top-ports 100 -oA scans/udp-top100 "$IP"
```

Continue with the linked guides to enumerate detected services. `-Pn` skips host discovery and does not confirm the target is online.

## Working principles

- Scan **only** authorized targets and networks.
- Save raw scan output and record evidence for every conclusion.
- Treat banners, CVE matches and automated script results as **leads**, not verified vulnerabilities.
- Prefer targeted, reviewed checks over indiscriminate vulnerability scripts.
- Never commit real passwords, private files, tokens, or sensitive lab evidence to this public repository.

## Repository status

The enumeration and web-application enumeration guides above are available. Additional sections for initial access, privilege escalation, Active Directory, password attacks, pivoting, exam workflow, and lab writeups are planned but are **not yet published here**.
