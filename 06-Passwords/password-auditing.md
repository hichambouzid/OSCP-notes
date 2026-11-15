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


## 4A. Offline exam-practice recipe — select format, prepare files, test, resume

**Where:** Kali, in a private directory. The following is for your own synthetic test hashes or expressly authorized lab-provided hashes. A normal ticket cache or arbitrary binary ticket is not a Hashcat input file.

~~~bash
umask 077
mkdir -p "$HOME/oscp-local/password-audit"
cd "$HOME/oscp-local/password-audit"
command -v hashcat
command -v john
hashcat --version
hashcat -I
ls -l /usr/share/wordlists/rockyou.txt*
~~~

If rockyou is compressed, prepare a local copy before the exam; do not decompress over an existing customized list.

~~~bash
WORDLIST=/usr/share/wordlists/rockyou.txt
if [ ! -r "$WORDLIST" ] && [ -r /usr/share/wordlists/rockyou.txt.gz ]; then
  gzip -dc /usr/share/wordlists/rockyou.txt.gz > rockyou.txt
  WORDLIST="$PWD/rockyou.txt"
fi
test -r "$WORDLIST" && wc -l "$WORDLIST"
~~~

### Select the mode from the source, not the length

| Format / evidence | Hashcat mode | John Jumbo format clue |
| --- | --- | --- |
| Raw MD5 (confirmed) | 0 | raw-md5 |
| Raw SHA-1 (confirmed) | 100 | raw-sha1 |
| Raw SHA-256 (confirmed) | 1400 | raw-sha256 |
| NTLM | 1000 | NT |
| NetNTLMv1 challenge-response | 5500 | netntlm |
| NetNTLMv2 challenge-response | 5600 | netntlmv2 |
| bcrypt ($2a$, $2b$, $2y$) | 3200 | bcrypt |
| Unix sha512crypt ($6$) | 1800 | sha512crypt |
| Kerberos AS-REP RC4 (etype 23) | 18200 | krb5asrep |
| Kerberos TGS RC4 (etype 23) | 13100 | krb5tgs |
| Kerberos TGS AES128 (etype 17) | 19600 | Check installed formats |
| Kerberos TGS AES256 (etype 18) | 19700 | Check installed formats |
| Kerberos AS-REP AES128 (etype 17) | 32100 | Check installed formats |
| Kerberos AS-REP AES256 (etype 18) | 32200 | Check installed formats |

Check the [Hashcat example hashes](https://hashcat.net/wiki/doku.php?id=example_hashes) and installed version; modes are specific to the exported structure. A 32-character hexadecimal string might be MD5, NTLM or another algorithm. NetNTLM challenge-response values are not NTLM password hashes. Keep mixed formats in separate files.

### Test your installation without any target data

Generate a known, disposable MD5 sample and candidate list. This exercises the whole offline workflow before touching authorized lab data.

~~~bash
printf '%s' 'hashcat' | md5sum | cut -d ' ' -f1 > demo-md5.txt
printf '%s\n' 'incorrect' 'hashcat' > demo-words.txt
hashcat -m 0 -a 0 demo-md5.txt demo-words.txt --potfile-path "$PWD/demo.potfile"
hashcat -m 0 demo-md5.txt --show --potfile-path "$PWD/demo.potfile"
~~~

Expected: the candidate hashcat matches the test digest. If the device or self-test fails, troubleshoot the local installation instead of forcing past the error. For a Kerberos-mode smoke test, copy the complete public example for the chosen mode from the official Hashcat table into a local demo file; use its documented example password as a candidate. Do not use real ticket material for the installation test.

### Authorized lab hash workflow

1. Confirm the exact format and account or service association. Keep one complete exported hash per line in a private file.
2. Check that the installed tool supports the mode: `hashcat -m 18200 --example-hashes` and `john --list=formats`.
3. Run a bounded dictionary test; choose the matching mode and a distinct session name for each dataset.
4. Inspect results and record which authorized identity was matched. An exhausted dictionary does not establish that the password is strong.
5. If needed, pause or resume offline work while continuing unrelated enumeration. Do not let a long-running audit consume the entire exam.

See [AD ticket and hash workflow](../05-Active-Directory/ad-attack-paths.md#3b-offline-password-auditing--as-rep-and-tgs-hashes) for the six Kerberos modes, RC4 examples, John alternatives, and ticket-specific troubleshooting.

### Common errors that cost time

| Error / symptom | Decision |
| --- | --- |
| Separator unmatched / token length | Wrong format, incomplete line or extra username label; compare to exact example format |
| No password found / Exhausted | Candidate set finished, not a parser error; move on to other leads |
| Hash already in potfile | Use the same mode and potfile with --show; do not restart needlessly |
| Restore file not found | Verify session name, working directory, and whether a restore file was created |
| Device unavailable / self-test failed | Fix runtime or try an appropriate supported CPU tool; do not use --force blindly |
| John auto-detects the wrong format | Use the verified explicit --format value |
| Password contains spaces or punctuation | Preserve literal characters; do not paste secrets into shell history or public notes |

**Exam boundary:** a locally recovered candidate is not a privilege result. Confirm actual access only through the relevant authorized service and its allowed credentials. Never commit target hashes, tickets, candidate passwords, potfiles or reports. Follow the OffSec file-transfer restriction for any target files needed for compromise.

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
