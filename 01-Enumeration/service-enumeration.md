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

### Practical web access, browsing and downloads

If Nmap reports HTTP or HTTPS, visit the actual open port:

```bash
curl -i "http://$IP:80/"
curl -k -i "https://$IP:443/"
```

In a browser, open `http://TARGET_IP:PORT/` and follow visible links. For a named virtual host provided by the lab, add the assigned hostname to `/etc/hosts` and browse by name rather than IP.

To inspect an HTTP response and download a publicly accessible file:

```bash
curl -I "http://$IP:80/"
curl -o evidence/web-page.html "http://$IP:80/"
curl -O "http://$IP:80/readme.txt"
file evidence/web-page.html
less evidence/web-page.html
```

`curl -O` saves using the remote basename in the current directory. Replace `readme.txt` with a file actually discovered; do not assume it exists. `-I` requests headers and may be unsupported by some servers.

For paths discovered with Gobuster, request them individually and distinguish `200` (response), `301/302` (redirect), `401` (authentication required), `403` (forbidden), and `404` (not found). A `200` alone does not prove sensitive data exposure.


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

### Practical SMB share access and downloads

List shares without supplying a password (only works if anonymous/guest access is allowed):

```bash
smbclient -L "//$IP/" -N
```

Connect to a share returned by the listing:

```bash
mkdir -p evidence/smb
smbclient "//$IP/SHARE" -N
```

Inside the `smbclient` prompt:

```text
smb: \\> pwd
smb: \\> ls
smb: \\> cd documents
smb: \\> ls
smb: \\> lcd evidence/smb
smb: \\> get readme.txt
smb: \\> exit
```

Replace `SHARE`, `documents`, and `readme.txt` with names actually returned. `lcd` changes the local download directory. The `get` command downloads a readable file; listing a share does not prove file access.

Inspect locally:

```bash
file evidence/smb/readme.txt
less evidence/smb/readme.txt
```

For a lab-provided account, use `smbclient "//$IP/SHARE" -U USERNAME` and enter the password interactively rather than exposing it on the command line.

**If access fails:** `NT_STATUS_ACCESS_DENIED` indicates insufficient permission; `NT_STATUS_BAD_NETWORK_NAME` often means an incorrect share name. Record the outcome instead of assuming anonymous access works.


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

### Practical SSH login and remote file inspection

SSH normally requires **authorized credentials or a valid key**; it does not provide anonymous file browsing.

```bash
ssh -p 22 USERNAME@"$IP"
```

Once logged in with approved credentials:

```bash
pwd
whoami
ls -lah
find . -maxdepth 2 -type f -readable 2>/dev/null
file ./notes.txt
less ./notes.txt
exit
```

To copy a file that the account is allowed to read, from **your Kali terminal**:

```bash
mkdir -p evidence/ssh
scp -P 22 USERNAME@"$IP":/home/USERNAME/notes.txt evidence/ssh/
```

Replace usernames, paths and ports with actual values. `scp -P` uses an uppercase P for port. If the host only supports SFTP:

```bash
sftp -P 22 USERNAME@"$IP"
```

Then use `pwd`, `ls`, `cd`, `lcd evidence/ssh`, `get notes.txt`, and `bye`. Do not download private material outside the lab scope.


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

### Practical DNS enumeration and output collection

DNS does **not** offer general filesystem access. It exposes records, not remote files.

```bash
export DOMAIN=example.lab  # Replace with the assigned domain
dig @"$IP" "$DOMAIN" A +noall +answer
dig @"$IP" "$DOMAIN" NS +noall +answer
dig @"$IP" "$DOMAIN" MX +noall +answer
dig @"$IP" "$DOMAIN" TXT +noall +answer
dig @"$IP" "$DOMAIN" AXFR > scans/dns-axfr.txt
```

A zone transfer only succeeds if the server allows it for your client; a failure is normal. If permitted and successful, review `scans/dns-axfr.txt` for in-scope hostnames and resolve them individually. You are saving DNS responses locally, **not downloading files from the DNS server**.

```bash
cat scans/dns-axfr.txt
dig @"$IP" www."$DOMAIN" A +short
```


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

### Practical SNMP access and evidence collection

SNMP exposes management objects rather than remote files. For SNMPv2c, use a community string **supplied or explicitly permitted by the lab**:

```bash
snmpget -v2c -c COMMUNITY "$IP" 1.3.6.1.2.1.1.1.0
snmpwalk -v2c -c COMMUNITY "$IP" 1.3.6.1.2.1.1 > scans/snmp-system.txt
cat scans/snmp-system.txt
```

The first OID requests the system description; the second walks the system information subtree. Replace `COMMUNITY` with the authorized value. A timeout can indicate a wrong community, filtering, version mismatch or no response; it is not proof the port is closed.

Record hostnames, system details and interface clues. Avoid write operations (`snmpset`) during enumeration.


## 7. SMTP — Mail service (25/465/587)

```bash
sudo nmap -Pn -sV -p 25,465,587 --script smtp-commands -oA scans/smtp-info "$IP"
```

Review supported SMTP commands, TLS options, banner information and mail domain configuration. Do not send unsolicited mail or perform large-scale address guessing.

### Practical SMTP enumeration — commands and interpretation

SMTP is a **mail transport protocol**, not a remote file browser. You can inspect the server's greeting and supported commands without sending a message.

First identify which SMTP ports are actually open:

```bash
sudo nmap -Pn -sV -p 25,465,587 --script smtp-commands -oA scans/smtp-info "$IP"
```

**Plain SMTP on port 25** (when permitted):

```bash
nc -nv "$IP" 25
```

At the SMTP prompt, enter:

```text
EHLO kali.lab
QUIT
```

Typical responses include `220` (service greeting), `250` (command accepted / advertised capabilities), `500/502` (unknown or unsupported command), and `530` (authentication required).

**STARTTLS on port 587**, if advertised:

```bash
openssl s_client -starttls smtp -connect "$IP:587" -crlf
```

After the TLS handshake, type `EHLO kali.lab` and then `QUIT`. For implicit TLS on port 465:

```bash
openssl s_client -connect "$IP:465" -crlf
```

Inspect the certificate, hostname, server greeting, `EHLO` extensions, and whether STARTTLS and AUTH are advertised. `AUTH` being advertised does not mean anonymous login is possible.

To save a non-authenticating SMTP capability check:

```bash
printf 'EHLO kali.lab\r\nQUIT\r\n' | nc -w 5 "$IP" 25 | tee scans/smtp-ehlo.txt
```

**Do not** attempt open-relay testing by delivering mail to third parties, bulk recipient guessing, or unsolicited messages. SMTP generally does not let you list mailboxes or download emails. Mailbox access uses separate protocols such as POP3 or IMAP with authorized credentials.


## 8. NFS — Network File System (111/2049)

```bash
sudo nmap -Pn -sV -p 111,2049 --script nfs-showmount,nfs-ls -oA scans/nfs-info "$IP"
showmount -e "$IP"
```

Check exports and client restrictions. Do not assume that an exported path is accessible or writable; verify with authorized, non-destructive checks.

### Practical NFS access and read-only file inspection

Enumerate exported paths:

```bash
showmount -e "$IP"
```

If the server exports an authorized path and your client is permitted, mount it **read-only** to avoid modifying remote files:

```bash
sudo mkdir -p /mnt/oscp-nfs
sudo mount -t nfs -o ro "$IP:/export/share" /mnt/oscp-nfs
ls -lah /mnt/oscp-nfs
find /mnt/oscp-nfs -maxdepth 2 -type f 2>/dev/null
```

Replace `/export/share` with a real exported path. Copy an authorized readable file locally and unmount afterward:

```bash
mkdir -p evidence/nfs
cp /mnt/oscp-nfs/readme.txt evidence/nfs/
file evidence/nfs/readme.txt
sudo umount /mnt/oscp-nfs
```

Export listing does not guarantee access: server restrictions, protocol versions and filesystem permissions still apply.


## 9. RDP — Remote Desktop (3389)

```bash
sudo nmap -Pn -sV -p 3389 --script rdp-ntlm-info,rdp-enum-encryption -oA scans/rdp-info "$IP"
```

Review hostname/domain clues, supported security layers and certificate details. Do not attempt authentication without approved credentials or scope.

### Practical RDP connection

RDP is a graphical remote-desktop protocol, not an anonymous file-listing interface. With credentials explicitly supplied or authorized for the lab, connect using a client installed on Kali:

```bash
xfreerdp /v:"$IP" /u:USERNAME
```

Enter the password securely when prompted; client syntax varies by installed FreeRDP version. Inspect only resources your account is authorized to access. If FreeRDP is unavailable, check `xfreerdp /help` or your installed RDP client's documentation.

Do not assume an open RDP port grants access or that file transfer is enabled.


## 10. Databases — MySQL, PostgreSQL, MSSQL

```bash
sudo nmap -Pn -sV -p 1433,3306,5432 "$IP"
```

Use only ports that are actually open. Note product, version, whether remote access is exposed, and any authentication requirements. Avoid destructive queries; do not assume default credentials.

### Practical database connection and safe read-only checks

A database port does not grant anonymous access. Use credentials explicitly supplied for the authorized lab and **avoid modifying data**.

**MySQL/MariaDB (usually 3306):**

```bash
mysql -h "$IP" -P 3306 -u USERNAME -p
```

After authentication:

```sql
SHOW DATABASES;
SELECT VERSION();
```

**PostgreSQL (usually 5432):**

```bash
psql -h "$IP" -p 5432 -U USERNAME -d postgres
```

In `psql`:

```text
\l
\dt
\q
```

**Microsoft SQL Server (usually 1433):** use an approved SQL client and credentials; first identify the server/version with Nmap. Client availability and authentication options vary by Kali installation.

Database results can be exported locally using approved client features, but avoid dumping entire databases or extracting personal data. Record only the minimum evidence required for the lab finding.


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
