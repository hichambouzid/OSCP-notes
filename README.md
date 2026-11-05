# OSCP Notes — Step-by-Step Practical Cheat Sheet

A practical, **exam-focused study reference** for authorized OSCP labs and penetration-testing practice. This repository brings together enumeration, manual web testing, initial access, Linux/Windows privilege escalation, Active Directory, passwords, pivoting, and report preparation.

**Important:** All targets, addresses, usernames, domains and commands are **illustrative** unless from your own assigned lab. Test only hosts and applications explicitly in scope. Nothing here authorizes testing third-party systems.

## Start here

**[Open the one-page OSCP Quick Reference](00-Quick-Reference/quick-reference.md)** — fastest entry point during practice: scan → enumerate → select a verified path → get a foothold → privilege escalate → capture evidence.

## Full documentation

| Chapter | Guide | Purpose |
| --- | --- | --- |
| 00 | [Quick Reference](00-Quick-Reference/quick-reference.md) | Fast commands, decision tables and checklists |
| 01 | [Host Discovery](01-Enumeration/host-discovery.md) | VPN, routing, reachability, scoped host discovery |
| 01 | [Nmap Enumeration](01-Enumeration/nmap.md) | All TCP ports, selected UDP, services, versions and triage |
| 01 | [Service Enumeration](01-Enumeration/service-enumeration.md) | HTTP, SMB, FTP, SSH, DNS, SNMP, SMTP, NFS, RDP and databases |
| 02 | [Web Enumeration](02-Web-Application/web-enumeration.md) | FFUF, subdomains, CVEs, SQLi, LFI, uploads, command injection, XSS, IDOR, SSRF, SSTI and more |
| 02 | [Web Vulnerability Testing](02-Web-Application/web-vulnerability-testing.md) | Manual vulnerability-verification methodology |
| 03 | [Initial Access](03-Initial-Access/initial-access.md) | Verified entry points, shell context and evidence |
| 04 | [Linux Privilege Escalation](04-Privilege-Escalation/linux-privesc.md) | Sudo, SUID, capabilities, cron, services and writable paths |
| 04 | [Windows Privilege Escalation](04-Privilege-Escalation/windows-privesc.md) | Token privileges, services, ACLs, tasks and application paths |
| 05 | [Active Directory Enumeration](05-Active-Directory/ad-enumeration.md) | DC/DNS, accounts, groups, shares, SPNs and relationships |
| 05 | [AD Attack-Path Validation](05-Active-Directory/ad-attack-paths.md) | Credentialed access, SPN/ACL/delegation preconditions and lateral movement |
| 06 | [Password and Hash Auditing](06-Passwords/password-auditing.md) | Identify formats, John/Hashcat offline practice, lockout safety |
| 07 | [Pivoting and Tunneling](07-Pivoting/pivoting-tunneling.md) | SSH -L/-D/-R/-J, SOCKS, route checks and troubleshooting |
| 08 | [Exam Methodology](08-Exam-Workflow/exam-methodology.md) | Target workflow, scoring changes, proof requirements and restrictions |
| 08 | [Reporting](08-Exam-Workflow/reporting.md) | Evidence templates, screenshots, PDF, 7z and final submission |
| 09 | [Practice Lab Writeup Template](09-Lab-Writeups/README.md) | Sanitized learning journal for your authorized practice boxes |

## Repeatable workflow

1. **Scope:** Confirm assigned IPs, domain names, credentials and VPN routes.
2. **Discover:** Scan all TCP ports, check meaningful UDP ports and identify exact services.
3. **Enumerate:** Follow every relevant service guide; capture the important evidence.
4. **Validate:** Choose a specific suspected weakness and reproduce it manually.
5. **Initial access:** Obtain the least complicated authorized foothold.
6. **Privilege escalation:** Apply the relevant Linux/Windows/AD guide based on your current context.
7. **Network movement:** Only if necessary and in scope, use approved credentials/tunnels.
8. **Document:** Save steps, commands and sanitized output privately. Meet proof and reporting requirements.

## Quick start on an assigned Linux/Kali lab

~~~bash
export IP=192.168.56.101     # Replace with assigned target
mkdir -p "$HOME/oscp-local/$IP"/{scans,evidence}
cd "$HOME/oscp-local/$IP"    # Keep private lab data outside public Git
ip route get "$IP"
sudo nmap -Pn -n -sS -p- -T4 \
  --min-rate 300 \
  --max-retries 1 \
  --max-scan-delay 100ms \
  --open -v -oA scans/tcp-all "$IP"
# See Quick Reference for extracting every open TCP port before -sC -sV
sudo nmap -Pn -sU --top-ports 100 -oA scans/udp-top100 "$IP"  # First UDP pass ONLY
~~~

Then use the [Quick Reference](00-Quick-Reference/quick-reference.md) to **extract all open TCP ports and scan every detected service**, followed by [Service-Specific Enumeration](01-Enumeration/service-enumeration.md). The UDP top-100 pass is **not exhaustive**: expand to service-driven ports, top 1,000, or all UDP when warranted and record the coverage. `-Pn` skips host discovery; it does **not** prove a host is online. The chosen scan is **speed-oriented**: `--max-retries 1` and the scan-delay cap can miss services when replies are dropped/rate-limited. Verify questionable results using `sudo nmap -Pn -n -sS -p- --reason -oA scans/tcp-verify "$IP"` and include any additional confirmed ports before service enumeration.

## OSCP+ exam compatibility — checked November 3, 2026

Consult the **[official OffSec OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide)** immediately before the exam; tool features and rules may change.

- **Explicitly permitted:** Nmap/NSE, Nikto, Burp Free and DirBuster.
- **Prohibited:** automatic exploitation such as SQLmap/SQLninja, mass vulnerability scanners, commercial Burp Pro, spoofing, and AI chatbot/LLM assistance during the exam.
- **Restricted:** Metasploit modules and Meterpreter may be used on only **one chosen target**. The official exceptions allow `msfvenom` and `exploit/multi/handler` across targets, with Meterpreter payload use still restricted.
- **Other utilities:** OffSec does not individually certify every tool. Commands shown here are intended for manual investigation or legitimate connectivity; check their actual function, not just the tool name.

**Proof requirements:** OffSec requires control-panel submission of the original proof values and screenshots showing the proof file read via `cat` or `type` in an **interactive target shell**, with target IP visible. Do not use a web shell to satisfy proof capture. Details are in [Exam Methodology](08-Exam-Workflow/exam-methodology.md).

The official guide updated October 21, 2026 notes that **scaled scoring begins for exam starts on or after December 1, 2026 at 08:00 GMT**. Verify the current scoring and requirements for your exam date.

## Repository hygiene

- During the exam, **do not download target files/applications/source to Kali** unless necessary to compromise the target; remove allowed downloads after completing objectives, per the [official guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide).
- Never commit real passwords, hashes, private keys, tokens, target proof files or proprietary exam screenshots.
- Keep raw target-specific evidence in **private, local** notes.
- A banner, CVE result, open port or unusual response is **not** proof of a vulnerability.
- Treat third-party cheat sheets as references to verify rather than instructions to run blindly.
- Document both successful and unsuccessful manual tests.

## Useful references

- [OffSec OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide)
- [OffSec AI Usage Policy](https://help.offsec.com/hc/en-us/articles/35549468971156-AI-Usage-Policy-in-OffSec-Exams)
- [OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [PortSwigger Web Security Academy](https://portswigger.net/web-security)
- [dudisamarel/OSCP-Notes](https://github.com/dudisamarel/OSCP-Notes) — topic-organized community reference
- [0xsyr0/OSCP](https://github.com/0xsyr0/OSCP) — large community command reference

---

**Status:** Core OSCP cheat sheet chapters **00–09** are populated. Treat these as living lab notes: verify each command against your actual environment and the current OffSec rules. Start at the [Quick Reference](00-Quick-Reference/quick-reference.md), then follow the detailed chapter needed.
