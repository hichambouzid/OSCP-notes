# Active Directory Enumeration — OSCP Field Guide

> Scope: Authorized OSCP labs and assigned domain hosts. The current OSCP+ AD scenario provides initial credentials; use **only** accounts, hosts and domains included in your assigned scope. Enumeration alone is not evidence of a privilege escalation path.

## 0. Prepare your notes

~~~text
Domain / FQDN:
Domain controller IP and hostname:
Assigned username:
Initial access host:
Reachable DNS / LDAP / SMB / Kerberos / WinRM ports:
Interesting users, groups, computers and shares:
Evidence and next step:
~~~

Avoid storing actual passwords in this public repository. Keep secrets in secure local lab notes.

## 1. Identify DC, domain and services

~~~bash
export DC=192.168.56.10
export DOMAIN=example.lab
dig @"$DC" _ldap._tcp.dc._msdcs."$DOMAIN" SRV
dig @"$DC" "$DOMAIN" A

# Full TCP port discovery on this assigned domain controller
mkdir -p scans/ad
sudo nmap -Pn -n -sS -p- -T4 \
  --min-rate 300 \
  --max-retries 1 \
  --max-scan-delay 100ms \
  --open -v -oA scans/ad/dc-tcp-all "$DC"

# Identify versions/scripts on ALL discovered open TCP ports, not a fixed AD list
DC_PORTS=$(grep -oE '[0-9]+/open/tcp' scans/ad/dc-tcp-all.gnmap | cut -d/ -f1 | sort -nu | paste -sd, -)
if [ -n "$DC_PORTS" ]; then
  sudo nmap -Pn -sC -sV -p "$DC_PORTS" -oA scans/ad/dc-services "$DC"
else
  echo "No confirmed open TCP ports; verify VPN, target IP, routing and filtering."
fi
~~~

The full-range scan uses the requested **fast timing**; a one-retry cap can miss services on lossy/rate-limited paths. Where results look incomplete, run `sudo nmap -Pn -n -sS -p- --reason -oA scans/ad/dc-tcp-verify "$DC"` and combine all confirmed open ports before concluding enumeration.

AD services often appear on ports 53, 88, 135, 139, 389, 445, 464, 636, 3268, 3269, and 5985/5986, **but these are clues, not a scan boundary**. The full TCP scan and all-discovered-port service detection above must be **repeated for every assigned AD host**, not only the DC. For each machine, run service detection on **all its discovered open TCP ports** using the extraction procedure in [Nmap Enumeration](../01-Enumeration/nmap.md). Consider relevant UDP ports (especially DNS/Kerberos/NTP) and expand UDP coverage when the initial top-100 pass is insufficient; no fixed list rules out services elsewhere. If DNS cannot resolve lab hostnames, check VPN DNS and known DC FQDN before editing your resolver. Correct hostname and time are important for Kerberos.

## 2. Use supplied credentials to map identity

On a Windows domain member:

~~~cmd
whoami /all
echo %USERDOMAIN%
echo %LOGONSERVER%
nltest /dsgetdc:example.lab
net user /domain
net group /domain
net group "Domain Admins" /domain
net view /domain
~~~

On Linux with a valid lab identity, authenticated LDAP can enumerate directory objects:

~~~bash
ldapsearch -LLL -x -H ldap://192.168.56.10 -D 'student@example.lab' -W -b 'DC=example,DC=lab' '(objectClass=user)' sAMAccountName distinguishedName
ldapsearch -LLL -x -H ldap://192.168.56.10 -D 'student@example.lab' -W -b 'DC=example,DC=lab' '(objectClass=computer)' dNSHostName operatingSystem
~~~

The prompt from -W avoids passing a password directly in command-line arguments. Replace the bind DN and base DN with your actual domain. TLS/LDAPS or SASL may be required by the DC policy.

## 3. SMB shares and Windows group information

~~~bash
smbclient -L //192.168.56.10 -U 'EXAMPLE/student'
~~~

List shares first, then inspect only those made available to your test account. SYSVOL and NETLOGON can reveal logon scripts and domain policy. Never publish real GPO passwords, keys or private files.

On Windows, additional read-only checks:

~~~cmd
net group "Domain Users" /domain
net group "Domain Computers" /domain
net accounts /domain
gpresult /r
~~~

A failed access attempt may reflect authentication scope or signing/encryption requirements, not absence of the service.

## 4. Service principal names (SPNs) and Kerberos

~~~powershell
setspn -T example.lab -Q */*
~~~

Record which service accounts own SPNs, whether pre-authentication is required, and whether delegation is configured, where visible. SPNs are **leads**, not vulnerabilities. Check DNS and system clock if tickets or domain lookups fail.

~~~bash
date -u
dig @"$DC" _kerberos._tcp."$DOMAIN" SRV
~~~

Do not perform unauthenticated mass username guessing or broad password spraying unless the lab explicitly permits it; account lockout policies matter.

### 4.1 Kerberos fundamentals — TGT versus TGS

| Item | Meaning |
| --- | --- |
| AS-REQ / AS-REP | Initial authentication request and response from the KDC |
| TGT | Ticket granting ticket, identified by krbtgt/REALM; used to request service tickets |
| TGS-REQ / TGS-REP | Request and response for a particular service ticket |
| SPN | Service principal name, such as cifs/server.example.lab or MSSQLSvc/sql.example.lab:1433 |

AS-REP roasting concerns the AS-REP encrypted response portion protected by the user's long-term key when preauthentication is disabled. It is **not cracking the TGT itself**, which is encrypted with the KRBTGT account's key. Kerberoasting concerns a service ticket encrypted with the service identity's key. Neither an ordinary TGT nor a registered SPN proves a weak password.

### 4.2 Check Kerberos connectivity and your current tickets

On a Windows domain member, using the supplied lab identity:

~~~powershell
whoami
whoami /groups
$env:USERDNSDOMAIN
$env:LOGONSERVER
Resolve-DnsName -Type SRV _kerberos._tcp.example.lab
Test-NetConnection dc.example.lab -Port 88
klist
klist tgt
~~~

Replace the sample domain and DC hostname with actual values. `klist` displays the current logon session's cached tickets; `klist tgt` displays its initial TGT. Look at the client principal, realm, server/SPN, encryption type, start/end/renew times and flags. A server principal beginning with `krbtgt/` is a TGT; other service principals normally identify service tickets. Keep ticket blobs, keys and credential material out of reports and public Git.

On Kali, if MIT Kerberos utilities are installed and configured for your authorized lab:

~~~bash
date -u
dig @"$DC" _kerberos._tcp."$DOMAIN" SRV
klist
~~~

Linux `klist` reads the local credential cache, not a remote Windows host's ticket cache. If you have no cache, that is normal before Kerberos authentication. Windows sessions authenticated through NTLM or some remote shells may have no TGT. Do not assume a missing TGT proves invalid credentials.

### 4.3 AS-REP roasting — enumerate preauthentication-disabled accounts

The AD userAccountControl flag DONT_REQ_PREAUTH is decimal **4194304** (hex 0x400000). The ACCOUNTDISABLE flag is decimal 2. Use the following read-only LDAP queries from an authorized domain account.

Windows, if the ActiveDirectory PowerShell module is available:

~~~powershell
Get-Module -ListAvailable ActiveDirectory
Import-Module ActiveDirectory
Get-ADUser -Filter 'Enabled -eq $true -and DoesNotRequirePreAuth -eq $true' -Properties DoesNotRequirePreAuth,PasswordLastSet |
  Select-Object SamAccountName,Enabled,DoesNotRequirePreAuth,PasswordLastSet
~~~

Kali, using an authenticated LDAP connection with the correct domain/base DN. Prefer trusted LDAPS or an LDAP signing/sealing configuration appropriate to the environment; the example assumes the DC certificate is trusted:

~~~bash
ldapsearch -LLL -x -H "ldaps://dc.example.lab" \
  -D 'student@example.lab' -W -b 'DC=example,DC=lab' \
  '(&(objectCategory=person)(objectClass=user)(userAccountControl:1.2.840.113556.1.4.803:=4194304)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))' \
  sAMAccountName userAccountControl pwdLastSet
~~~

If PowerView is already installed and approved in your lab, another read-only alternative is:

~~~powershell
Get-DomainUser -PreauthNotRequired |
  Select-Object samaccountname,useraccountcontrol,pwdlastset
~~~

Check enabled status separately for PowerView results. A matching enabled account is a candidate for AS-REP roasting, not a recovered credential. No SPN is required. Although a known username with disabled preauth can permit an unauthenticated AS request, authenticated directory enumeration is preferable when the exam provides credentials. An empty successful query means no matching visible objects in that search scope, not proof that the entire forest is unaffected. A failed query is inconclusive.

### 4.4 Kerberoasting — enumerate SPN-bearing accounts

~~~powershell
Get-ADUser -LDAPFilter '(&(objectCategory=person)(objectClass=user)(servicePrincipalName=*)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))' -Properties ServicePrincipalName,PasswordLastSet,msDS-SupportedEncryptionTypes |
  Select-Object SamAccountName,ServicePrincipalName,PasswordLastSet,msDS-SupportedEncryptionTypes
~~~

Without the AD module, `setspn -T example.lab -Q */*` lists SPNs, including those on computer accounts. PowerView's `Get-DomainUser -SPN` is another directory enumeration option. Identify the actual account owning each SPN, whether it is enabled, its purpose, and what relevant rights it has. Machine and managed service accounts normally have strong automatically managed passwords; a registered SPN does not establish a crackable password. AES tickets can also be relevant; RC4 is not a universal prerequisite.

### 4.5 Rubeus and Mimikatz — ticket inspection

The [official OSCP+ FAQ](https://help.offsec.com/hc/en-us/articles/4412170923924-OSCP-Exam-FAQ) explicitly lists Rubeus and Mimikatz as allowed tools, alongside PowerView, Impacket and BloodHound (Legacy/Community). This is not blanket approval of every feature: prohibited automation, spoofing and other [exam restrictions](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide) still apply. Prepare reviewed builds before the exam; do not disable security controls to run them. No AI assistance during the exam or reporting.

**Rubeus** (Windows, from a normal non-elevated session using your assigned identity; run from the directory containing your reviewed executable):

~~~powershell
.\Rubeus.exe currentluid
.\Rubeus.exe triage
.\Rubeus.exe klist /service:krbtgt
.\Rubeus.exe kerberoast /stats
~~~

The first three commands inspect the session ID and cached ticket information. `kerberoast /stats` collects statistics about SPN-bearing user accounts **without requesting roasting tickets**. It requires directory connectivity and appropriate credentials. In an elevated context Rubeus ticket listing can include other sessions; restrict inspection to your assigned session. Verify version-specific options with the tool's help. The stats command is not an AS-REP roasting check; use the preauthentication query above for that.

**Mimikatz** (Windows, current authorized logon session only):

~~~text
mimikatz # kerberos::list
mimikatz # exit
~~~

Run the reviewed Mimikatz executable from its directory first, then enter the displayed commands at its prompt. Do not type the prompt itself. Compare the listed principals and validity periods to Windows klist. No export, injection, credential dumping or security-control bypass is needed for this enumeration task. If the utility is unavailable or blocked, use native klist; a tool failure is not a negative Kerberos finding.

### 4.6 Delegation and ticket-related relationship checks

With the ActiveDirectory module:

~~~powershell
Get-ADComputer -Filter 'TrustedForDelegation -eq $true' -Properties TrustedForDelegation |
  Select-Object Name,TrustedForDelegation
Get-ADUser -LDAPFilter '(msDS-AllowedToDelegateTo=*)' -Properties msDS-AllowedToDelegateTo |
  Select-Object SamAccountName,msDS-AllowedToDelegateTo
Get-ADComputer -LDAPFilter '(msDS-AllowedToDelegateTo=*)' -Properties msDS-AllowedToDelegateTo |
  Select-Object Name,msDS-AllowedToDelegateTo
Get-ADComputer -LDAPFilter '(msDS-AllowedToActOnBehalfOfOtherIdentity=*)' -Properties PrincipalsAllowedToDelegateToAccount |
  Select-Object Name,PrincipalsAllowedToDelegateToAccount
~~~

Unconstrained delegation is a trust setting, constrained delegation identifies allowed service SPNs, and resource-based constrained delegation identifies trusted principals on the resource. Review the effective permissions and the actual service involved; default DC settings alone do not prove a useful escalation path. Also consider user service accounts with unconstrained delegation and resource-based delegation on non-computer service objects where relevant.

### 4.7 Decision and evidence

| Observation | Next check |
| --- | --- |
| Enabled user with DONT_REQ_PREAUTH | Verify the exact identity and AS-REP roasting prerequisites |
| Enabled user with SPN | Identify service, account ownership, privileges and Kerberoasting prerequisites |
| TGT in current cache | Check client, realm, validity and current authentication context |
| Service ticket in cache | Check exact SPN and service authorization; ticket possession is not admin access |
| No cached tickets | Check logon session, NTLM versus Kerberos, DNS, clock, and DC reachability |
| Delegation configuration | Determine which identity and resource are actually involved |
| Neither roasting lead appears | Return to shares, ACLs, local privileges, management services and AD relationships |

Record account name, enabled status, relevant flag/SPN, scope, current identity, host, time, tool version and next hypothesis. Do not record raw ticket blobs, hashes, passwords or exam machine details in this public repository. See [AD Attack Paths](./ad-attack-paths.md) for deciding which findings matter.

## 5. Account privileges and AD relationships

Determine:
- Current user and group memberships; nested groups and privileged delegated groups.
- Computer accounts, operating systems, domain controllers and likely administrative hosts.
- Which account controls or can edit which group/object permissions.
- Which services and shares your assigned identity legitimately reaches.
- Whether Windows remote management or RDP is available to your assigned account.

For visual relationship analysis, tools such as BloodHound may be useful in training environments. **OffSec does not individually approve every collector or feature**: evaluate whether collection is within scope and whether it triggers prohibited automation before exam use.

## 6. Credentialed enumeration workflow

1. Confirm domain DNS, DC and time synchronization.
2. Verify the starting account and its group memberships.
3. List reachable hosts and exposed domain services.
4. Enumerate permitted SMB shares, scripts and policies.
5. Review SPNs, privileged groups and object relationships.
6. Prioritize the single shortest plausible lateral-movement or privilege path.
7. Record hypotheses and only then test the relevant permissions.

## Common troubleshooting

| Problem | Next check |
| --- | --- |
| Kerberos clock-skew error | Correct target-relative clock and timezone |
| Cannot resolve DC | VPN DNS and SRV records |
| LDAP bind fails | Base DN, UPN/DOMAIN syntax, LDAP signing/LDAPS |
| SMB access denied | Permissions, auth format, SMB policies |
| Empty groups/users | Wrong domain/base DN or insufficient permissions |
| WinRM fails | Listener, firewall, allowed users, credentials |

## OSCP checklist

- [ ] Scanned all 65,535 TCP ports on **each** in-scope AD host, not merely the DC or common AD ports.
- [ ] Ran version/service detection on every discovered open TCP port and recorded UDP coverage.
- [ ] Verified DC, domain FQDN, DNS and time.
- [ ] Starting credentials tested only against in-scope targets.
- [ ] Users, groups, computers, SPNs and shares documented.
- [ ] Current TGT/TGS cache checked where available; preauth-disabled accounts, SPN-bearing users and delegation candidates enumerated.
- [ ] Rubeus/Mimikatz used only as needed and in line with current exam restrictions; no secret ticket material stored publicly.
- [ ] Effective access and delegated relationships evaluated.
- [ ] Suspected AD attack path written as evidence + preconditions.
- [ ] No secrets or exam evidence committed publicly.

**Next:** [AD Attack-Path Validation](./ad-attack-paths.md)

## References

- [OffSec OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide)
- [Microsoft Active Directory overview](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/get-started/virtual-dc/active-directory-domain-services-overview)
- [Microsoft setspn command](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/setspn)

- [OffSec OSCP+ Exam FAQ](https://help.offsec.com/hc/en-us/articles/4412170923924-OSCP-Exam-FAQ)
- [Microsoft klist](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/klist)
- [Microsoft UserAccountControl flags](https://learn.microsoft.com/en-us/troubleshoot/windows-server/active-directory/useraccountcontrol-manipulate-account-properties)
- [Rubeus official project](https://github.com/GhostPack/Rubeus)
- [Mimikatz official project](https://github.com/gentilkiwi/mimikatz)
