# OSCP Quick Reference — Manual Decision Sheet

> **Need a faster lookup or a rehearsal?** Open the [Fast Reference Index](reference-index.md), [Hands-on Terminal Drills](../09-Lab-Writeups/hands-on-terminal-drills.md), or [Troubleshooting Cards](../08-Exam-Workflow/troubleshooting-cards.md). Run the local self-test before the exam; use these static references independently during the exam subject to OffSec rules.


> Fast lookup for **authorized labs**. Read the full guides before using unfamiliar commands. Replace example addresses, domains, users and ports with the actual assigned target. This is a study aid, **not** a substitute for current OffSec rules.

## Start a target

~~~bash
export IP=192.168.56.101  # Replace with your assigned host
mkdir -p "$HOME/oscp-local/$IP"/{scans,evidence}
cd "$HOME/oscp-local/$IP"  # Private working directory outside the public Git repo
ip route get "$IP"

# Fast full-TCP discovery: all ports, but only one retry (may miss responses)
sudo nmap -Pn -n -sS -p- -T4 \
  --min-rate 300 \
  --max-retries 1 \
  --max-scan-delay 100ms \
  --open -v -oA scans/tcp-all "$IP"

# Extract ALL confirmed open TCP ports from this scan
PORTS=$(grep -oE '[0-9]+/open/tcp' scans/tcp-all.gnmap | cut -d/ -f1 | sort -nu | paste -sd, -)
if [ -n "$PORTS" ]; then
  sudo nmap -Pn -sC -sV -p "$PORTS" -oA scans/tcp-services "$IP"
else
  echo "No open TCP ports found: check VPN, IP, filtering and scan accuracy."
fi

# UDP FIRST PASS ONLY: not a complete UDP audit
sudo nmap -Pn -sU --top-ports 100 -oA scans/udp-top100 "$IP"
~~~

**Accuracy safeguard:** This is a **fast** full-range scan, not guaranteed complete detection. `--max-retries 1` and `--max-scan-delay 100ms` can miss rate-limited or lost replies. If few/no ports appear or a service is suspected, confirm with `sudo nmap -Pn -n -sS -p- --reason -oA scans/tcp-verify "$IP"`, compare both scans and enumerate all confirmed open ports. `-oA` is kept so the extraction command has a real `.gnmap` file.

**Do not skip discovered ports:** never copy a fixed port list such as `22,80,445` into service detection unless those are actually your only open TCP ports. The extraction above reads Nmap's real `.gnmap` output.

**UDP escalation decision:** top 100 is a quick starting point, **not enough to rule out other UDP services**. Examine UDP leads from TCP/AD discovery and, if needed, run:

~~~bash
sudo nmap -Pn -sU --top-ports 1000 -oA scans/udp-top1000 "$IP"
# Full UDP coverage, when time and scope justify it:
sudo nmap -Pn -sU -p- -oA scans/udp-all "$IP"
~~~

`open|filtered` does not confirm an open UDP port. Use `-sV` or a reviewed service-specific probe to validate. If TCP or UDP results are inconsistent, recheck routing and retry conservatively before moving on. **Only scan in-scope systems.**

## When a port is open

| Port / service | First manual checks | Full guide |
| --- | --- | --- |
| 21 FTP | Anonymous access if permitted, banners, directory list | [Services](../01-Enumeration/service-enumeration.md#3-ftp--file-transfer-protocol-21) |
| 22 SSH | Banner, authorized supplied account | [Services](../01-Enumeration/service-enumeration.md) |
| 53 DNS | A/NS/SRV records, domain naming | [Services](../01-Enumeration/service-enumeration.md) |
| 80/443/8080 Web | Headers, redirects, hosts, paths, params | [Web](../02-Web-Application/web-enumeration.md) |
| 88 Kerberos | DC, correct time, SPNs, assigned credentials | [AD](../05-Active-Directory/ad-enumeration.md) |
| 139/445 SMB | Shares, guest policy, assigned account access | [SMBClient](../01-Enumeration/smbclient.md) / [Services](../01-Enumeration/service-enumeration.md) |
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

## Initial access and file transfer

Use [Initial Access](../03-Initial-Access/initial-access.md) for the verified vulnerability or assigned credential workflow. SSH, RDP, WinRM and web/SMB access have different rights; verify the resulting shell identity.

**Kali — serve an authorized test file:**

~~~bash
export LHOST=192.168.45.219  # Your actual reachable VPN address
mkdir -p "$HOME/oscp-local/transfer"
printf 'transfer test\n' > "$HOME/oscp-local/transfer/test.txt"
python3 -m http.server 8000 --bind "$LHOST" --directory "$HOME/oscp-local/transfer"
~~~

**Target — Linux:**

~~~bash
curl -f -o /tmp/oscp-test.txt http://192.168.45.219:8000/test.txt
~~~

**Target — Windows PowerShell:**

~~~powershell
Invoke-WebRequest -Uri 'http://192.168.45.219:8000/test.txt' -OutFile "$env:TEMP\oscp-test.txt"
~~~

Keep the Kali server running in its own terminal, serve no secrets, and stop it after use. For checksums, wget, curl.exe, SCP and connection errors see [HTTP and File Transfer](../03-Initial-Access/file-transfer.md). Target-to-Kali downloads must meet the official exam exception.

## AD, credentials and pivoting

- [AD Enumeration](../05-Active-Directory/ad-enumeration.md): DNS/clock, starting credentials, users, groups, SPNs, shares, relationships.
- [AD Attack Paths](../05-Active-Directory/ad-attack-paths.md): rights, account/host scope and one hypothesis at a time.
- [Password Auditing](../06-Passwords/password-auditing.md): offline datasets, mode table, wordlists, synthetic test and troubleshooting; avoid broad login guessing.
- [Kerberos hash-mode reference](../05-Active-Directory/ad-attack-paths.md#3b-offline-password-auditing--as-rep-and-tgs-hashes): RC4 and AES AS-REP/TGS formats, offline Hashcat and John workflows. A ticket is not automatically a password hash.
- [Pivoting](../07-Pivoting/pivoting-tunneling.md): SSH -L/-D/-R/-J, SOCKS, ProxyChains, Chisel, Ligolo-ng and cleanup; draw source → pivot → assigned destination.

### Pivoting: select a method

| Need | Method |
| --- | --- |
| One internal TCP service | SSH -L |
| Multiple TCP services | SSH -D with SOCKS5 |
| Pivot needs local Kali HTTP | SSH -R |
| SSH through a jump host | SSH -J |
| Authorized pivot can connect outbound | Chisel reverse SOCKS / Ligolo-ng |
| Specific internal IP route | Ligolo-ng TUN |

Full examples: [Pivoting decision sheet](../07-Pivoting/pivoting-tunneling.md#4a-pivoting-decision-sheet--choose-the-simplest-working-route). Raw SYN, ICMP and standard UDP scans do not traverse ordinary SSH SOCKS. Metasploit cannot be used to pivot in the exam.

## Non-negotiable exam notes

- Latest [OffSec OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide) always overrides notes.
- No LLM/chatbot use during the exam. No SQLmap/SQLninja, automatic exploitation, mass vulnerability scanners, commercial Burp Pro or spoofing.
- Metasploit modules and Meterpreter: one selected target; published exceptions for msfvenom and multi/handler.
- File transfers: do not download target files/apps/source to Kali unless needed to compromise the exam host; delete permitted downloads after objectives.
- Proof files: control panel before exam end **and** original-location cat/type in an interactive shell with target IP in screenshot.
- Report: professional reproducible PDF in an unencrypted 7z; confirm submission and checksum.

See [Exam Methodology](../08-Exam-Workflow/exam-methodology.md) and [Reporting](../08-Exam-Workflow/reporting.md).

## Last-minute checklist

- [ ] Target scope / route / starting identity noted.
- [ ] All 65,535 TCP ports scanned; service detection on **all discovered** TCP ports.
- [ ] UDP top-100 initial pass completed and expansion decision explicitly recorded.
- [ ] Empty or suspicious scan results checked for filtering, routing and packet-loss issues.
- [ ] Every discovered service has a next action or ruled-out reason.
- [ ] Candidate vulnerability manually validated.
- [ ] Foothold and effective privilege recorded.
- [ ] Evidence captured privately, without exposing secrets.
- [ ] Proof and report requirements checked against current exam guide.
