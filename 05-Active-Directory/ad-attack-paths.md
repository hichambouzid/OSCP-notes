# Active Directory Attack Paths — OSCP Lab Decision Guide

> Purpose: Convert **observed** AD relationships into a defensible test plan in your authorized lab. This guide emphasizes preconditions, evidence, permitted tooling and troubleshooting. It is not a checklist of attacks to run blindly.

**Start here:** [AD Enumeration](./ad-enumeration.md) and [Password Auditing](../06-Passwords/password-auditing.md).

## How to reason about an AD path

For each candidate path, write:

~~~text
Current identity / host:
Target account / host:
Observed right or misconfiguration:
Why this right might permit the next action:
What authentication or network access is required:
Single test to validate the hypothesis:
Expected evidence:
Potential service interruption / account lockout risk:
Result / next step:
~~~

## 1. Provided credentials and legitimate remote access

On the supplied account, ask:
- Is this identity a local administrator on an in-scope member server?
- Does the account have permitted access to a share, RDP, WinRM or a database?
- Is the management port reachable from this machine or only from another network?
- Is there a simpler approved path using existing permissions?

For example, with a **known authorized** Windows account:

~~~powershell
Test-NetConnection server.example.lab -Port 5985
Test-NetConnection server.example.lab -Port 3389
~~~

Network reachability does not establish authorization. Use only the assigned credentials and approved hosts.

## 2. AS-REP roasting — precondition triage

**Enumeration first:** [AS-REP account checks](./ad-enumeration.md#43-as-rep-roasting--enumerate-preauthentication-disabled-accounts) includes native PowerShell, LDAP and PowerView queries. Look for enabled accounts with DONT_REQ_PREAUTH (4194304). No SPN is required. The AS-REP encrypted response portion, not the KRBTGT-encrypted TGT, is the relevant password-auditing material. The flag establishes exposure, not password recovery.

**What must be true:** An in-scope account has Kerberos preauthentication disabled, and the environment permits a request for that account. Determine whether the account and policy are actually relevant first. Requests for ticket material and any offline cracking must stay within the lab authorization. Do not run this across real user directories.

**Investigate:** Which specific object has the flag? Is it a service/normal user? Is it within scope? Would exploiting that identity contribute to the next objective?

## 3. Kerberoasting — precondition triage

**Enumeration first:** [SPN-bearing account checks](./ad-enumeration.md#44-kerberoasting--enumerate-spn-bearing-accounts) identifies account ownership, enabled status and password age. Rubeus `kerberoast /stats` enumerates statistics without requesting roasting tickets. Both AES and RC4 may be relevant; a service ticket does not demonstrate a weak password.

**What must be true:** A service account has an SPN and you possess an authorized domain identity capable of requesting relevant service tickets. A returned ticket is not a guaranteed weak password. Avoid large indiscriminate ticket requests or credential attacks without scope.

~~~cmd
setspn -T example.lab -Q */*
~~~

Document the account, service, ticket type and whether any legitimate path exists independent of password recovery. If practicing offline auditing, see [Password Auditing](../06-Passwords/password-auditing.md).

## 3A. Kerberos ticket and delegation decision guide

Start with [current ticket inspection](./ad-enumeration.md#42-check-kerberos-connectivity-and-your-current-tickets) and [Rubeus/Mimikatz inspection](./ad-enumeration.md#45-rubeus-and-mimikatz--ticket-inspection). These commands are for checking your authorized session and directory exposure.

| Technique | Necessary condition / evidence | What not to assume |
| --- | --- | --- |
| AS-REP roasting | Enabled identity with preauthentication disabled | The account password is weak |
| Kerberoasting | Relevant SPN-bearing identity and a permissible service-ticket request | An SPN proves credential recovery |
| Pass-the-Ticket | Valid ticket and applicable session/realm/service scope | A ticket automatically grants admin access |
| Pass-the-Hash | Relevant NTLM credential and service accepting that authentication | This is the same as Kerberos ticket authentication |
| Unconstrained delegation | Relevant trusted service/computer and applicable Kerberos context | Every trusted computer is an immediate path |
| Constrained delegation | A relevant service and configured delegation target SPN; applicable protocol transition settings | Delegation to arbitrary services is permitted |
| Resource-based constrained delegation | Resource's delegation security descriptor and relevant effective principal rights | The presence of a descriptor alone establishes exploitability |
| Golden Ticket | Compromise of the domain KRBTGT key | A normal user's TGT provides the KRBTGT key |
| Silver Ticket | Compromise of the relevant service identity key | A service ticket provides its service account's key |
| DCSync | Effective directory replication rights over the relevant domain naming context | Any domain account can replicate credentials |

Golden/Silver Ticket and DCSync are higher-impact post-compromise topics, not first-line enumeration tasks. Distinguish authentication from authorization at every step. A valid ticket does not prove the current identity can access a particular administrative service.

**Tool choice:** Windows klist is the fastest first check. Rubeus is useful for Kerberos-specific metadata and SPN statistics. Mimikatz offers Kerberos inspection in addition to other sensitive capabilities; listing your own session's tickets does not require credential dumping, ticket export, or injection. The [official OSCP+ FAQ](https://help.offsec.com/hc/en-us/articles/4412170923924-OSCP-Exam-FAQ) names both Rubeus and Mimikatz as allowed, subject to feature restrictions in the exam guide.

## 3B. Offline password auditing — AS-REP and TGS hashes

Use only authorized, already obtained roasting-format hashes from your practice lab. This section tests password candidates offline; it does not crack an arbitrary TGT, .kirbi file or credential cache. A normal TGT is protected by the KRBTGT key, not the user's password. Do not confuse ticket replay with password recovery.

### Choose the hash mode

| Hash prefix | Kerberos encryption type | Hashcat mode |
| --- | --- | --- |
| `$krb5asrep$23# Active Directory Attack Paths — OSCP Lab Decision Guide

> Purpose: Convert **observed** AD relationships into a defensible test plan in your authorized lab. This guide emphasizes preconditions, evidence, permitted tooling and troubleshooting. It is not a checklist of attacks to run blindly.

**Start here:** [AD Enumeration](./ad-enumeration.md) and [Password Auditing](../06-Passwords/password-auditing.md).

## How to reason about an AD path

For each candidate path, write:

~~~text
Current identity / host:
Target account / host:
Observed right or misconfiguration:
Why this right might permit the next action:
What authentication or network access is required:
Single test to validate the hypothesis:
Expected evidence:
Potential service interruption / account lockout risk:
Result / next step:
~~~

## 1. Provided credentials and legitimate remote access

On the supplied account, ask:
- Is this identity a local administrator on an in-scope member server?
- Does the account have permitted access to a share, RDP, WinRM or a database?
- Is the management port reachable from this machine or only from another network?
- Is there a simpler approved path using existing permissions?

For example, with a **known authorized** Windows account:

~~~powershell
Test-NetConnection server.example.lab -Port 5985
Test-NetConnection server.example.lab -Port 3389
~~~

Network reachability does not establish authorization. Use only the assigned credentials and approved hosts.

## 2. AS-REP roasting — precondition triage

**Enumeration first:** [AS-REP account checks](./ad-enumeration.md#43-as-rep-roasting--enumerate-preauthentication-disabled-accounts) includes native PowerShell, LDAP and PowerView queries. Look for enabled accounts with DONT_REQ_PREAUTH (4194304). No SPN is required. The AS-REP encrypted response portion, not the KRBTGT-encrypted TGT, is the relevant password-auditing material. The flag establishes exposure, not password recovery.

**What must be true:** An in-scope account has Kerberos preauthentication disabled, and the environment permits a request for that account. Determine whether the account and policy are actually relevant first. Requests for ticket material and any offline cracking must stay within the lab authorization. Do not run this across real user directories.

**Investigate:** Which specific object has the flag? Is it a service/normal user? Is it within scope? Would exploiting that identity contribute to the next objective?

## 3. Kerberoasting — precondition triage

**Enumeration first:** [SPN-bearing account checks](./ad-enumeration.md#44-kerberoasting--enumerate-spn-bearing-accounts) identifies account ownership, enabled status and password age. Rubeus `kerberoast /stats` enumerates statistics without requesting roasting tickets. Both AES and RC4 may be relevant; a service ticket does not demonstrate a weak password.

**What must be true:** A service account has an SPN and you possess an authorized domain identity capable of requesting relevant service tickets. A returned ticket is not a guaranteed weak password. Avoid large indiscriminate ticket requests or credential attacks without scope.

~~~cmd
setspn -T example.lab -Q */*
~~~

Document the account, service, ticket type and whether any legitimate path exists independent of password recovery. If practicing offline auditing, see [Password Auditing](../06-Passwords/password-auditing.md).

## 3A. Kerberos ticket and delegation decision guide

Start with [current ticket inspection](./ad-enumeration.md#42-check-kerberos-connectivity-and-your-current-tickets) and [Rubeus/Mimikatz inspection](./ad-enumeration.md#45-rubeus-and-mimikatz--ticket-inspection). These commands are for checking your authorized session and directory exposure.

| Technique | Necessary condition / evidence | What not to assume |
| --- | --- | --- |
| AS-REP roasting | Enabled identity with preauthentication disabled | The account password is weak |
| Kerberoasting | Relevant SPN-bearing identity and a permissible service-ticket request | An SPN proves credential recovery |
| Pass-the-Ticket | Valid ticket and applicable session/realm/service scope | A ticket automatically grants admin access |
| Pass-the-Hash | Relevant NTLM credential and service accepting that authentication | This is the same as Kerberos ticket authentication |
| Unconstrained delegation | Relevant trusted service/computer and applicable Kerberos context | Every trusted computer is an immediate path |
| Constrained delegation | A relevant service and configured delegation target SPN; applicable protocol transition settings | Delegation to arbitrary services is permitted |
| Resource-based constrained delegation | Resource's delegation security descriptor and relevant effective principal rights | The presence of a descriptor alone establishes exploitability |
| Golden Ticket | Compromise of the domain KRBTGT key | A normal user's TGT provides the KRBTGT key |
| Silver Ticket | Compromise of the relevant service identity key | A service ticket provides its service account's key |
| DCSync | Effective directory replication rights over the relevant domain naming context | Any domain account can replicate credentials |

Golden/Silver Ticket and DCSync are higher-impact post-compromise topics, not first-line enumeration tasks. Distinguish authentication from authorization at every step. A valid ticket does not prove the current identity can access a particular administrative service.

**Tool choice:** Windows klist is the fastest first check. Rubeus is useful for Kerberos-specific metadata and SPN statistics. Mimikatz offers Kerberos inspection in addition to other sensitive capabilities; listing your own session's tickets does not require credential dumping, ticket export, or injection. The [official OSCP+ FAQ](https://help.offsec.com/hc/en-us/articles/4412170923924-OSCP-Exam-FAQ) names both Rubeus and Mimikatz as allowed, subject to feature restrictions in the exam guide.

 | AS-REP RC4 | 18200 |
| `$krb5tgs$23# Active Directory Attack Paths — OSCP Lab Decision Guide

> Purpose: Convert **observed** AD relationships into a defensible test plan in your authorized lab. This guide emphasizes preconditions, evidence, permitted tooling and troubleshooting. It is not a checklist of attacks to run blindly.

**Start here:** [AD Enumeration](./ad-enumeration.md) and [Password Auditing](../06-Passwords/password-auditing.md).

## How to reason about an AD path

For each candidate path, write:

~~~text
Current identity / host:
Target account / host:
Observed right or misconfiguration:
Why this right might permit the next action:
What authentication or network access is required:
Single test to validate the hypothesis:
Expected evidence:
Potential service interruption / account lockout risk:
Result / next step:
~~~

## 1. Provided credentials and legitimate remote access

On the supplied account, ask:
- Is this identity a local administrator on an in-scope member server?
- Does the account have permitted access to a share, RDP, WinRM or a database?
- Is the management port reachable from this machine or only from another network?
- Is there a simpler approved path using existing permissions?

For example, with a **known authorized** Windows account:

~~~powershell
Test-NetConnection server.example.lab -Port 5985
Test-NetConnection server.example.lab -Port 3389
~~~

Network reachability does not establish authorization. Use only the assigned credentials and approved hosts.

## 2. AS-REP roasting — precondition triage

**Enumeration first:** [AS-REP account checks](./ad-enumeration.md#43-as-rep-roasting--enumerate-preauthentication-disabled-accounts) includes native PowerShell, LDAP and PowerView queries. Look for enabled accounts with DONT_REQ_PREAUTH (4194304). No SPN is required. The AS-REP encrypted response portion, not the KRBTGT-encrypted TGT, is the relevant password-auditing material. The flag establishes exposure, not password recovery.

**What must be true:** An in-scope account has Kerberos preauthentication disabled, and the environment permits a request for that account. Determine whether the account and policy are actually relevant first. Requests for ticket material and any offline cracking must stay within the lab authorization. Do not run this across real user directories.

**Investigate:** Which specific object has the flag? Is it a service/normal user? Is it within scope? Would exploiting that identity contribute to the next objective?

## 3. Kerberoasting — precondition triage

**Enumeration first:** [SPN-bearing account checks](./ad-enumeration.md#44-kerberoasting--enumerate-spn-bearing-accounts) identifies account ownership, enabled status and password age. Rubeus `kerberoast /stats` enumerates statistics without requesting roasting tickets. Both AES and RC4 may be relevant; a service ticket does not demonstrate a weak password.

**What must be true:** A service account has an SPN and you possess an authorized domain identity capable of requesting relevant service tickets. A returned ticket is not a guaranteed weak password. Avoid large indiscriminate ticket requests or credential attacks without scope.

~~~cmd
setspn -T example.lab -Q */*
~~~

Document the account, service, ticket type and whether any legitimate path exists independent of password recovery. If practicing offline auditing, see [Password Auditing](../06-Passwords/password-auditing.md).

## 3A. Kerberos ticket and delegation decision guide

Start with [current ticket inspection](./ad-enumeration.md#42-check-kerberos-connectivity-and-your-current-tickets) and [Rubeus/Mimikatz inspection](./ad-enumeration.md#45-rubeus-and-mimikatz--ticket-inspection). These commands are for checking your authorized session and directory exposure.

| Technique | Necessary condition / evidence | What not to assume |
| --- | --- | --- |
| AS-REP roasting | Enabled identity with preauthentication disabled | The account password is weak |
| Kerberoasting | Relevant SPN-bearing identity and a permissible service-ticket request | An SPN proves credential recovery |
| Pass-the-Ticket | Valid ticket and applicable session/realm/service scope | A ticket automatically grants admin access |
| Pass-the-Hash | Relevant NTLM credential and service accepting that authentication | This is the same as Kerberos ticket authentication |
| Unconstrained delegation | Relevant trusted service/computer and applicable Kerberos context | Every trusted computer is an immediate path |
| Constrained delegation | A relevant service and configured delegation target SPN; applicable protocol transition settings | Delegation to arbitrary services is permitted |
| Resource-based constrained delegation | Resource's delegation security descriptor and relevant effective principal rights | The presence of a descriptor alone establishes exploitability |
| Golden Ticket | Compromise of the domain KRBTGT key | A normal user's TGT provides the KRBTGT key |
| Silver Ticket | Compromise of the relevant service identity key | A service ticket provides its service account's key |
| DCSync | Effective directory replication rights over the relevant domain naming context | Any domain account can replicate credentials |

Golden/Silver Ticket and DCSync are higher-impact post-compromise topics, not first-line enumeration tasks. Distinguish authentication from authorization at every step. A valid ticket does not prove the current identity can access a particular administrative service.

**Tool choice:** Windows klist is the fastest first check. Rubeus is useful for Kerberos-specific metadata and SPN statistics. Mimikatz offers Kerberos inspection in addition to other sensitive capabilities; listing your own session's tickets does not require credential dumping, ticket export, or injection. The [official OSCP+ FAQ](https://help.offsec.com/hc/en-us/articles/4412170923924-OSCP-Exam-FAQ) names both Rubeus and Mimikatz as allowed, subject to feature restrictions in the exam guide.

 | TGS-REP RC4 | 13100 |
| `$krb5tgs$17# Active Directory Attack Paths — OSCP Lab Decision Guide

> Purpose: Convert **observed** AD relationships into a defensible test plan in your authorized lab. This guide emphasizes preconditions, evidence, permitted tooling and troubleshooting. It is not a checklist of attacks to run blindly.

**Start here:** [AD Enumeration](./ad-enumeration.md) and [Password Auditing](../06-Passwords/password-auditing.md).

## How to reason about an AD path

For each candidate path, write:

~~~text
Current identity / host:
Target account / host:
Observed right or misconfiguration:
Why this right might permit the next action:
What authentication or network access is required:
Single test to validate the hypothesis:
Expected evidence:
Potential service interruption / account lockout risk:
Result / next step:
~~~

## 1. Provided credentials and legitimate remote access

On the supplied account, ask:
- Is this identity a local administrator on an in-scope member server?
- Does the account have permitted access to a share, RDP, WinRM or a database?
- Is the management port reachable from this machine or only from another network?
- Is there a simpler approved path using existing permissions?

For example, with a **known authorized** Windows account:

~~~powershell
Test-NetConnection server.example.lab -Port 5985
Test-NetConnection server.example.lab -Port 3389
~~~

Network reachability does not establish authorization. Use only the assigned credentials and approved hosts.

## 2. AS-REP roasting — precondition triage

**Enumeration first:** [AS-REP account checks](./ad-enumeration.md#43-as-rep-roasting--enumerate-preauthentication-disabled-accounts) includes native PowerShell, LDAP and PowerView queries. Look for enabled accounts with DONT_REQ_PREAUTH (4194304). No SPN is required. The AS-REP encrypted response portion, not the KRBTGT-encrypted TGT, is the relevant password-auditing material. The flag establishes exposure, not password recovery.

**What must be true:** An in-scope account has Kerberos preauthentication disabled, and the environment permits a request for that account. Determine whether the account and policy are actually relevant first. Requests for ticket material and any offline cracking must stay within the lab authorization. Do not run this across real user directories.

**Investigate:** Which specific object has the flag? Is it a service/normal user? Is it within scope? Would exploiting that identity contribute to the next objective?

## 3. Kerberoasting — precondition triage

**Enumeration first:** [SPN-bearing account checks](./ad-enumeration.md#44-kerberoasting--enumerate-spn-bearing-accounts) identifies account ownership, enabled status and password age. Rubeus `kerberoast /stats` enumerates statistics without requesting roasting tickets. Both AES and RC4 may be relevant; a service ticket does not demonstrate a weak password.

**What must be true:** A service account has an SPN and you possess an authorized domain identity capable of requesting relevant service tickets. A returned ticket is not a guaranteed weak password. Avoid large indiscriminate ticket requests or credential attacks without scope.

~~~cmd
setspn -T example.lab -Q */*
~~~

Document the account, service, ticket type and whether any legitimate path exists independent of password recovery. If practicing offline auditing, see [Password Auditing](../06-Passwords/password-auditing.md).

## 3A. Kerberos ticket and delegation decision guide

Start with [current ticket inspection](./ad-enumeration.md#42-check-kerberos-connectivity-and-your-current-tickets) and [Rubeus/Mimikatz inspection](./ad-enumeration.md#45-rubeus-and-mimikatz--ticket-inspection). These commands are for checking your authorized session and directory exposure.

| Technique | Necessary condition / evidence | What not to assume |
| --- | --- | --- |
| AS-REP roasting | Enabled identity with preauthentication disabled | The account password is weak |
| Kerberoasting | Relevant SPN-bearing identity and a permissible service-ticket request | An SPN proves credential recovery |
| Pass-the-Ticket | Valid ticket and applicable session/realm/service scope | A ticket automatically grants admin access |
| Pass-the-Hash | Relevant NTLM credential and service accepting that authentication | This is the same as Kerberos ticket authentication |
| Unconstrained delegation | Relevant trusted service/computer and applicable Kerberos context | Every trusted computer is an immediate path |
| Constrained delegation | A relevant service and configured delegation target SPN; applicable protocol transition settings | Delegation to arbitrary services is permitted |
| Resource-based constrained delegation | Resource's delegation security descriptor and relevant effective principal rights | The presence of a descriptor alone establishes exploitability |
| Golden Ticket | Compromise of the domain KRBTGT key | A normal user's TGT provides the KRBTGT key |
| Silver Ticket | Compromise of the relevant service identity key | A service ticket provides its service account's key |
| DCSync | Effective directory replication rights over the relevant domain naming context | Any domain account can replicate credentials |

Golden/Silver Ticket and DCSync are higher-impact post-compromise topics, not first-line enumeration tasks. Distinguish authentication from authorization at every step. A valid ticket does not prove the current identity can access a particular administrative service.

**Tool choice:** Windows klist is the fastest first check. Rubeus is useful for Kerberos-specific metadata and SPN statistics. Mimikatz offers Kerberos inspection in addition to other sensitive capabilities; listing your own session's tickets does not require credential dumping, ticket export, or injection. The [official OSCP+ FAQ](https://help.offsec.com/hc/en-us/articles/4412170923924-OSCP-Exam-FAQ) names both Rubeus and Mimikatz as allowed, subject to feature restrictions in the exam guide.

 | TGS-REP AES128 | 19600 |
| `$krb5tgs$18# Active Directory Attack Paths — OSCP Lab Decision Guide

> Purpose: Convert **observed** AD relationships into a defensible test plan in your authorized lab. This guide emphasizes preconditions, evidence, permitted tooling and troubleshooting. It is not a checklist of attacks to run blindly.

**Start here:** [AD Enumeration](./ad-enumeration.md) and [Password Auditing](../06-Passwords/password-auditing.md).

## How to reason about an AD path

For each candidate path, write:

~~~text
Current identity / host:
Target account / host:
Observed right or misconfiguration:
Why this right might permit the next action:
What authentication or network access is required:
Single test to validate the hypothesis:
Expected evidence:
Potential service interruption / account lockout risk:
Result / next step:
~~~

## 1. Provided credentials and legitimate remote access

On the supplied account, ask:
- Is this identity a local administrator on an in-scope member server?
- Does the account have permitted access to a share, RDP, WinRM or a database?
- Is the management port reachable from this machine or only from another network?
- Is there a simpler approved path using existing permissions?

For example, with a **known authorized** Windows account:

~~~powershell
Test-NetConnection server.example.lab -Port 5985
Test-NetConnection server.example.lab -Port 3389
~~~

Network reachability does not establish authorization. Use only the assigned credentials and approved hosts.

## 2. AS-REP roasting — precondition triage

**Enumeration first:** [AS-REP account checks](./ad-enumeration.md#43-as-rep-roasting--enumerate-preauthentication-disabled-accounts) includes native PowerShell, LDAP and PowerView queries. Look for enabled accounts with DONT_REQ_PREAUTH (4194304). No SPN is required. The AS-REP encrypted response portion, not the KRBTGT-encrypted TGT, is the relevant password-auditing material. The flag establishes exposure, not password recovery.

**What must be true:** An in-scope account has Kerberos preauthentication disabled, and the environment permits a request for that account. Determine whether the account and policy are actually relevant first. Requests for ticket material and any offline cracking must stay within the lab authorization. Do not run this across real user directories.

**Investigate:** Which specific object has the flag? Is it a service/normal user? Is it within scope? Would exploiting that identity contribute to the next objective?

## 3. Kerberoasting — precondition triage

**Enumeration first:** [SPN-bearing account checks](./ad-enumeration.md#44-kerberoasting--enumerate-spn-bearing-accounts) identifies account ownership, enabled status and password age. Rubeus `kerberoast /stats` enumerates statistics without requesting roasting tickets. Both AES and RC4 may be relevant; a service ticket does not demonstrate a weak password.

**What must be true:** A service account has an SPN and you possess an authorized domain identity capable of requesting relevant service tickets. A returned ticket is not a guaranteed weak password. Avoid large indiscriminate ticket requests or credential attacks without scope.

~~~cmd
setspn -T example.lab -Q */*
~~~

Document the account, service, ticket type and whether any legitimate path exists independent of password recovery. If practicing offline auditing, see [Password Auditing](../06-Passwords/password-auditing.md).

## 3A. Kerberos ticket and delegation decision guide

Start with [current ticket inspection](./ad-enumeration.md#42-check-kerberos-connectivity-and-your-current-tickets) and [Rubeus/Mimikatz inspection](./ad-enumeration.md#45-rubeus-and-mimikatz--ticket-inspection). These commands are for checking your authorized session and directory exposure.

| Technique | Necessary condition / evidence | What not to assume |
| --- | --- | --- |
| AS-REP roasting | Enabled identity with preauthentication disabled | The account password is weak |
| Kerberoasting | Relevant SPN-bearing identity and a permissible service-ticket request | An SPN proves credential recovery |
| Pass-the-Ticket | Valid ticket and applicable session/realm/service scope | A ticket automatically grants admin access |
| Pass-the-Hash | Relevant NTLM credential and service accepting that authentication | This is the same as Kerberos ticket authentication |
| Unconstrained delegation | Relevant trusted service/computer and applicable Kerberos context | Every trusted computer is an immediate path |
| Constrained delegation | A relevant service and configured delegation target SPN; applicable protocol transition settings | Delegation to arbitrary services is permitted |
| Resource-based constrained delegation | Resource's delegation security descriptor and relevant effective principal rights | The presence of a descriptor alone establishes exploitability |
| Golden Ticket | Compromise of the domain KRBTGT key | A normal user's TGT provides the KRBTGT key |
| Silver Ticket | Compromise of the relevant service identity key | A service ticket provides its service account's key |
| DCSync | Effective directory replication rights over the relevant domain naming context | Any domain account can replicate credentials |

Golden/Silver Ticket and DCSync are higher-impact post-compromise topics, not first-line enumeration tasks. Distinguish authentication from authorization at every step. A valid ticket does not prove the current identity can access a particular administrative service.

**Tool choice:** Windows klist is the fastest first check. Rubeus is useful for Kerberos-specific metadata and SPN statistics. Mimikatz offers Kerberos inspection in addition to other sensitive capabilities; listing your own session's tickets does not require credential dumping, ticket export, or injection. The [official OSCP+ FAQ](https://help.offsec.com/hc/en-us/articles/4412170923924-OSCP-Exam-FAQ) names both Rubeus and Mimikatz as allowed, subject to feature restrictions in the exam guide.

 | TGS-REP AES256 | 19700 |
| `$krb5asrep$17# Active Directory Attack Paths — OSCP Lab Decision Guide

> Purpose: Convert **observed** AD relationships into a defensible test plan in your authorized lab. This guide emphasizes preconditions, evidence, permitted tooling and troubleshooting. It is not a checklist of attacks to run blindly.

**Start here:** [AD Enumeration](./ad-enumeration.md) and [Password Auditing](../06-Passwords/password-auditing.md).

## How to reason about an AD path

For each candidate path, write:

~~~text
Current identity / host:
Target account / host:
Observed right or misconfiguration:
Why this right might permit the next action:
What authentication or network access is required:
Single test to validate the hypothesis:
Expected evidence:
Potential service interruption / account lockout risk:
Result / next step:
~~~

## 1. Provided credentials and legitimate remote access

On the supplied account, ask:
- Is this identity a local administrator on an in-scope member server?
- Does the account have permitted access to a share, RDP, WinRM or a database?
- Is the management port reachable from this machine or only from another network?
- Is there a simpler approved path using existing permissions?

For example, with a **known authorized** Windows account:

~~~powershell
Test-NetConnection server.example.lab -Port 5985
Test-NetConnection server.example.lab -Port 3389
~~~

Network reachability does not establish authorization. Use only the assigned credentials and approved hosts.

## 2. AS-REP roasting — precondition triage

**Enumeration first:** [AS-REP account checks](./ad-enumeration.md#43-as-rep-roasting--enumerate-preauthentication-disabled-accounts) includes native PowerShell, LDAP and PowerView queries. Look for enabled accounts with DONT_REQ_PREAUTH (4194304). No SPN is required. The AS-REP encrypted response portion, not the KRBTGT-encrypted TGT, is the relevant password-auditing material. The flag establishes exposure, not password recovery.

**What must be true:** An in-scope account has Kerberos preauthentication disabled, and the environment permits a request for that account. Determine whether the account and policy are actually relevant first. Requests for ticket material and any offline cracking must stay within the lab authorization. Do not run this across real user directories.

**Investigate:** Which specific object has the flag? Is it a service/normal user? Is it within scope? Would exploiting that identity contribute to the next objective?

## 3. Kerberoasting — precondition triage

**Enumeration first:** [SPN-bearing account checks](./ad-enumeration.md#44-kerberoasting--enumerate-spn-bearing-accounts) identifies account ownership, enabled status and password age. Rubeus `kerberoast /stats` enumerates statistics without requesting roasting tickets. Both AES and RC4 may be relevant; a service ticket does not demonstrate a weak password.

**What must be true:** A service account has an SPN and you possess an authorized domain identity capable of requesting relevant service tickets. A returned ticket is not a guaranteed weak password. Avoid large indiscriminate ticket requests or credential attacks without scope.

~~~cmd
setspn -T example.lab -Q */*
~~~

Document the account, service, ticket type and whether any legitimate path exists independent of password recovery. If practicing offline auditing, see [Password Auditing](../06-Passwords/password-auditing.md).

## 3A. Kerberos ticket and delegation decision guide

Start with [current ticket inspection](./ad-enumeration.md#42-check-kerberos-connectivity-and-your-current-tickets) and [Rubeus/Mimikatz inspection](./ad-enumeration.md#45-rubeus-and-mimikatz--ticket-inspection). These commands are for checking your authorized session and directory exposure.

| Technique | Necessary condition / evidence | What not to assume |
| --- | --- | --- |
| AS-REP roasting | Enabled identity with preauthentication disabled | The account password is weak |
| Kerberoasting | Relevant SPN-bearing identity and a permissible service-ticket request | An SPN proves credential recovery |
| Pass-the-Ticket | Valid ticket and applicable session/realm/service scope | A ticket automatically grants admin access |
| Pass-the-Hash | Relevant NTLM credential and service accepting that authentication | This is the same as Kerberos ticket authentication |
| Unconstrained delegation | Relevant trusted service/computer and applicable Kerberos context | Every trusted computer is an immediate path |
| Constrained delegation | A relevant service and configured delegation target SPN; applicable protocol transition settings | Delegation to arbitrary services is permitted |
| Resource-based constrained delegation | Resource's delegation security descriptor and relevant effective principal rights | The presence of a descriptor alone establishes exploitability |
| Golden Ticket | Compromise of the domain KRBTGT key | A normal user's TGT provides the KRBTGT key |
| Silver Ticket | Compromise of the relevant service identity key | A service ticket provides its service account's key |
| DCSync | Effective directory replication rights over the relevant domain naming context | Any domain account can replicate credentials |

Golden/Silver Ticket and DCSync are higher-impact post-compromise topics, not first-line enumeration tasks. Distinguish authentication from authorization at every step. A valid ticket does not prove the current identity can access a particular administrative service.

**Tool choice:** Windows klist is the fastest first check. Rubeus is useful for Kerberos-specific metadata and SPN statistics. Mimikatz offers Kerberos inspection in addition to other sensitive capabilities; listing your own session's tickets does not require credential dumping, ticket export, or injection. The [official OSCP+ FAQ](https://help.offsec.com/hc/en-us/articles/4412170923924-OSCP-Exam-FAQ) names both Rubeus and Mimikatz as allowed, subject to feature restrictions in the exam guide.

 | AS-REP AES128 | 32100 |
| `$krb5asrep$18# Active Directory Attack Paths — OSCP Lab Decision Guide

> Purpose: Convert **observed** AD relationships into a defensible test plan in your authorized lab. This guide emphasizes preconditions, evidence, permitted tooling and troubleshooting. It is not a checklist of attacks to run blindly.

**Start here:** [AD Enumeration](./ad-enumeration.md) and [Password Auditing](../06-Passwords/password-auditing.md).

## How to reason about an AD path

For each candidate path, write:

~~~text
Current identity / host:
Target account / host:
Observed right or misconfiguration:
Why this right might permit the next action:
What authentication or network access is required:
Single test to validate the hypothesis:
Expected evidence:
Potential service interruption / account lockout risk:
Result / next step:
~~~

## 1. Provided credentials and legitimate remote access

On the supplied account, ask:
- Is this identity a local administrator on an in-scope member server?
- Does the account have permitted access to a share, RDP, WinRM or a database?
- Is the management port reachable from this machine or only from another network?
- Is there a simpler approved path using existing permissions?

For example, with a **known authorized** Windows account:

~~~powershell
Test-NetConnection server.example.lab -Port 5985
Test-NetConnection server.example.lab -Port 3389
~~~

Network reachability does not establish authorization. Use only the assigned credentials and approved hosts.

## 2. AS-REP roasting — precondition triage

**Enumeration first:** [AS-REP account checks](./ad-enumeration.md#43-as-rep-roasting--enumerate-preauthentication-disabled-accounts) includes native PowerShell, LDAP and PowerView queries. Look for enabled accounts with DONT_REQ_PREAUTH (4194304). No SPN is required. The AS-REP encrypted response portion, not the KRBTGT-encrypted TGT, is the relevant password-auditing material. The flag establishes exposure, not password recovery.

**What must be true:** An in-scope account has Kerberos preauthentication disabled, and the environment permits a request for that account. Determine whether the account and policy are actually relevant first. Requests for ticket material and any offline cracking must stay within the lab authorization. Do not run this across real user directories.

**Investigate:** Which specific object has the flag? Is it a service/normal user? Is it within scope? Would exploiting that identity contribute to the next objective?

## 3. Kerberoasting — precondition triage

**Enumeration first:** [SPN-bearing account checks](./ad-enumeration.md#44-kerberoasting--enumerate-spn-bearing-accounts) identifies account ownership, enabled status and password age. Rubeus `kerberoast /stats` enumerates statistics without requesting roasting tickets. Both AES and RC4 may be relevant; a service ticket does not demonstrate a weak password.

**What must be true:** A service account has an SPN and you possess an authorized domain identity capable of requesting relevant service tickets. A returned ticket is not a guaranteed weak password. Avoid large indiscriminate ticket requests or credential attacks without scope.

~~~cmd
setspn -T example.lab -Q */*
~~~

Document the account, service, ticket type and whether any legitimate path exists independent of password recovery. If practicing offline auditing, see [Password Auditing](../06-Passwords/password-auditing.md).

## 3A. Kerberos ticket and delegation decision guide

Start with [current ticket inspection](./ad-enumeration.md#42-check-kerberos-connectivity-and-your-current-tickets) and [Rubeus/Mimikatz inspection](./ad-enumeration.md#45-rubeus-and-mimikatz--ticket-inspection). These commands are for checking your authorized session and directory exposure.

| Technique | Necessary condition / evidence | What not to assume |
| --- | --- | --- |
| AS-REP roasting | Enabled identity with preauthentication disabled | The account password is weak |
| Kerberoasting | Relevant SPN-bearing identity and a permissible service-ticket request | An SPN proves credential recovery |
| Pass-the-Ticket | Valid ticket and applicable session/realm/service scope | A ticket automatically grants admin access |
| Pass-the-Hash | Relevant NTLM credential and service accepting that authentication | This is the same as Kerberos ticket authentication |
| Unconstrained delegation | Relevant trusted service/computer and applicable Kerberos context | Every trusted computer is an immediate path |
| Constrained delegation | A relevant service and configured delegation target SPN; applicable protocol transition settings | Delegation to arbitrary services is permitted |
| Resource-based constrained delegation | Resource's delegation security descriptor and relevant effective principal rights | The presence of a descriptor alone establishes exploitability |
| Golden Ticket | Compromise of the domain KRBTGT key | A normal user's TGT provides the KRBTGT key |
| Silver Ticket | Compromise of the relevant service identity key | A service ticket provides its service account's key |
| DCSync | Effective directory replication rights over the relevant domain naming context | Any domain account can replicate credentials |

Golden/Silver Ticket and DCSync are higher-impact post-compromise topics, not first-line enumeration tasks. Distinguish authentication from authorization at every step. A valid ticket does not prove the current identity can access a particular administrative service.

**Tool choice:** Windows klist is the fastest first check. Rubeus is useful for Kerberos-specific metadata and SPN statistics. Mimikatz offers Kerberos inspection in addition to other sensitive capabilities; listing your own session's tickets does not require credential dumping, ticket export, or injection. The [official OSCP+ FAQ](https://help.offsec.com/hc/en-us/articles/4412170923924-OSCP-Exam-FAQ) names both Rubeus and Mimikatz as allowed, subject to feature restrictions in the exam guide.

 | AS-REP AES256 | 32200 |

Modes 19800/19900 are AES **preauthentication** formats, not AES AS-REP roasting modes. Check the [official Hashcat examples](https://hashcat.net/wiki/doku.php?id=example_hashes) and your installed version before selecting a mode. Keep each format in its own file, one complete hash per line, with no terminal wrapping, labels or extraneous whitespace.

### Prepare and test locally on Kali

~~~bash
umask 077
mkdir -p "$HOME/oscp-local/ad-password-audit"
cd "$HOME/oscp-local/ad-password-audit"
hashcat --version
hashcat -I
ls -l /usr/share/wordlists/rockyou.txt*
~~~

Use a local wordlist prepared before the exam. If only rockyou.txt.gz exists, decompress a private copy with `gzip -dc /usr/share/wordlists/rockyou.txt.gz > rockyou.txt` and set WORDLIST to that file. Do not assume every Kali installation includes the wordlist or a usable GPU driver.

~~~bash
WORDLIST=/usr/share/wordlists/rockyou.txt
test -r "$WORDLIST" || echo "Set WORDLIST to your actual readable wordlist"

# RC4 AS-REP hash file supplied by the authorized lab
hashcat -m 18200 -a 0 asrep.txt "$WORDLIST" --session=lab-asrep

# RC4 service-ticket hash file supplied by the authorized lab
hashcat -m 13100 -a 0 tgs.txt "$WORDLIST" --session=lab-tgs
~~~

For AES hashes, choose the matching mode from the table instead of reusing an RC4 mode. Use distinct input files and session names when changing hash type. To practice safely before working with lab data, copy an official Hashcat example hash into a test file and use a small test wordlist containing the published sample password (usually `hashcat`). This checks that the installed mode and device actually work.

### Inspect results and resume

~~~bash
hashcat -m 18200 asrep.txt --show
hashcat -m 13100 tgs.txt --show

# Resume a previously interrupted session, if a restore file exists
hashcat --session=lab-asrep --restore
~~~

John the Ripper Jumbo is another offline alternative; run `john --list=formats` to confirm the appropriate Kerberos format is supported by your installed build. For RC4 practice-lab examples, `krb5asrep` and `krb5tgs` are common format names:

~~~bash
john --format=krb5asrep --wordlist="$WORDLIST" asrep.txt
john --format=krb5tgs --wordlist="$WORDLIST" tgs.txt
~~~

Do not use `--force` as a default to suppress Hashcat driver or self-test problems. A recovered password does not grant administrator access by itself; evaluate the account's actual authorized group memberships and service rights. Offline auditing does not generate online account lockouts, but subsequent authentication attempts can. Never publish hashes, recovered passwords, potfiles, restore files, or ticket blobs. The official exam guide restricts downloading target files unless necessary for compromise; delete any permitted local copies after completing exam objectives. Keep reports and permitted evidence separate and private.

| Result | Next action |
| --- | --- |
| Cracked | Record the affected authorized account privately; verify its permissions |
| Exhausted | Only the tested candidate set was exhausted; return to other enumeration paths |
| Token length / separator error | Check hash mode, complete line and exporter format |
| No usable compute device | Check backend/driver or use a supported CPU auditing tool |
| No hashes loaded | Check file contents and installed mode support |
| No valid Kerberos ticket / clock skew | Return to DNS, time, realm and session checks; cracking does not fix authentication setup |

**Time management:** run a bounded dictionary test, then keep enumerating while it runs locally if resources permit. A strong service-account password or managed account may not be recoverable in the available time. Do not make successful cracking a prerequisite for the rest of the AD workflow.

See [Password Auditing](../06-Passwords/password-auditing.md) for general offline auditing and [AD Enumeration](./ad-enumeration.md) for preauthentication, SPN and ticket checks.

## 4. Object and ACL-based paths

Investigate relationships such as:
- A lower-privileged identity can modify **membership** of a specific group.
- It can reset the password of a specifically delegated test account.
- It owns or can modify a directory object used by a service.
- It has a delegated computer or service-account management right.

The decisive factor is the **effective ACL** on that object, not merely an interesting group name. Validate the right read-only first and identify the minimum safe change allowed by the lab. Record original values so any permitted modification can be reversed.

## 5. Lateral movement after authorized access

Use the permissions learned from AD enumeration. A host-to-host action is justified only when you know the identity, target, allowed protocol and network path. Remote admin interfaces, file shares and web management endpoints have different authorization requirements.

~~~powershell
whoami /all
Test-NetConnection server.example.lab -Port 445
Test-NetConnection server.example.lab -Port 5985
~~~

After moving to another authorized host, repeat local enumeration; domain group membership alone does **not** guarantee local administrative rights.

## 6. Delegation and certificate services — when present

Note evidence of Kerberos delegation configurations, service accounts, certificate templates, enrollment web services and AD CS roles **only if they exist in your lab**. These are contextual, not universal OSCP objectives. Avoid automated mass template modification or destructive certificate operations.

## 7. Decision table

| Evidence | Question before taking action |
| --- | --- |
| User holds credentials | Where does the assigned identity actually have access? |
| SPN on service account | Is the service identity relevant and auditing authorized? |
| Preauth disabled | Is the affected account in scope and worth evaluating? |
| Editable group/object ACL | Can a specific permitted change lead to a new right? |
| Local admin on another host | Can you reach that host and demonstrate authorized login? |
| Reachable management port | Do credentials authorize that interface? |
| AD CS installed | Is a relevant enrollment misconfiguration confirmed? |

## 8. Avoid common OSCP mistakes

- Do not spray passwords across the domain to find a working account.
- Do not equate a graph edge or scanner hit with proof of exploitation.
- Do not assume a user is admin on every computer because of a group name.
- Do not ignore DNS, time synchronization, SPNs and protocol requirements.
- Do not run exploitation tools with prohibited automation or Metasploit modules on multiple targets; review [OffSec restrictions](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide).

## Evidence checklist

- [ ] Current account and host.
- [ ] Exact observed ACL, SPN, group or delegated right.
- [ ] Affected object/host and associated business function.
- [ ] Validation method and command transcript.
- [ ] Resulting identity and effective privilege.
- [ ] Sanitized screenshot and rollback note where applicable.

## References

- [Hashcat official example hashes and modes](https://hashcat.net/wiki/doku.php?id=example_hashes)
- [John the Ripper documentation](https://www.openwall.com/john/doc/)

- [Microsoft Active Directory security](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/plan/security-best-practices/)
- [OffSec OSCP+ Exam FAQ](https://help.offsec.com/hc/en-us/articles/4412170923924-OSCP-Exam-FAQ)
- [Microsoft Kerberos](https://learn.microsoft.com/en-us/windows-server/security/kerberos/kerberos-authentication-overview)
- [OffSec OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide)
