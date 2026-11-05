# Service-Specific Enumeration — OSCP Field Guide

> **Purpose:** Turn Nmap results into a structured enumeration plan for each discovered service.
>
> **Scope:** Assigned OSCP targets and authorized labs only. Use discovered ports, not assumptions about default ports.

**Exam-day accuracy rule:** Complete the [full TCP scan and discovered-port service detection](./nmap.md) **before** relying on any section below. All fixed port numbers in this guide illustrate common services; a service can run on **any discovered port**. UDP top 100 is only a first pass: expand to relevant specific ports, top 1,000 or a full UDP scan when warranted.

**OffSec exam file-transfer restriction:** [The official exam guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide) forbids downloading applications, files or source code from exam targets to Kali **unless necessary to compromise the exam machine**; in that case delete those local downloads after completing the exam objectives. Commands containing `get`, `mget`, `scp`, `sftp get`, `curl -o`, or copying from mounted shares are **practice-lab examples, not routine exam-day instructions**. Prefer listing and in-place inspection on the target when appropriate; keep any permitted evidence private.

**Previous:** [Nmap Enumeration](./nmap.md)

## Service-by-service testing rule

For **every discovered port**, record: protocol, actual service/version, anonymous or authenticated access, configuration/security controls, in-scope resources, likely weakness, and **what evidence would prove it**. Port numbers in headings are examples, **never scan boundaries**. Work from a **full TCP 1–65535 scan** and a separately documented UDP decision; identify **all** discovered open TCP services first. If you have no path, revisit obscure ports, alternative HTTP ports, DNS/vhosts and inconclusive UDP results.

**Potential checks are hypotheses, not vulnerabilities.** Use only manual, authorized, non-destructive tests. Do not default to guessed credentials, bulk user enumeration, spraying, brute forcing, relay/spoofing, mass vuln scanning, arbitrary file transfers, or broad NSE exploit categories. Before a targeted NSE check, run `nmap --script-help SCRIPT_NAME` and confirm what it does. See the [official OffSec OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide) for exam restrictions.

**Service tracking matrix (copy privately per target):**

```text
PORT/PROTO | DETECTED SERVICE | ACCESS (anon/assigned/denied) | MANUAL CHECK | RESULT | NEXT STEP
```

## Workflow

1. Review `scans/tcp-services.nmap` and UDP results.
2. Make a list of **every** open TCP port and each promising UDP result; do not silently discard nonstandard ports.
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

The `-p 80,443` list above is an **illustrative targeted check**, not a replacement for full-TCP discovery or scanning all discovered web ports (including 8080, 8443 and nonstandard ports). Replace it with ports where you actually identified HTTP/HTTPS. `-k` skips TLS certificate validation for lab inspection; do not treat it as evidence that the certificate is trustworthy.

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

**Next:** Record each web service's URL (including port and hostname), then follow [Web Enumeration](../02-Web-Application/web-enumeration.md).

### Practical web access, browsing and downloads

If Nmap reports HTTP or HTTPS, visit the actual open port:

```bash
curl -i "http://$IP:80/"
curl -k -i "https://$IP:443/"
```

In a browser, open `http://TARGET_IP:PORT/` and follow visible links. For a named virtual host provided by the lab, add the assigned hostname to `/etc/hosts` and browse by name rather than IP.

**Lab practice / permitted-compromise exception only:** Inspect a response and, only when allowed under OffSec's file-transfer rule above, save a discovered file locally:

```bash
curl -I "http://$IP:80/"
curl -o evidence/web-page.html "http://$IP:80/"
curl -f -o evidence/readme.txt "http://$IP:80/readme.txt"
file evidence/web-page.html
less evidence/web-page.html
```

`curl -f -o` saves to an explicit local path and fails on HTTP 4xx/5xx responses. Replace `readme.txt` with a file actually discovered; do not assume it exists. `-I` requests headers and may be unsupported by some servers.

For paths discovered with Gobuster, request them individually and distinguish `200` (response), `301/302` (redirect), `401` (authentication required), `403` (forbidden), and `404` (not found). A `200` alone does not prove sensitive data exposure.


### HTTP/HTTPS — potential checks to test

- **Hostname/virtual host mismatch:** follow `Location` redirects, certificates and app links; test discovered DNS-backed names and HTTP Host headers separately. HTTPS may also depend on TLS SNI.
- **Unexpected surfaces:** manually inspect `robots.txt`, `sitemap.xml`, linked JavaScript, API docs, login/admin forms and upload functions. Use small wordlists/rates with wildcard-response validation; see [Web Enumeration](../02-Web-Application/web-enumeration.md).
- **Security boundaries:** compare a baseline with a changed parameter, logged-in versus anonymous access, and resource ownership using only approved lab accounts. Investigate SQLi, LFI, command injection, XSS, SSTI, SSRF and upload execution **only if the feature exists**.
- **Config/version:** verify server/framework/CMS versions against advisories; check allowed HTTP methods, authentication, TLS certificates and cookie flags. A banner, response status, or missing security header is not an exploit by itself.

**Decision:** enumerate **every discovered web port** and hostname as its own application. Do not assume `80` and `443` are the only web listeners.
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

Use the share list above; anonymous/guest access is not guaranteed. Connect to a share returned by the listing:

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
smb: \\> lcd /absolute/path/to/your/repository/evidence/smb
smb: \\> get readme.txt
smb: \\> exit
```

Replace `SHARE`, `documents`, `readme.txt`, and the example absolute path with real values. `lcd` changes the local download directory; use an absolute path to avoid ambiguity. The `get` command downloads a readable file; listing a share does not prove file access.

Inspect locally:

```bash
file evidence/smb/readme.txt
less evidence/smb/readme.txt
```

For a lab-provided account, use `smbclient "//$IP/SHARE" -U USERNAME` and enter the password interactively rather than exposing it on the command line.

**If access fails:** `NT_STATUS_ACCESS_DENIED` indicates insufficient permission; `NT_STATUS_BAD_NETWORK_NAME` often means an incorrect share name. Record the outcome instead of assuming anonymous access works.


### SMB — potential checks to test

**Read-only baseline:**

```bash
# Run against an SMB service actually found, often 445/tcp
nmap --script-help smb-protocols
sudo nmap -Pn -p 445 --script smb-protocols,smb2-security-mode,smb2-capabilities "$IP"
smbclient -L "//$IP/" -N                       # One anonymous/guest attempt
smbclient -L "//$IP/" -U 'DOMAIN/USERNAME'      # Lab-supplied account; prompt for password
```

**What to investigate:**

- **Guest/null access:** do anonymous share listing and actual share access succeed? A visible share name is **not** permission to read its contents.
- **Share permissions:** compare read/list/write access with the assigned identity. For write access, do a harmless test marker and clean it up **only with explicit lab permission**; do not write to SYSVOL, production paths or unknown files.
- **SMB dialects/signing:** note whether SMBv1 is offered, and whether signing is required. Signing not required is a **relay-risk condition**, not proof that a relay attack will work; **do not attempt spoofing/relay during the exam**.
- **Identity and policy:** domain, hostname, OS/version, SYSVOL/NETLOGON listing, exposed configuration/scripts, and differences between anonymous and authorized users. Inspect allowed files **in place** where possible; exam file-download restrictions apply.
- **Domain RPC:** if the host and scope permit it, a single guest query can reveal whether a null session is accessible:

```bash
rpcclient -U "" -N "$IP" -c 'srvinfo'
```

If denied, record the restriction; do not brute credentials. For Windows patch/CVE leads, confirm exact OS/build and whether the vulnerable SMB protocol or configuration is actually enabled.

**Record:** actual access level per share, signing, dialects, host/domain, and sanitized evidence. See [AD Enumeration](../05-Active-Directory/ad-enumeration.md) for credentialed domain relationships.
## 3. FTP — File Transfer Protocol (21)

```bash
sudo nmap -Pn -sV -p 21 --script ftp-anon,ftp-syst -oA scans/ftp-info "$IP"
ftp "$IP"
```

Check whether anonymous login is enabled and, if authorized, what files are readable. Do not modify or upload files without a specific reason and permission.

### FTP anonymous login — step by step

If Nmap reports `Anonymous FTP login allowed`, use the `ftp "$IP"` connection shown above and try anonymous authentication.
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
ftp> cd pub
ftp> dir
ftp> binary
ftp> get readme.txt
ftp> bye
```

| FTP command | Purpose |
| --- | --- |
| `pwd` | Show the current remote FTP directory |
| `ls` or `dir` | List remote files and directories |
| `dir` | Request a detailed listing (server-dependent) |
| `cd pub` | Enter the remote `pub` directory if it exists |
| `cd ..` | Move to the parent remote directory |
| `lcd /absolute/path/to/evidence` | Change the **local** download destination (directory must exist) |
| `binary` | Transfer files without text conversion |
| `get filename` | Download one readable remote file |
| `mget *.txt` | Download matching files (may prompt for each) |
| `bye` | Disconnect |

### Inspect remote FTP files — practice downloads only

**Exam warning:** FTP `get` and `mget` transfer files from the exam host to Kali, so do **not** use them merely for general inspection. Only download a specific file if necessary to compromise the machine, and delete the local copy after the objectives. FTP `ls` and `dir` are useful non-download first steps. In ordinary authorized labs, downloading specifically permitted files may be appropriate.

On Kali, before opening the FTP client:

```bash
mkdir -p evidence/ftp
ftp "$IP"
```

Then in the FTP prompt:

```text
ftp> pwd
ftp> ls
ftp> lcd /absolute/path/to/your/repository/evidence/ftp
ftp> binary
ftp> get notes.txt
ftp> bye
```

Replace the sample `lcd` path with the absolute path to the directory created on Kali. Back in the Kali terminal, inspect the downloaded file:

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
ftp> lcd /absolute/path/to/your/repository/evidence/ftp
ftp> binary
ftp> prompt
ftp> mget *.txt
ftp> bye
```

`prompt` toggles interactive confirmation for multi-file transfers; check its current state before using it. Use `mget` only for files in scope; it does not recursively download entire directory trees.

### Troubleshooting FTP access

- **530 Login incorrect:** Anonymous access may be disabled, restricted, or require a different password format.
- **550 Permission denied / File unavailable:** The file may not exist or your FTP account may lack permission.
- **Directory listing hangs:** Check passive mode and VPN/firewall behavior; in the interactive client, `passive` toggles passive mode on implementations that support it.
- **Downloaded file looks corrupted:** Use `binary` before transferring it.
- **Cannot locate the downloaded file:** Run `lpwd` if supported, or set the destination with `lcd` before `get`.

**Security note:** FTP transmits credentials and data without encryption. Anonymous FTP is common in labs but should not be used for sensitive production transfers. Do not publish downloaded credentials or private files in this public repository.

Look for backups, configuration files, web-root content and version clues. A banner version is a lead for research, not proof of a CVE.

### FTP — potential checks to test

- **Anonymous login:** check once, then list the assigned directory with `pwd`, `ls`, `dir` (no download required). Record whether guest access is readable or restricted.
- **Permissions:** can your supplied test account list the directory? Is a sensitive backup/configuration **name** exposed? Test write privileges only if the lab explicitly authorizes a harmless upload and cleanup.
- **Web-root relationship:** if an exposed FTP share appears linked to an actual web root, document that hypothesis and test using a harmless marker only when authorized. An upload does not prove server-side code execution.
- **Protocol security:** check FTP banner/version, plaintext authentication, FTPS support and whether `AUTH TLS` is offered; server TLS certificate and version must be confirmed.
- **Exploit leads:** match an exact FTP server version to vendor advisories; do **not** run backdoor, denial-of-service or brute-force NSE scripts during routine enumeration.

```bash
# Read-only fingerprint; replace 21 with the actual discovered FTP port
sudo nmap -Pn -sV -p 21 --script ftp-anon,ftp-syst "$IP"
```

**Exam reminder:** `get`, `mget`, `curl -o` and similar file transfers **download target files to Kali**. OffSec permits that only when necessary to compromise the target, and requires deletion after objectives. Directory listings and in-place reading are preferable.
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
ssh -p 22 "USERNAME@$IP"
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

**Practice lab / necessary-to-compromise exception only:** `scp` downloads a target file to Kali; do **not** run this during the exam unless the official exception applies, and delete the copy after objectives. If appropriate, inspect the file in place through the authorized shell. From your Kali terminal:

```bash
mkdir -p evidence/ssh
scp -P 22 "USERNAME@$IP:/home/USERNAME/notes.txt" evidence/ssh/
```

Replace usernames, paths and ports with actual values. `scp -P` uses an uppercase P for port. If the host only supports SFTP:

```bash
sftp -P 22 "USERNAME@$IP"
```

Then use `pwd`, `ls`, `cd`, and `bye` for navigation; `get notes.txt` is a **download** and subject to the same exam restriction as `scp`. Do not download private material outside the lab scope.


### SSH — potential checks to test

- **Banner/algorithms:** collect server product, host-key types and key-exchange/cipher algorithms with `ssh2-enum-algos` and `ssh-hostkey`. Outdated options are hardening leads, not automatic footholds.
- **Authentication:** try only explicitly supplied credentials/keys; note whether the authorized identity has shell/SFTP access and its effective user. Do not use account guessing or brute-force tools.
- **Version/CVE:** verify exact package build, distro patch backports and exploit preconditions. A common OpenSSH banner does not demonstrate that a CVE is exploitable.
- **Post-login context:** if authorized, inspect `id`, `sudo -l`, local listening services and file permissions using the [Linux privilege-escalation guide](../04-Privilege-Escalation/linux-privesc.md).

**Potential issue:** reused assigned credentials, exposed weaker auth configuration, or a verified version-specific flaw. **Do not** equate SSH availability with access.
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


### DNS — potential checks to test

- **Records:** check `A`, `AAAA`, `CNAME`, `NS`, `MX`, `TXT`, `SRV` and PTR for assigned hosts/domains. Domain-controller SRV records may reveal additional in-scope machines.
- **Zone transfer:** test `AXFR` **only for the assigned zone**, against an authoritative server; refusal is expected on properly restricted servers.
- **Unintended disclosure:** look for internal hostnames, nonstandard service locations, admin zones, or lab-only TXT records. Do not broaden scope just because DNS reveals a name.
- **Recursion/transfer policy:** note whether the server is authoritative or recursive; assess only with queries for names the lab authorizes, never use third-party targets or DNS spoofing.

```bash
export DOMAIN=example.lab          # Replace with assigned domain
dig @"$IP" "$DOMAIN" NS
dig @"$IP" _ldap._tcp.dc._msdcs."$DOMAIN" SRV
dig @"$IP" "$DOMAIN" AXFR          # Only on assigned zone
```

**UDP note:** an inconclusive `53/udp open|filtered` result needs a real DNS query or version/service probe; the same service may use TCP/53.
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


### SNMP — potential checks to test

- **Version and supplied community:** is SNMPv1/v2c accessible using a **lab-provided** community, or is SNMPv3 required? A failed SNMP query does not confirm no service.
- **System and interface clues:** review system name/description, interfaces, IPs, routes and running network-service hints **only within authorized access**.
- **Security exposure:** unauthenticated or weakly protected management information is a configuration finding; do not automatically walk all OIDs or try random strings across hosts.
- **Write access:** identify whether your provided account/community has write capabilities from the authorized configuration; **do not use `snmpset`** as a routine test.

```bash
snmpget -v2c -c COMMUNITY "$IP" 1.3.6.1.2.1.1.5.0
snmpwalk -v2c -c COMMUNITY "$IP" 1.3.6.1.2.1.2.2.1.2
```

Both commands require a supplied or expressly approved community. Confirm the actual UDP port and version and record retrieved values without publishing sensitive management data.
## 7. SMTP — Mail service (25/465/587)

```bash
sudo nmap -Pn -sV -p 25,465,587 --script smtp-commands -oA scans/smtp-info "$IP"
```

Review supported SMTP commands, TLS options, banner information and mail domain configuration. Do not send unsolicited mail or perform large-scale address guessing.

### Practical SMTP enumeration — commands and interpretation

SMTP is a **mail transport protocol**, not a remote file browser. You can inspect the server's greeting and supported commands without sending a message.

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

After the implicit TLS handshake, send `EHLO kali.lab` and `QUIT` in the encrypted session. For STARTTLS, the SMTP capabilities may change after upgrading to TLS, so repeat `EHLO` after the handshake.

Inspect the certificate, hostname, server greeting, `EHLO` extensions, and whether STARTTLS and AUTH are advertised. `AUTH` being advertised does not mean anonymous login is possible.

To save a non-authenticating SMTP capability check on plaintext port 25 (some servers close connections or require a valid hostname):

```bash
printf 'EHLO kali.lab\r\nQUIT\r\n' | nc -w 5 "$IP" 25 | tee scans/smtp-ehlo.txt
```

**Do not** attempt open-relay testing by delivering mail to third parties, bulk recipient guessing, or unsolicited messages. SMTP generally does not let you list mailboxes or download emails. Mailbox access uses separate protocols such as POP3 or IMAP with authorized credentials.


### SMTP — potential checks to test

- **Banner/EHLO:** enumerate capabilities (`STARTTLS`, `AUTH`, `VRFY`, `EXPN`, `SIZE`, NTLM) and server/domain names; `EHLO` is not an authentication attempt.
- **TLS:** compare advertised STARTTLS support on the actual port with TLS certificate details; a server may hide `AUTH` until TLS is negotiated.
- **User enumeration:** if `VRFY`/`EXPN` are advertised, test **at most an explicitly supplied lab identity** when permitted. Do not run bulk recipient guessing, `smtp-enum-users` wordlists, or password spraying.
- **Open relay:** an EHLO capability list cannot prove relay. Only perform a controlled relay test when the lab **explicitly authorizes** it and the sender/recipient/test destination are owned by the lab; avoid delivering real messages or using third-party addresses.
- **AD clues:** if NTLM is advertised, targeted `smtp-ntlm-info` may disclose host/domain/build details; inspect `nmap --script-help smtp-ntlm-info` first.

```bash
nmap --script-help smtp-commands
sudo nmap -Pn -sV -p 25 --script smtp-commands "$IP"  # Replace with discovered SMTP port
printf 'EHLO kali.lab\r\nQUIT\r\n' | nc -w 5 "$IP" 25
```

**Record:** server banner, auth policy, advertised commands, STARTTLS, domain names and precisely what was **not** verified (e.g. relay not tested). For mailbox access, see the POP3/IMAP section below.
## 8. NFS — Network File System (111/2049)

```bash
sudo nmap -Pn -sV -p 111,2049 --script nfs-showmount,nfs-ls -oA scans/nfs-info "$IP"
showmount -e "$IP"
```

Check exports and client restrictions. Do not assume that an exported path is accessible or writable; verify with authorized, non-destructive checks.

### Practical NFS access and read-only file inspection

If the server exports an authorized path and your client is permitted, mount it **read-only** to avoid modifying remote files:

```bash
sudo mkdir -p /mnt/oscp-nfs
sudo mount -t nfs -o ro "$IP:/export/share" /mnt/oscp-nfs
ls -lah /mnt/oscp-nfs
find /mnt/oscp-nfs -maxdepth 2 -type f 2>/dev/null
```

Replace `/export/share` with a real exported path. **Exam warning:** `cp` from a mounted remote export to Kali is a download. Do not perform it unless required to compromise the machine, then delete the local copy after the objective. For ordinary authorized practice labs, an explicitly permitted example is:

```bash
mkdir -p evidence/nfs
cp /mnt/oscp-nfs/readme.txt evidence/nfs/
file evidence/nfs/readme.txt
sudo umount /mnt/oscp-nfs
```

Export listing does not guarantee access: server restrictions, protocol versions and filesystem permissions still apply.


### NFS/RPC — potential checks to test

- **RPC program discovery:** `rpcinfo -p` identifies services/ports registered through rpcbind (which may not be 111/2049); investigate any discovered in-scope nonstandard program ports.
- **Exports:** `showmount -e` lists some NFS exports; compare permitted client restrictions and whether the assigned account can mount/read an explicitly authorized share **read-only**.
- **Sensitive exposures:** look for exposed mount paths, backup locations, permissions and NFS version; an export listing is not proof your client can access files.
- **Ownership mapping:** root squashing, UID/GID mapping and export permission misconfiguration are possible concerns, but **cannot be determined from a share name**. Avoid write/ownership changes and do not test `no_root_squash` destructively.

```bash
rpcinfo -p "$IP"
showmount -e "$IP"
```

**Exam restriction:** copying remotely mounted target files to Kali is a download; apply the documented exception only when necessary for compromise, then remove the local copy.
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


### RDP — potential checks to test

- **NLA/security layers:** inspect RDP security mode, TLS certificates and host/domain information from `rdp-ntlm-info` and `rdp-enum-encryption` (read each NSE help entry first).
- **Login rights:** only a lab-provided account can establish authorized access; note whether the identity is merely a remote-desktop user or has administrative rights.
- **After login:** inspect privileges, groups, network connections and local services following the [Windows privilege-escalation guide](../04-Privilege-Escalation/windows-privesc.md).
- **Version/CVE:** confirm build and patch-level preconditions; do not run blanket RDP exploitation or authentication guessing.

**Decision:** a working RDP listener is a service clue, not proof of weak credentials or a bypass.
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

**Microsoft SQL Server (usually 1433):** use an approved SQL client and credentials; first identify the server/version with Nmap. Client availability and authentication options vary by Kali installation. For example, where `impacket-mssqlclient` is installed, check its help and use the supplied lab credentials; avoid queries that modify the server.

Database results can be exported locally using approved client features, but avoid dumping entire databases or extracting personal data. Record only the minimum evidence required for the lab finding.


### Databases — potential checks to test

- **Exposure/auth:** determine whether the service accepts remote connections, what authentication is required, and whether an expressly assigned identity has more access than expected. Avoid default-credential attempts or dumping data.
- **Privileges:** after legitimate login, check **current user/role**, version, accessible databases/schema names and any dangerous permissions or server-side program execution capabilities. Only inspect; do not enable features.
- **Network/config:** note optional TLS settings, server version, local-only endpoints and OS/service-account context.
- **CVE research:** match exact vendor, version, patch and configuration. A TCP/1433 response is not enough to label MSSQL vulnerable.

Read-only authenticated examples:

```sql
-- MySQL/MariaDB (inside the mysql client)
SELECT VERSION(), CURRENT_USER();
SHOW GRANTS;

-- PostgreSQL (inside psql)
SELECT version(), current_user;
```

For **MSSQL**, an authorized query such as `SELECT @@VERSION;` and `SELECT SYSTEM_USER;` establishes basic context; avoid features like `xp_cmdshell` during enumeration unless a separate verified lab task justifies it. See [Initial Access](../03-Initial-Access/initial-access.md) for next steps after an actual verified weakness.
## 11. Additional services — inspect when discovered

**Rule:** These are **conditional service-specific checks**, not a replacement for full port scanning. Only inspect a service actually discovered on an assigned target; substitute its **real port** for examples. Keep all commands read-only and test with supplied lab credentials only.

### 11.1 LDAP / LDAPS / Global Catalog — commonly 389, 636, 3268, 3269 TCP

**Potential checks:** Anonymous rootDSE disclosure, naming contexts/domain details, LDAP signing/TLS requirements, allowed authenticated reads, relevant users/computers/groups and delegated ACLs (with an approved domain identity).

```bash
# One read-only rootDSE request; this may be denied when anonymous binds are disabled
nmap --script-help ldap-rootdse
sudo nmap -Pn -p 389 --script ldap-rootdse "$IP"
ldapsearch -x -H "ldap://$IP:389" -s base -b "" namingContexts defaultNamingContext supportedLDAPVersion
```

For secure LDAP use the actual hostname/port with `ldaps://HOST:636` and inspect the certificate. Authenticate only using assigned credentials; don't recursively dump directory objects or confuse a readable rootDSE with an exploitable authorization bypass. See [AD Enumeration](../05-Active-Directory/ad-enumeration.md).

### 11.2 Kerberos / AD domain controller — commonly 88 TCP/UDP, 464 TCP/UDP

**Potential checks:** Domain/FQDN, DC/KDC DNS records, clock skew, service principal names, account policy, permitted groups and a **specific** account's Kerberos configuration.

```bash
# Only when an AD domain was identified and is assigned
export DOMAIN=example.lab
dig @"$IP" "_kerberos._tcp.$DOMAIN" SRV
date -u
sudo nmap -Pn -sV -p 88,464 "$IP"       # Follow up, NOT a complete scan
```

Do not perform bulk username enumeration, AS-REP requests, ticket harvesting or password spraying during initial discovery. Those are separate, specifically scoped assessment decisions. Use [AD Attack Paths](../05-Active-Directory/ad-attack-paths.md) after validating rights and preconditions.

### 11.3 POP3 / POP3S / IMAP / IMAPS — commonly 110, 995, 143, 993 TCP

**Potential checks:** Service greeting, `CAPA`/`CAPABILITY` features, TLS/STARTTLS, plaintext-auth policy, authentication requirements and whether an **assigned test mailbox** is accessible.

```bash
nmap --script-help pop3-capabilities
nmap --script-help imap-capabilities
sudo nmap -Pn -sV -p 110,143 --script pop3-capabilities,imap-capabilities "$IP"
printf 'a1 CAPABILITY\r\na2 LOGOUT\r\n' | nc -w 5 "$IP" 143
openssl s_client -starttls imap -connect "$IP:143" -crlf
```

Use the actual discovered ports; for implicit TLS inspect `993` or `995` instead. Do not enumerate or retrieve personal mail, try unknown passwords or bulk-guess mail users. A capability list is not a login bypass.

### 11.4 Microsoft RPC / MSRPC endpoint mapper — commonly 135 TCP, dynamic high ports

**Potential checks:** Host/domain details, advertised RPC endpoint UUIDs, service registrations, whether SMB/AD/WinRM is also present and whether authenticated management is permitted. RPC endpoints may be dynamically assigned: **don't assume the only relevant port is 135**.

```bash
sudo nmap -Pn -sV -p 135 "$IP"
# For Unix rpcbind/NFS instead:
rpcinfo -p "$IP"
```

Enumerate the actual discovered endpoint ports with Nmap first. An advertised endpoint does not automatically expose an administrative operation. Avoid remote service changes, coercion/spoofing and exploit modules as routine enumeration.

### 11.5 WinRM / WS-Management — commonly 5985 HTTP, 5986 HTTPS TCP

**Potential checks:** Whether a WinRM service responds, HTTP vs TLS, authentication challenges, service version, allowed users and whether assigned credentials grant a legitimate remote session.

```bash
sudo nmap -Pn -sV -p 5985,5986 "$IP"
curl -i "http://$IP:5985/wsman"
curl -k -i "https://$IP:5986/wsman"
```

HTTP `401`, `405` or `404` may simply indicate auth/protocol requirements; none proves exploitation. Use a WinRM client only with assigned credentials, then document the user's real privileges. `-k` disables TLS verification for controlled lab inspection.

### 11.6 Telnet / remote terminal — commonly 23 TCP

**Potential checks:** Banner, operating system, transport encryption (Telnet usually plaintext), reachable login prompt and whether a **supplied** account can log in.

```bash
sudo nmap -Pn -sV -p 23 "$IP"
nc -nv "$IP" 23
```

Do not guess usernames/passwords or expose real credentials on untrusted networks. Document a plaintext-login exposure as a configuration risk, not an automatic foothold.

### 11.7 VNC / remote desktop sharing — commonly 5900–5909 TCP

**Potential checks:** Protocol version, whether authentication is required, encryption/security options, and access permitted to a lab-provided account.

```bash
nmap --script-help vnc-info
sudo nmap -Pn -p 5900 --script vnc-info "$IP"
```

A connection to a VNC listener does not authorize interacting with another person's desktop. No brute-force/authentication-bypass tests without explicit lab scope.

### 11.8 rsync daemon — commonly 873 TCP

**Potential checks:** Anonymous module listing, exposed module names and permissions, unexpected read/write access, sensitive path exposure and daemon version. **Never assume a listed module is readable or writable**.

```bash
nmap --script-help rsync-list-modules
sudo nmap -Pn -p 873 --script rsync-list-modules "$IP"
rsync "rsync://$IP/"                  # List visible modules; no file download
rsync "rsync://$IP/MODULE/"           # List contents only if permitted
```

Do not transfer the remote files to Kali except under the official exam compromise-necessary exception. Write tests need separate explicit authorization and cleanup.

### 11.9 TFTP — commonly 69 UDP

**Potential checks:** Confirm UDP service, note missing authentication design, identify known filenames **only from authorized evidence**, and verify that any file transfers are in scope.

```bash
sudo nmap -Pn -sU -sV -p 69 "$IP"
```

TFTP has no standard directory listing, and UDP silence is inconclusive. Avoid guessing large filename lists, downloading arbitrary files or uploading executable content as part of routine enumeration.

### 11.10 Redis / Memcached — commonly 6379 / 11211 TCP

**Potential checks:** Presence of authentication, server version, whether read-only status/info commands are unexpectedly accessible without approved credentials, service binding and configured network exposure.

```bash
redis-cli -h "$IP" -p 6379 PING
redis-cli -h "$IP" -p 6379 INFO server     # May require authentication
printf 'version\r\nquit\r\n' | nc -w 5 "$IP" 11211
```

Record only harmless status/metadata. Never use `CONFIG SET`, filesystem writes, replication changes, FLUSH commands or bulk key/value extraction during basic enumeration. An exposed port is not automatically unauthenticated access.

### 11.11 MongoDB / Elasticsearch / OpenSearch — commonly 27017 / 9200 TCP

**Potential checks:** Transport security, authentication requirement, product/version, whether harmless status/health endpoints respond anonymously and whether the service is bound to a public interface.

```bash
# The following read-only checks may return an expected access-denied response
mongosh "mongodb://$IP:27017" --quiet --eval 'db.runCommand({hello:1})'
curl -i "http://$IP:9200/"
curl -i "http://$IP:9200/_cluster/health"
```

For TLS, use the discovered scheme/port and verify certificate behavior. Avoid listing/dumping whole databases, indices, user records or modifying cluster settings. A cluster health response may be intentionally public.

### 11.12 Docker / Kubernetes / container management APIs — commonly 2375, 2376, 6443 TCP

**Potential checks:** HTTP/TLS transport, authentication, exposed API version, authorization for a read-only status request, and whether the endpoint is actually reachable from the assigned host.

```bash
# Only if these APIs were identified on these exact discovered ports
curl -i "http://$IP:2375/version"      # Unencrypted Docker API: investigate exposure
curl -k -i "https://$IP:6443/version"  # Kubernetes API version/health clue
```

These are sensitive management interfaces. **Do not create pods, run containers, attach to exec endpoints, retrieve cluster secrets or change configuration** during enumeration. A reachable version endpoint is a lead, not administrative access.

### 11.13 HTTP proxies / management consoles — often 3128, 8080, 8000, 8443 TCP

**Potential checks:** Does the listener speak HTTP, provide a proxy challenge (`407`), present an admin UI, use default vhost routing or expose an authentication boundary?

```bash
curl -i "http://$IP:8080/"             # Use the discovered port
sudo nmap -Pn -sV -p 8080 "$IP"
```

Use [Web Enumeration](../02-Web-Application/web-enumeration.md) for any UI. An open proxy finding requires a **specifically authorized test destination**; never forward traffic to third-party sites or out-of-scope internal hosts.

### 11.14 Message protocols — MQTT (1883/8883), AMQP (5672/5671), SIP (5060/5061)

**Potential checks:** Product/version, TLS, authentication requirements, exposed management interface, and whether anonymous capabilities or assigned test accounts have excess rights.

```bash
sudo nmap -Pn -sV -p 1883,8883,5672,5671,5060,5061 "$IP"
# SIP may use UDP; probe only discovered or specifically relevant in-scope ports
sudo nmap -Pn -sU -sV -p 5060 "$IP"
```

For MQTT/AMQP, inspect only assigned broker topics/queues and **do not publish messages or subscribe broadly**. For SIP, do not originate calls, register arbitrary extensions or brute-force credentials. Treat any claimed anonymous access as unverified until a minimally scoped manual check confirms it.

### 11.15 Other high-value service clues

| Service / common ports | What to look for without disruptive actions |
| --- | --- |
| NTP (123/UDP) | Server version/time behavior; clock skew affecting Kerberos; no reflection/amplification testing |
| RADIUS (1812/1813 UDP) | Authentication-service identity/configuration from authorized context; no bulk shared-secret guessing |
| Java RMI/JMX (1099/9010/etc.) | Registry/management endpoint exposure and authentication; no arbitrary code/deserialization payloads during discovery |
| X11 (6000+) | Unexpected remote display access; do not view or interfere with private sessions |
| Printer protocols (515, 631, 9100) | Exposed admin UI, model/version and auth; no unsolicited print jobs |
| Git / dev service (9418, 3000, 5000, 8081, etc.) | Public project/repository listing, permissions, version and access boundaries; no source-code downloads outside OffSec's exam exception |
| Other UDP services | Run `-sU -sV` against relevant discovered ports and assess `open|filtered` carefully |

**When a service is unfamiliar:** use `nmap -sV` on its **actual** port, inspect its banner with a suitable read-only protocol client, identify product/version and default authentication requirements, consult trusted vendor documentation/CVEs, and decide on **one** focused authorized verification. Unknown ≠ unimportant; odd ports may be the entry point.

## 12. Investigate potential vulnerabilities

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

- [ ] Review **every** confirmed open TCP port, including nonstandard ports, and record the UDP coverage/expansion decision.
- [ ] Do not treat fixed examples such as `-p 80,443` as complete scans.
- [ ] Apply the exam file-download exception strictly; delete any permitted local downloads after objectives.
- [ ] Confirm the real service, even on nonstandard ports.
- [ ] Enumerate web applications, including hostnames and virtual hosts.
- [ ] Inspect accessible SMB shares and permissions.
- [ ] Check FTP, SSH, DNS and SNMP as applicable.
- [ ] For SMB: evaluate guest access, actual share permissions, dialects, signing and in-scope domain identity.
- [ ] For FTP: check anonymous auth, directory listings, permissions and possible web-root relationship.
- [ ] For SMTP and POP3/IMAP: check capabilities, TLS, permitted auth and possible information leakage (no bulk enumeration).
- [ ] For DNS/SNMP: inspect assigned records and authorized management information; validate UDP responses.
- [ ] For NFS/RPC: enumerate registered services, exports, effective permissions and nonstandard ports.
- [ ] For SSH/RDP/WinRM: inspect protocol security and validate only supplied credentials.
- [ ] For databases/caches/management APIs: test only read-only version/health/auth controls.
- [ ] Consider LDAP/Kerberos, Telnet, VNC, rsync, TFTP, Redis, MongoDB, message brokers and unfamiliar ports **when actually discovered**.
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
