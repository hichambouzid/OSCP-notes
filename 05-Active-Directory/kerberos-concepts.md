# Kerberos and Active Directory — beginner concept cards

For authorized learning before the exam. This guide explains what tickets, hashes and permissions represent, how to read common errors, and how to inspect your own session. It is not a ticket-extraction, credential-cracking or impersonation recipe.

## 1. Vocabulary

| Term | Meaning |
| --- | --- |
| AD DS | Directory storing domain objects, authentication and policy. |
| DC | Domain controller; provides directory and authentication services. |
| KDC | Key Distribution Center: authentication service (AS) and ticket-granting service (TGS). |
| Realm | Kerberos administrative namespace; often the uppercase DNS domain. |
| Principal | Identity of a user, computer or service. |
| SPN | Service principal name: identifies a service instance and its associated account. |
| TGT | Ticket-granting ticket used to request service tickets. |
| Service ticket | Ticket for a particular service; not proof of administrative rights. |
| Session key | Key used within the relevant authenticated session. |
| Preauthentication | Proof of possession of a long-term key before the KDC issues certain responses. |
| NTLM | A different Windows authentication mechanism; not a Kerberos ticket. |
| ACL / ACE | Access-control list and its individual entries. |
| SID | Security identifier; unique identity used in access checks. |
| Delegation | Policy allowing a service to act on behalf of a user within defined conditions. |

## 2. Normal authentication in plain language

1. A client authenticates to the KDC and obtains a TGT.
2. The client presents the TGT to request a service ticket for a specific SPN.
3. The client presents that service ticket to the service.
4. The service evaluates identity and authorization. A ticket alone does not guarantee access.

DNS, time synchronization, identity, realm and the requested service name all matter. A ticket can expire and must be renewed or replaced through ordinary authentication as applicable. An SPN is not an IP address or a password.

## 3. Terms you will encounter in security training

| Term | Concept | Defensive significance |
| --- | --- | --- |
| AS-REP roasting | Certain responses for accounts lacking required preauthentication can expose encrypted material usable for password-guess verification. | Require preauthentication where appropriate; review exceptional accounts. |
| Kerberoasting | A service ticket includes encrypted material protected by the service account's key; weak service-account passwords create offline guessing risk. | Use managed service accounts or strong random secrets; monitor service-ticket activity. |
| Pass-the-hash | Reusing certain password-derived authentication material rather than the original password. | Limit privileged account exposure; reduce legacy authentication where appropriate. |
| Pass-the-ticket | Reusing a valid ticket rather than authenticating with the original password. | Protect ticket caches and endpoints; limit delegation and privileged sessions. |
| Golden ticket | Forged TGT associated with compromise of the domain's ticket-signing key. | Treat key compromise as a critical domain incident. |
| Silver ticket | Forged service ticket associated with compromise of a service-account key. | Rotate exposed service secrets and investigate affected services. |
| Delegation misconfiguration | Excessive or incorrectly assigned trust may allow unintended identity use. | Review delegation settings and account protections. |

These labels describe distinct mechanisms. Do not confuse an AS-REP with a TGS response, or an account that has an SPN with an account that necessarily uses a weak password.

## 4. What does “cracking a ticket” mean?

It usually means testing password candidates against password-derived encrypted material, not decrypting every ticket or converting it to plaintext automatically. Whether a candidate can be verified depends on the artifact type, encryption type, account key and correct format. RC4 and AES are different encryption families; guessing costs can differ. A strong secret may be impractical to guess.

Distinguish an actual ticket cache, encrypted response material, a password verifier, a Windows NT hash and an ordinary file checksum. They are not interchangeable.

For hands-on exercises, use your assigned PEN-200 course labs before exam day, with course-provided artifacts and instructions. Never use collected third-party credentials or upload private ticket material to online services. Do not include secrets or real ticket blobs in Git.

## 5. Inspect your own existing session

On Linux with MIT Kerberos installed:

```bash
klist
date -Is
timedatectl status
hostname
```

On Windows in your existing authorized session:

```powershell
whoami
whoami /all
klist
Get-Date
w32tm /query /status
```

Linux and Windows klist implementations differ. Inspect the principal, service, realm, lifetime and expiration; do not export or share tickets. A missing local cache does not prove a domain is unavailable.

## 6. Error vocabulary

| Error / symptom | What to investigate conceptually |
| --- | --- |
| Clock skew | Client and KDC time discrepancy; check clock and time source. |
| Cannot find KDC | DNS/realm configuration, VPN or name resolution. |
| Principal unknown | Name, realm, account or SPN mismatch. |
| Preauthentication failed | Incorrect or stale authentication information or policy; avoid repeated guessing. |
| Ticket expired | Validity period; use ordinary authorized authentication. |
| Encryption type not supported | Client, server and account cryptographic compatibility. |
| Access denied after authentication | Authorization, identity or policy rather than necessarily a bad password. |

## 7. Learn to reason without memorizing attack commands

Write down: who is authenticating, to what service, in which realm, what is proven, what permissions are known, and what remains uncertain. In a practice lab, use course-provided exercises to explain each of those facts before attempting the next exercise.

## 8. References

- [MIT Kerberos documentation](https://web.mit.edu/kerberos/krb5-latest/doc/)
- [Microsoft Kerberos authentication overview](https://learn.microsoft.com/en-us/windows-server/security/kerberos/kerberos-authentication-overview)
- [Beginner desk reference](../00-Quick-Reference/beginner-desk-reference.md)
