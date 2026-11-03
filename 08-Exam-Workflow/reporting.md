# OSCP+ Reporting — Reproducible Evidence Guide

> The report is part of the exam objective, not optional paperwork. This public repository contains a **template only**; keep actual exam notes, proof values, target IPs, credentials and screenshots off public GitHub. Follow the current [OffSec OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide).

## Report quality requirements

A competent technical reader should be able to reproduce the path from the initial network evidence to the attained privileges **in the stated lab environment**. Show exact versions/ports, commands, minimal meaningful outputs, prerequisites, and screenshots.

## 1. Suggested report structure

~~~text
Title and exam candidate details (private submission only)
Executive summary
Scope and methodology
Target-by-target technical findings
  Target #1 — address, services, initial access, privilege escalation
  Target #2 — ...
  Active Directory set — host order, identities, relationships, movement
Risk and remediation summaries
Appendix: references, code modifications, relevant commands
~~~

The exam guide points to official Microsoft Word/LibreOffice report templates. You may use another professional structured format if it satisfies all requirements.

## 2. Target worksheet

Copy this template **locally**, not into your public repo:

~~~markdown
### Target: HOSTNAME / IP (PRIVATE)

**Assigned objective:**
**Starting context:**
**OS and exposed services:**
**Discovered technology/version:**
**Finding and preconditions:**
**Evidence from enumeration:**

#### Initial access
- Entry point:
- Validation:
- Exact command or manual request:
- Relevant output:
- Target user:
- Screenshot file:

#### Privilege escalation
- Starting privilege:
- Misconfiguration or CVE:
- Preconditions verified:
- Step-by-step commands:
- Relevant output:
- Final effective privilege:
- Screenshot file:

#### Proof
- Proof filename and original path:
- Interactive-shell cat/type screenshot:
- Target IP displayed in same screenshot:
- Control panel submitted: yes/no
- Timestamp:

#### Remediation and references
- Root cause:
- Recommended fix:
- Vendor or CVE reference:
~~~

## 3. Screenshots and proof rules

**Exam requirement:** Display the actual contents of local.txt or proof.txt **from the original file location** in an **interactive shell on the target** using cat (Linux) or type (Windows), with the **target IP address visible** via ip addr, ifconfig or ipconfig in the screenshot. A web shell screenshot is not sufficient. Submit proof values to the control panel before the exam ends.

Examples illustrating the *command types*:

~~~bash
ip addr
# In your authorized interactive Linux exam shell, display the assigned original proof file with cat.
~~~

~~~cmd
ipconfig
REM In your authorized interactive Windows exam shell, display the assigned original proof file with type.
~~~

Avoid storing actual proof values or screenshots publicly.

## 4. Exploit code documentation

When you use an unmodified public exploit, the guide says to cite the original URL rather than reproduce several pages of code. If you modify an exploit, document:
- Original URL and affected software/version.
- Exact modifications and rationale.
- Relevant modified code.
- Shellcode-generation command where applicable.
- Evidence of result and reproducibility.

Do not claim an exploit succeeded solely because a scanner reported a CVE.

## 5. Keep evidence organized

Suggested **local/private** directory structure:

~~~text
report/
  screenshots/
    target-01-initial.png
    target-01-privilege.png
    ad-01.png
  notes/
    target-01-commands.txt
    target-01-versions.txt
  final/
    OSCP-OS-XXXXX-Exam-Report.pdf
~~~

Do not save passwords in command-line histories unnecessarily. Sanitize demonstration data before sharing outside the permitted exam submission.

## 6. Export and submission checklist

OffSec currently specifies:
- PDF report with the case-sensitive filename format **OSCP-OS-XXXXX-Exam-Report.pdf**.
- Unencrypted **.7z** archive named **OSCP-OS-XXXXX-Exam-Report.7z**.
- Maximum archive size **200MB**.
- Upload to https://upload.offsec.com within the stated 24-hour reporting window.
- Verify the site-displayed MD5 matches your local archive checksum.
- Complete the final **Submit File** action.

~~~bash
7z a OSCP-OS-XXXXX-Exam-Report.7z OSCP-OS-XXXXX-Exam-Report.pdf
md5sum OSCP-OS-XXXXX-Exam-Report.7z
~~~

Replace the placeholder with your **own actual OSID** in the private submission, never the public repository. Check the complete guide for updates before exam day.

## 7. Common avoidable failures

| Failure | Prevention |
| --- | --- |
| Missing screenshot | Capture it immediately after each successful foothold/objective |
| Missing original proof path | Document which host/path produced the proof |
| Web shell used for proof capture | Use interactive shell and cat/type |
| Screenshot lacks target IP | Show ip addr/ifconfig/ipconfig on target |
| Command cannot be reproduced | Include assumptions, arguments and outputs |
| Exploit changed without explanation | Include original URL and exact diff/rationale |
| Report exceeds archive limit | Compress images and inspect PDF before packaging |
| Upload left unfinished | Check MD5 and final submission confirmation |

## 8. Final verification

- [ ] Every target's service map, initial access and privilege path documented.
- [ ] Every proof screenshot meets interactive shell and IP requirements.
- [ ] All required proof values submitted to control panel.
- [ ] Code modifications and references recorded.
- [ ] PDF legible and internally consistent.
- [ ] Only PDF included in 7z; archive unencrypted and under size limit.
- [ ] Correct filename and upload verified.

## References

- [OffSec OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide)
- [OffSec AI Usage Policy](https://help.offsec.com/hc/en-us/articles/35549468971156-AI-Usage-Policy-in-OffSec-Exams)
