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

For visual relationship analysis, use SharpHound and BloodHound Legacy/Community Edition as explicitly listed in the OffSec FAQ. See section 5.1 for scoped collection, import, and manual relationship validation.

### 5.1 SharpHound and BloodHound — collect and interpret AD relationships

**Roles:** SharpHound is the Windows AD data collector. BloodHound is the graph analysis interface. SharpHound produces JSON records, normally packaged into a ZIP. BloodHound ingests those records and shows directory objects, group memberships, permissions, and possible paths. Neither tool cracks passwords.

**Exam rules:** The [OSCP+ FAQ](https://help.offsec.com/hc/en-us/articles/4412170923924-OSCP-Exam-FAQ) explicitly permits SharpHound and BloodHound **Legacy and Community Edition only**. Do not use Enterprise/commercial features or prohibited automation. Read the [exam guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide), including the file-download restriction: exam target files may be downloaded only when necessary to compromise an exam machine, and permitted copies must be deleted after completing the objectives. Keep collection data local and private, not in a public repository or hosted service.

#### Step 1 — Prepare BloodHound before the exam

- Install BloodHound Community Edition on your local authorized lab machine using its [official quickstart](https://bloodhound.specterops.io/get-started/quickstart/community-edition-quickstart). The official CLI is the recommended installation method; confirm Docker/Compose requirements for your release.
- Open the local BloodHound interface, set a strong local admin password, and confirm that sample data imports correctly before the exam.
- In CE, use Settings / Download Collectors to obtain the corresponding SharpHound CE build. Keep the collector and BloodHound versions compatible; Legacy and CE collectors/data schemas are not automatically interchangeable.
- Use a separate local graph/database for each lab. Do not leave a graph of a different domain mixed with the current one.

#### Step 2 — Confirm the collection scope and starting identity

On the authorized Windows domain member, using the supplied lab account:

~~~powershell
whoami
$env:USERDNSDOMAIN
$env:LOGONSERVER
Resolve-DnsName -Type SRV _ldap._tcp.dc._msdcs.example.lab
.\SharpHound.exe --help
~~~

Substitute your assigned domain and verify that the collector build supports the listed options. A normal domain account can typically read substantial directory metadata; it cannot necessarily read all local groups or session information on every host. Do not elevate privileges solely to improve collection coverage.

#### Step 3 — Start with DC-only directory enumeration

When the lab authorizes directory-wide enumeration in the assigned domain, use the DC-only collection method first:

~~~powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\oscp-ad-collection" | Out-Null
.\SharpHound.exe --CollectionMethods DCOnly --Domain example.lab --OutputDirectory "$env:USERPROFILE\oscp-ad-collection"
Get-ChildItem "$env:USERPROFILE\oscp-ad-collection"
~~~

**What this collects:** directory group memberships, object properties, ACL relationships, domain trusts, OUs and GPO links, plus some GPO-derived local-group relationships. It does not query each domain-joined computer for live sessions or local groups. Use the actual authorized domain and ensure the selected DC is within scope. Where only a subset of directory objects is authorized, use a suitable directory search base/filter or manual LDAP checks instead of domain-wide collection.

Do not default to `All`, forest-wide collection, or repeated session loops. Those increase collection scope, time and unnecessary traffic. A domain trust in the graph is not permission to enumerate the other domain.

#### Step 4 — Understand additional collection options

| Method | Information | When useful |
| --- | --- | --- |
| DCOnly | Directory relationships without contacting all members | Initial domain graph |
| Group | Domain group memberships | Focused membership checks |
| ACL | Directory object permissions | Validate delegated rights |
| ObjectProps | Directory object properties | Review SPNs and account configuration |
| LocalGroup / LocalAdmin | Host-local group membership | Only when specific assigned hosts and access permit |
| Session | Observed user sessions on member computers | Only when explicitly authorized and needed |

The official [SharpHound CE flags](https://bloodhound.specterops.io/collect-data/ce-collection/sharphound-flags) document `--ComputerFile` for a line-separated list of specific computer names/IPs. Use that scope control for host-specific collection when needed rather than querying every computer. A missing local-admin/session edge in a DCOnly collection is an **information gap**, not proof that the relationship does not exist. Permission failures and stale session observations also affect coverage.

#### Step 5 — Import the dataset

In authorized practice labs, move the generated ZIP to your private local BloodHound instance only using an approved method. In the actual exam, obey the OffSec file-download exception above; a collector being allowed does not authorize unrestricted downloading. Use only the necessary data, and never upload exam data to third-party services.

In BloodHound CE:

1. Open Administration > Data Collection > File Ingest.
2. Select Upload File(s) and choose the collected ZIP or compatible JSON files.
3. Wait for the import status to finish successfully.
4. Open Explore and search for the assigned account, such as STUDENT@EXAMPLE.LAB.
5. Click the node and inspect group memberships, outbound relationships, inbound relationships, object properties and collection timestamps.

The Legacy interface uses its own compatible import workflow. Avoid importing the same dataset repeatedly into unrelated graphs.

#### Step 6 — Interpret the graph rather than following it blindly

In Explore, start from your known account, review its groups, and use Pathfinding to inspect a route to an actual in-scope objective. For a lab exercise you may select the relevant administrative group or assigned computer as the destination. Inspect each edge individually and read the explanation provided by BloodHound.

| Edge or property | Meaning to verify manually |
| --- | --- |
| MemberOf | Direct/nested group membership and resulting rights |
| AdminTo | Indicated local-administrator relationship; confirm current access |
| CanRDP / CanPSRemote | Relevant local group/remote management relationship; check actual host configuration |
| GenericAll / GenericWrite | Broad object permissions; identify the exact affected object and effective ACL |
| WriteDacl / WriteOwner | Permission to modify ACL/ownership; verify effective rights |
| AddMember | Ability to change a particular group's membership; assess scope and prerequisites |
| HasSession | Observed user session; may be stale or incomplete |
| SPN / preauth property | Possible Kerberos password-auditing lead, not a recovered password |
| Delegation-related edge | Configured delegation relationship; check service, identity and effective permissions |

Use the built-in query library or node properties to review groups, SPN-bearing accounts, preauthentication-disabled users, and delegation relationships where the relevant data is available. Cross-check these against the native LDAP/PowerShell commands in section 4. Shortest graph path does not necessarily mean easiest or feasible path: network routing, account policy, privileges, service availability and collection age can invalidate it.

#### Step 7 — Troubleshoot and record results

| Problem | Check first |
| --- | --- |
| Collector cannot locate domain | DNS SRV, DC FQDN, assigned domain, VPN route |
| LDAP bind fails | Current identity, credentials, signing/LDAPS requirements |
| ZIP missing | Output directory, collector errors, filesystem permissions |
| Import fails | SharpHound/BloodHound version compatibility and ZIP/JSON integrity |
| No graph path | Missing collection methods, wrong source/destination, incomplete permissions |
| Edge disagrees with manual test | Collection age, actual token, nested groups, effective ACL, target availability |

Record the scope, collection command, tool version, data timestamp, missing collection methods, current identity, candidate relationship and manual validation result. Do not use an empty graph to conclude that the target is secure. Do not store raw directory datasets, ticket material, credentials or actual exam evidence in this repository.

**Next:** [AD Attack Paths](./ad-attack-paths.md) explains how to turn verified relationships into a prioritized plan, and includes the offline Kerberos hash-auditing workflow.

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
- [ ] If using SharpHound/BloodHound, recorded the authorized collection scope, imported matching-version data privately, and manually checked relevant graph edges.
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

- [BloodHound CE quickstart](https://bloodhound.specterops.io/get-started/quickstart/community-edition-quickstart)
- [SharpHound CE collection flags](https://bloodhound.specterops.io/collect-data/ce-collection/sharphound-flags)
