# Service-Specific Enumeration — OSCP Field Guide

> **Purpose:** Turn Nmap results into a structured enumeration plan for each discovered service.
>
> **Scope:** Assigned OSCP targets and authorized labs only. Use discovered ports, not assumptions about default ports.

**Previous:** [Nmap Enumeration](./nmap.md)

## Workflow

1. Review `scans/tcp-services.nmap` and UDP results.
2. Make a list of each open port and identified service.
3. Follow the relevant service section below.
4. Save outputs, URLs, shares, usernames, versions and evidence.
5. Research possible weaknesses and verify them manually.
6. Return to remaining services before concluding enumeration.

### Prepare

```bash
export IP=192.168.56.101   # Replace with your assigned target
mkdir -p scans evidence
```

**Note:** `-Pn` is appropriate for a known assigned target that may ignore discovery probes. It does not prove the host is online.

## 1. HTTP / HTTPS — Web applications (80, 443, 8080, 8443, etc.)

### Identify the application

```bash
curl -i "http://$IP/"
curl -k -i "https://$IP/"
whatweb "http://$IP/"
sudo nmap -Pn -sV -p 80,443 --script http-title,http-headers -oA scans/http-info "$IP"
```

Only include ports you actually found. `-k` skips TLS certificate validation for lab inspection; do not treat it as evidence that the certificate is trustworthy.

Look for:
- Server, framework, CMS and application version clues
- Redirects, login forms, cookies, authentication and session handling
- `robots.txt`, `sitemap.xml`, linked JavaScript and exposed documentation
- Virtual hosts and alternate applications
- File uploads, APIs, administrative paths and unusual HTTP methods

### Discover content (authorized targets only)

```bash
gobuster dir -u "http://$IP/" -w /usr/share/wordlists/dirb/common.txt -o scans/web-dirs.txt
```

Use a modest request rate and the correct scheme, host and port. Check `/etc/hosts` or use the supplied hostname when the application requires a virtual host.

### TLS checks

```bash
sudo nmap -Pn -p 443 --script ssl-cert,ssl-enum-ciphers "$IP"
```

The cipher enumeration script makes multiple handshakes; run only when permitted.

**Potential findings:** exposed sensitive files, outdated components, missing access controls, insecure configuration. Confirm with actual evidence; banners alone are insufficient.

**Next:** [Web Application notes](../02-Web-Application/) when that section is available.

## 2. SMB — Windows file sharing (139/445)

### Identify configuration and shares

```bash
sudo nmap -Pn -p 139,445 --script smb-os-discovery,smb2-security-mode -oA scans/smb-info "$IP"
smbclient -L "//$IP/" -N
```

`-N` attempts an unauthenticated connection; it may fail when guest access is disabled.

If a share is visible and guest access is allowed:

```bash
smbclient "//$IP/SHARE" -N
```

Replace `SHARE` with a share actually returned by enumeration.

Look for:
- Accessible shares and read/write permissions
- Files containing credentials or environment details
- SMB signing configuration
- Hostname, domain and workgroup
- Usernames or group names revealed through authorized access

**Interpretation:** A listed share does not automatically mean its contents are readable. Test permissions explicitly and record what succeeded.

## 3. FTP — File Transfer Protocol (21)

```bash
sudo nmap -Pn -sV -p 21 --script ftp-anon,ftp-syst -oA scans/ftp-info "$IP"
ftp "$IP"
```

Check whether anonymous login is enabled and, if authorized, what files are readable. Do not modify or upload files without a specific reason and permission.

### FTP anonymous login — step by step

If Nmap reports `Anonymous FTP login allowed`, try connecting manually:

```bash
ftp "$IP"
```

At the prompts, enter:

```text
Name: anonymous
Password: anonymous@
```

Many anonymous FTP servers accept any email-style password or an empty password; the server may also reject anonymous access despite a scan result.

**Example session:**

```text
ftp> pwd
ftp> ls
ftp> dir
ftp> cd pub
ftp> ls -la
ftp> binary
ftp> get readme.txt
ftp> bye
```

| FTP command | Purpose |
| --- | --- |
| `pwd` | Show the current remote FTP directory |
| `ls` or `dir` | List remote files and directories |
| `ls -la` | Request a detailed listing (server-dependent) |
| `cd pub` | Enter the remote `pub` directory if it exists |
| `cd ..` | Move to the parent remote directory |
| `lcd evidence` | Change the **local** download destination (directory must exist) |
| `binary` | Transfer files without text conversion |
| `get filename` | Download one readable remote file |
| `mget *.txt` | Download matching files (may prompt for each) |
| `bye` | Disconnect |

### Inspect remote files and download evidence

FTP is a file-transfer protocol: the usual way to **read file contents** is to download the file to Kali and inspect it locally. Directory listings show filenames and metadata, not the full contents of a file.

On Kali, before opening the FTP client:

```bash
mkdir -p evidence/ftp
ftp "$IP"
```

Then in the FTP prompt:

```text
ftp> pwd
ftp> ls
ftp> lcd evidence/ftp
ftp> binary
ftp> get notes.txt
ftp> bye
```

Back in the Kali terminal, inspect the downloaded file:

```bash
file evidence/ftp/notes.txt
ls -lah evidence/ftp/
cat evidence/ftp/notes.txt
less evidence/ftp/notes.txt
```

For a file that may contain non-text data, start with `file` rather than `cat`.

If the FTP server is on a **nonstandard port**, use `ftp` with that port, for example:

```bash
ftp "$IP" 2121
```

### Download multiple files

Inside the FTP prompt, after entering the correct remote directory:

```text
ftp> lcd evidence/ftp
ftp> binary
ftp> prompt
ftp> mget *.txt
ftp> bye
```

`prompt` toggles interactive confirmation for multi-file transfers. Use `mget` only for files in scope; it does not recursively download entire directory trees.

### Troubleshooting FTP access

- **530 Login incorrect:** Anonymous access may be disabled, restricted, or require a different password format.
- **550 Permission denied / File unavailable:** The file may not exist or your FTP account may lack permission.
- **Directory listing hangs:** Check passive mode and VPN/firewall behavior; in the interactive client, `passive` toggles passive mode on implementations that support it.
- **Downloaded file looks corrupted:** Use `binary` before transferring it.
- **Cannot locate the downloaded file:** Run `lpwd` if supported, or set the destination with `lcd` before `get`.

**Security note:** FTP transmits credentials and data without encryption. Anonymous FTP is common in labs but should not be used for sensitive production transfers. Do not publish downloaded credentials or private files in this public repository.

Look for backups, configuration files, web-root content and version clues. A banner version is a lead for research, not proof of a CVE.

## 4. SSH — Secure Shell (22)

```bash
sudo nmap -Pn -sV -p 22 --script ssh-hostkey,ssh2-enum-algos -oA scans/ssh-info "$IP"
nc -nv "$IP" 22
```

Look for the SSH product/version, host keys, supported algorithms and authentication methods. A version may be patched through distribution backports.

**Next:** Use legitimate credentials discovered during authorized lab work; do not assume SSH is exploitable because it is exposed.

## 5. DNS — Domain Name System (53 TCP/UDP)

```bash
sudo nmap -Pn -sU -sV -p 53 "$IP"
dig @"$IP" example.lab A
dig @"$IP" example.lab NS
dig @"$IP" example.lab MX
```

Replace `example.lab` with the actual assigned domain. Check whether the server is authoritative and what names or records it reveals.

Where the domain and scope permit an authorized zone-transfer check:

```bash
dig @"$IP" example.lab AXFR
```

A refused zone transfer is normal and does not mean DNS is misconfigured.

## 6. SNMP — Network management (161/UDP)

```bash
sudo nmap -Pn -sU -sV -p 161 "$IP"
nmap --script-help snmp-info
sudo nmap -Pn -sU -p 161 --script snmp-info -oA scans/snmp-info "$IP"
```

If the lab explicitly supplies an SNMPv2c community string, inspect allowed information:

```bash
snmpwalk -v2c -c COMMUNITY "$IP" 1.3.6.1.2.1.1
```

Replace `COMMUNITY` with the authorized value. Look for system descriptions, hostnames, interface details and network configuration. SNMPv3 requires different authentication options.

**UDP reminder:** `open|filtered` is inconclusive, not proof of an open service.

## 7. SMTP — Mail service (25/465/587)

```bash
sudo nmap -Pn -sV -p 25,465,587 --script smtp-commands -oA scans/smtp-info "$IP"
```

Review supported SMTP commands, TLS options, banner information and mail domain configuration. Do not send unsolicited mail or perform large-scale address guessing.

## 8. NFS — Network File System (111/2049)

```bash
sudo nmap -Pn -sV -p 111,2049 --script nfs-showmount,nfs-ls -oA scans/nfs-info "$IP"
showmount -e "$IP"
```

Check exports and client restrictions. Do not assume that an exported path is accessible or writable; verify with authorized, non-destructive checks.

## 9. RDP — Remote Desktop (3389)

```bash
sudo nmap -Pn -sV -p 3389 --script rdp-ntlm-info,rdp-enum-encryption -oA scans/rdp-info "$IP"
```

Review hostname/domain clues, supported security layers and certificate details. Do not attempt authentication without approved credentials or scope.

## 10. Databases — MySQL, PostgreSQL, MSSQL

```bash
sudo nmap -Pn -sV -p 1433,3306,5432 "$IP"
```

Use only ports that are actually open. Note product, version, whether remote access is exposed, and any authentication requirements. Avoid destructive queries; do not assume default credentials.

## 11. Investigate potential vulnerabilities

For every service:

1. Confirm the product and version from more than one clue when possible.
2. Identify relevant security advisories or CVEs.
3. Check prerequisites (configuration, module, authentication, platform and patch status).
4. Select only **reviewed, appropriate** NSE scripts or non-destructive checks.
5. Classify the result as **unverified**, **ruled out**, or **verified**, with evidence.

Example research:

```bash
searchsploit "Apache httpd"
searchsploit "Samba"
```

Replace examples with actual product/version findings. SearchSploit matches and Nmap vulnerability alerts are not confirmation. Avoid running broad `--script vuln` categories blindly; some scripts can be intrusive.

## Decision table

| Observation | Next step |
| --- | --- |
| Web login page | Identify framework, routes, roles and auth behavior |
| SMB shares visible | Check actual access permissions and contents |
| FTP anonymous login | List accessible files and note sensitive exposures |
| SSH only | Record version/algorithms; inspect other services for legitimate credentials |
| DNS answers | Enumerate assigned domain records and permitted subdomains |
| SNMP information | Map host and network details for further enumeration |
| Version appears outdated | Cross-check advisories, patches and exploit prerequisites |
| No obvious weakness | Revisit less common ports, virtual hosts, UDP and service configuration |

## Findings template

```text
Target:
Port / protocol:
Service:
Version / evidence:
Authentication required:
Accessible resources:
Potential issue:
CVE / advisory:
Validation status: unverified | ruled out | verified
Saved output:
Next action:
```

## OSCP checklist

- [ ] Review every open TCP port and interesting UDP result.
- [ ] Confirm the real service, even on nonstandard ports.
- [ ] Enumerate web applications, including hostnames and virtual hosts.
- [ ] Inspect accessible SMB shares and permissions.
- [ ] Check FTP, SSH, DNS and SNMP as applicable.
- [ ] Investigate mail, NFS, RDP and database services when present.
- [ ] Save all commands and outputs.
- [ ] Research versions and validate potential weaknesses.
- [ ] Record credentials and sensitive findings securely in your local lab notes, **not in a public GitHub repository**.
- [ ] Document next steps and revisit overlooked services.

## References

- [Nmap NSE documentation](https://nmap.org/book/man-nse.html)
- [Nmap script documentation](https://nmap.org/nsedoc/)
- [SearchSploit](https://www.exploit-db.com/searchsploit)
- [Nmap version detection](https://nmap.org/book/man-version-detection.html)

---

**Previous:** [Nmap Enumeration](./nmap.md)
