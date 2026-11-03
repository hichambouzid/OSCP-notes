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
sudo nmap -Pn -sS -p- --reason -oA scans/ad/dc-tcp-all "$DC"

# Targeted follow-up only: use ports actually found in the full scan
sudo nmap -Pn -sV -p 53,88,135,139,389,445,464,636,3268,3269 "$DC"
~~~

The `-p 53,88,...` command is a **common AD-port example**, not complete enumeration; the full TCP scan above is mandatory for **every assigned AD machine**, not only the DC. For each machine, run service detection on **all its discovered open TCP ports** using the extraction procedure in [Nmap Enumeration](../01-Enumeration/nmap.md). Consider relevant UDP ports (especially DNS/Kerberos/NTP) and expand UDP coverage when the initial top-100 pass is insufficient; no fixed list rules out services elsewhere. If DNS cannot resolve lab hostnames, check VPN DNS and known DC FQDN before editing your resolver. Correct hostname and time are important for Kerberos.

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
- [ ] Effective access and delegated relationships evaluated.
- [ ] Suspected AD attack path written as evidence + preconditions.
- [ ] No secrets or exam evidence committed publicly.

**Next:** [AD Attack-Path Validation](./ad-attack-paths.md)

## References

- [OffSec OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide)
- [Microsoft Active Directory overview](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/get-started/virtual-dc/active-directory-domain-services-overview)
- [Microsoft setspn command](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/setspn)
