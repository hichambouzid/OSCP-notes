# Password and Hash Auditing — OSCP Lab Notes

> Scope: Authorized lab accounts, explicitly permitted test credentials and offline datasets only. This guide intentionally separates **offline password auditing** from online authentication testing to reduce accidental lockouts and avoid broad password-spraying behavior.

## 1. Identify what you actually have

Before trying a tool, record:

~~~text
Where did the value come from? (assigned lab / test file / service):
Username or service account (sanitize if published):
Likely format (NTLM, bcrypt, SHA-512 crypt, Kerberos ticket, etc.):
Evidence for the format:
Allowed use (offline audit / authorized sign-in / neither):
Wordlist and resource limits:
Outcome:
~~~

A hash is not the same as a cleartext password. Do not assume the hash type from its length alone, especially if salts or encodings are involved.

## 2. Inspect a sample file offline

~~~bash
file lab-hashes.txt
wc -l lab-hashes.txt
head -n 2 lab-hashes.txt
command -v hashid
hashid lab-hashes.txt
~~~

Only run this on a **sanitized or expressly authorized** file. Automated hash identification is suggestive, not definitive. Confirm the original software or password-storage format.

## 3. John the Ripper — controlled offline practice

~~~bash
john --help | head
john --list=formats | head
john --wordlist=/usr/share/wordlists/rockyou.txt lab-hashes.txt
john --show lab-hashes.txt
~~~

Kali's wordlists may ship compressed. Check the local path and tool instructions before running. Restrict inputs to approved datasets. Record the detected format and whether a candidate was verified.

## 4. Hashcat — choose the correct hash mode

~~~bash
hashcat --help
hashcat --example-hashes
hashcat -m 1000 -a 0 lab-ntlm.txt /usr/share/wordlists/rockyou.txt
hashcat -m 1000 --show lab-ntlm.txt
~~~

Mode **1000 is NTLM only**. Do not use it for arbitrary hashes. Hashcat may need suitable GPU/OpenCL drivers; errors can indicate a platform issue rather than incorrect credentials.

## 5. Online validation and lockout safety

If the lab explicitly provides a test identity, a single manual login to the specified service can confirm whether a credential works. Before any repeated attempts, inspect account lockout policy, rate limiting and scope. Avoid password spraying, guessing real accounts, or trying recovered credentials on unrelated hosts. An offline match does not automatically grant access to the relevant service.

On an authorized Windows domain member:

~~~cmd
net accounts /domain
~~~

This can provide a clue about password policy and lockout thresholds; effective per-user policies may differ.

## 6. Important distinctions

| Term | Meaning | Typical lab next step |
| --- | --- | --- |
| Cleartext credential | Actual password available | Verify with one approved login |
| Password hash | Stored one-way verifier | Identify algorithm and audit offline if authorized |
| Salted hash | Hash with per-user salt | Ensure tool input contains the required salt |
| Kerberos service ticket | Ticket material, not a password | Confirm identity/SPN and auditing scope |
| NTLM hash | Windows password-derived verifier | Treat as sensitive; never publish |
| Password reuse | One password works elsewhere | Test only hosts/accounts within assigned scope |

## 7. Troubleshooting

| Issue | Check |
| --- | --- |
| No candidates recovered | Format, wordlist coverage, correct input encoding |
| Hashcat: token length exception | Hash mode and salt/line syntax |
| John: no hashes loaded | Input format and `--format` selection |
| GPU unavailable | Driver/OpenCL installation and CPU alternatives |
| Valid password rejected online | Account state, domain syntax, service scope, lockout, MFA |
| Unexpected lockout | Stop testing, record attempts and follow lab reset procedure |

## OSCP exam tool policy

The [OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide) does **not individually certify John or Hashcat by name**; their **offline auditing** functionality is different from prohibited automatic exploitation. Validate the exact feature you use against the current guide. SQLmap/SQLninja and other automatic exploitation are prohibited; Metasploit/Meterpreter are restricted. AI chatbots cannot be used during the exam.

## Checklist

- [ ] Dataset or credential is lab-authorized.
- [ ] Hash type verified; correct mode/format chosen.
- [ ] Wordlist use and limits recorded.
- [ ] Offline results stored securely, never in public Git.
- [ ] Any online login is individually authorized and lockout-aware.
- [ ] Evidence retained without disclosing real secrets.

## References

- [John the Ripper](https://www.openwall.com/john/)
- [Hashcat wiki](https://hashcat.net/wiki/)
- [OffSec OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide)
