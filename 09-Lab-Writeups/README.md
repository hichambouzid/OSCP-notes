# Practice Lab Writeup Template — OSCP Learning Journal

> This folder is for **sanitized, authorized training labs** and made-up examples. **Do not publish live exam targets, proofs, private keys, credentials, screenshots or exam-specific information.** If you use this template, copy it to a **private local workspace**.

## How to learn from each box

1. Record the assigned scope and what you knew at the start.
2. Keep a short timeline of enumeration, hypotheses, tests and decisive evidence.
3. Separate confirmed findings from guesses and false positives.
4. Explain why the technique worked and what its prerequisites were.
5. Write a corrective action a defender could take.
6. End with one reusable lesson and one improvement to your notes.

## Blank writeup (copy into private notes)

~~~markdown
# Lab: NAME (authorized practice only)

## Context
- Platform / lab:
- Authorized target(s):
- Date:
- Initial network route:
- Starting credentials or constraints:

## Enumeration
- TCP ports and services:
- UDP observations:
- Web paths, hostnames, parameters:
- Accounts, shares, domain clues:
- Raw evidence file locations:

## Hypotheses
| Finding | Possible weakness | How to verify | Outcome |
| --- | --- | --- | --- |
| ... | ... | ... | untested / rejected / confirmed |

## Initial access
- Confirmed vulnerability or permitted credential:
- Preconditions:
- Exact manual steps and commands:
- Resulting shell/user:
- Evidence/screenshot references:

## Privilege escalation
- Starting user and OS:
- Manual enumeration findings:
- Verified misconfiguration:
- Steps taken:
- Final identity:
- Evidence/screenshot references:

## Lessons
- What was decisive?
- Which test was a false positive?
- What would I do sooner next time?
- Remediation:
- References:
~~~

## Suggested practice log

| Date | Lab | Area practiced | Main mistake | What improved |
| --- | --- | --- | --- | --- |
| YYYY-MM-DD | Sanitized name | Web / Linux / Windows / AD | Example | Example |

## Evidence quality tips

- Save **raw command output** in private files so that you can distinguish evidence from memory.
- Label screenshots with target, stage and time; capture a short annotation in notes.
- Avoid unnecessary personally identifying or sensitive information.
- A web banner or CVE result is not confirmation of exploitation.
- Do not accidentally commit .ovpn files, credentials, tokens, password hashes, remote shell transcripts or exam proofs to public GitHub.

## Reusable links

- [Quick Reference](../00-Quick-Reference/quick-reference.md)
- [Initial Access](../03-Initial-Access/initial-access.md)
- [Linux Privilege Escalation](../04-Privilege-Escalation/linux-privesc.md)
- [Windows Privilege Escalation](../04-Privilege-Escalation/windows-privesc.md)
- [AD Enumeration](../05-Active-Directory/ad-enumeration.md)
- [Exam Methodology](../08-Exam-Workflow/exam-methodology.md)
- [Reporting](../08-Exam-Workflow/reporting.md)
