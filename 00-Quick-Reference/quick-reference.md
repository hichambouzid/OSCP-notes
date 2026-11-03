# OSCP Quick Reference — Manual Decision Sheet

> Fast lookup for **authorized labs**. Read the full guides before using unfamiliar commands. Replace example addresses, domains, users and ports with the actual assigned target. This is a study aid, **not** a substitute for current OffSec rules.

## Start a target

~~~bash
export IP=192.168.56.101
mkdir -p scans evidence
ip route get "$IP"
sudo nmap -Pn -sS -p- -oA scans/tcp-all "$IP"
sudo nmap -Pn -sV -sC -p 22,80,445 -oA scans/tcp-services "$IP"
sudo nmap -Pn -sU --top-ports 100 -oA scans/udp-top100 "$IP"
~~~

The service-port list is a **placeholder**: use ports actually discovered in the full scan. Scan only in-scope systems.

## When a port is open

| Port / service | First manual checks | Full guide |
| --- | --- | --- |
| 21 FTP | Anonymous access if permitted, banners, directory list | [Services](../01-Enumeration/service-enumeration.md#3-ftp--file-transfer-protocol-21) |
| 22 SSH | Banner, authorized supplied account | [Services](../01-Enumeration/service-enumeration.md) |
| 53 DNS | A/NS/SRV records, domain naming | [Services](../01-Enumeration/service-enumeration.md) |
| 80/443/8080 Web | Headers, redirects, hosts, paths, params | [Web](../02-Web-Application/web-enumeration.md) |
| 88 Kerberos | DC, correct time, SPNs, assigned credentials | [AD](../05-Active-Directory/ad-enumeration.md) |
| 139/445 SMB | Shares, guest policy, assigned account access | [Services](../01-Enumeration/service-enumeration.md) |
| 389/636 LDAP | Bind policy, groups/computers with assigned creds | [AD](../05-Active-Directory/ad-enumeration.md) |
| 161 UDP SNMP | Authorized community and system metadata | [Services](../01-Enumeration/service-enumeration.md) |
| 2049 NFS | Exports and access rules | [Services](../01-Enumeration/service-enumeration.md) |
| 3389 RDP | Remote login only with assigned account | [Services](../01-Enumeration/service-enumeration.md) |
| 5985/5986 WinRM | Allowed account and reachability | [AD](../05-Active-Directory/ad-attack-paths.md) |

## Fast web triage

~~~bash
curl -i "http://$IP/"
whatweb "http://$IP/"
gobuster dir -u "http://$IP/" -w /usr/share/wordlists/dirb/common.txt -t 10
~~~

For DNS-resolvable subdomains of a domain **explicitly in scope**:

~~~bash
ffuf -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -u "https://FUZZ.example.lab/" -rate 20
~~~

The URL fuzzes **DNS-backed hostnames**. Header-based virtual host fuzzing against an IP is a **different** technique. Follow [Web Enumeration](../02-Web-Application/web-enumeration.md) for response filtering and troubleshooting.

## Web finding → next step

| Finding | Next check |
| --- | --- |
| Software/version | Vendor advisory and applicable CVE |
| Parameter + SQL errors or changed results | [Manual SQLi](../02-Web-Application/web-enumeration.md) |
| File path parameter | Traversal / PHP filter check |
| Upload form | Harmless upload, extension/MIME/storage behavior |
| Reflected HTML/JS | XSS context and browser execution |
| User-owned resource ID | Two-account IDOR authorization check |
| OS-command-like form | Benign output marker and timing |
| URL-fetching feature | Controlled SSRF callback |
| Template rendering field | Benign SSTI expression |

## Local privilege escalation — one glance

**Linux:**

~~~bash
id
sudo -l
find / -xdev -type f -perm -4000 2>/dev/null
getcap -r / 2>/dev/null
ss -lntup
ps auxww
~~~

**Windows:**

~~~cmd
whoami /all
systeminfo
sc query state= all
schtasks /query /fo LIST /v
netstat -ano
~~~

Use detailed [Linux](../04-Privilege-Escalation/linux-privesc.md) and [Windows](../04-Privilege-Escalation/windows-privesc.md) guides to validate actual vulnerabilities.

## AD, credentials and pivoting

- [AD Enumeration](../05-Active-Directory/ad-enumeration.md): DNS/clock, starting credentials, users, groups, SPNs, shares, relationships.
- [AD Attack Paths](../05-Active-Directory/ad-attack-paths.md): rights, account/host scope and one hypothesis at a time.
- [Password Auditing](../06-Passwords/password-auditing.md): offline datasets and hash identification; avoid broad login guessing.
- [Pivoting](../07-Pivoting/pivoting-tunneling.md): draw source → pivot → destination; use approved SSH forwards only where needed.

## Non-negotiable exam notes

- Latest [OffSec OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide) always overrides notes.
- No LLM/chatbot use during the exam. No SQLmap/SQLninja, automatic exploitation, mass vulnerability scanners, commercial Burp Pro or spoofing.
- Metasploit modules and Meterpreter: one selected target; published exceptions for msfvenom and multi/handler.
- Proof files: control panel before exam end **and** original-location cat/type in an interactive shell with target IP in screenshot.
- Report: professional reproducible PDF in an unencrypted 7z; confirm submission and checksum.

See [Exam Methodology](../08-Exam-Workflow/exam-methodology.md) and [Reporting](../08-Exam-Workflow/reporting.md).

## Last-minute checklist

- [ ] Target scope / route / starting identity noted.
- [ ] All TCP ports checked, UDP considered.
- [ ] Every discovered service has a next action or ruled-out reason.
- [ ] Candidate vulnerability manually validated.
- [ ] Foothold and effective privilege recorded.
- [ ] Evidence captured privately, without exposing secrets.
- [ ] Proof and report requirements checked against current exam guide.
