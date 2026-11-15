# OSCP+ Exam Workflow — Practical Checklist

> Prepared for study and practice. **Do not use an AI chatbot during the actual OSCP+ exam.** Recheck the [official exam guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide) immediately before exam day; its rules supersede this repository.

## 1. Current exam structure (guide updated October 21, 2026)

| Component | Raw points |
| --- | ---: |
| Three standalone machines | 60 total (20 each: 10 initial access + 10 privilege escalation) |
| One Active Directory set of three machines | 40 total (10 / 10 / 20) |
| Maximum raw points | 100 |

The official guide describes **23 hours 45 minutes** of exam time and an additional **24 hours** to submit documentation. The guide notes **scaled scoring starts for exams beginning on/after December 1, 2026 at 08:00 GMT**; consult the linked scaled-scoring FAQ for rules applicable to your actual date. Do not assume a single historical passing threshold will remain current.

## 2. Before exam day

- [ ] Read the latest exam guide, tool restrictions and proctor instructions.
- [ ] Test Kali VM, keyboard layout, screenshots, terminal logging, PDF export and 7-Zip.
- [ ] Check your Internet backup, power and VM disk space.
- [ ] Prepare a report template and a clean local (non-public) evidence directory.
- [ ] Practice confirming Kali VPN IP, network routes and host reachability.
- [ ] Know where your notes and offline manuals are. Do **not** use LLM/chatbot assistance during the exam.


### Pre-exam rehearsal — verify the cheat sheet before relying on it

Do this in your own practice environment, **before** the exam. The repository is a command reference, not proof that the commands work on your particular Kali build.

~~~bash
umask 077
mkdir -p "$HOME/oscp-local"/{scans,notes,evidence,reports,transfer}
for tool in nmap curl wget python3 ssh scp smbclient dig ffuf gobuster hashcat john; do
  command -v "$tool" || printf 'MISSING: %s\n' "$tool"
done
ls -l /usr/share/wordlists/rockyou.txt* /usr/share/wordlists/dirb/common.txt
ls -l /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt
~~~

Install and test missing utilities from trusted sources before the exam. Check installed command versions, wordlist paths, architecture and tool-specific help. Also prepare any approved Windows enumeration utilities, a compatible remote desktop client, and matching pivot binaries when needed. Review the current official restrictions; a tool name is not approval of every feature.

Practice the following workflows using your own authorized lab, with a fresh terminal each time:

| Rehearsal | Success condition |
| --- | --- |
| Port discovery | Full TCP range completed; discovered-port extraction returns correct list; UDP coverage recorded |
| HTTP transfer | Kali serves a harmless test file; Linux and Windows clients download it and checksums match |
| Credentialed access | Assigned test account signs in through the correct service; identity verified |
| Windows ACL and PuTTY | Locate a test session and interpret configuration versus an actual privileged consumer |
| Linux escalation enumeration | Identify test sudo, file capability or scheduled-task configuration and its actual execution context |
| Offline password audit | Public synthetic Hashcat example recovers the expected sample password; mode errors understood |
| AD enumeration | Find assigned domain/DC, verify DNS and time, inspect authorized account and SPNs |
| Pivot | Reach one known lab service through SSH or a prepared tunnel; verify route and clean up |
| Evidence and report | Produce a local sample PDF and unencrypted 7z; confirm screenshots and readable reproduction steps |

See [File Transfer](../03-Initial-Access/file-transfer.md), [Password Auditing](../06-Passwords/password-auditing.md), and [Pivoting](../07-Pivoting/pivoting-tunneling.md) for the relevant command sheets.

Keep a local copy of these static notes available before the exam. Do not store exam machine data in the public checkout, seek assistance from others, or prompt AI/chatbots during the exam or report phase. Refer to [OffSec AI policy](https://help.offsec.com/hc/en-us/articles/35549468971156-AI-Usage-Policy-in-OffSec-Exams).

## 3. Initial connectivity and logging

~~~bash
mkdir -p oscp-local/{scans,notes,evidence,reports}
ip -br addr
ip route
date -u
~~~

For local lab practice, optional terminal session logging:

~~~bash
script -q -f oscp-local/notes/terminal-session.log
~~~

Exit the script session when finished. Logs may contain credentials or target-specific data: store them securely **outside your public Git repository**.

## 4. Repeatable methodology per target

1. Confirm scope, IP, VPN route and known credentials.
2. Complete a **full TCP 1–65535 scan of every assigned target**, including each AD machine. The documented `-T4 --min-rate 300 --max-retries 1 --max-scan-delay 100ms` profile prioritizes speed and **may miss ports**. If empty/inconsistent, recheck with an accuracy-focused full-TCP scan (without those constraints) and combine confirmed open ports.
3. Extract **all** open TCP ports for `-sC -sV` detection. Run a UDP initial pass, then explicitly decide whether to expand targeted ports, top 1,000 or full UDP; **top 100 does not complete UDP enumeration**. Enumerate the actual services, not assumed standard ports.
4. For web applications, investigate hosts, paths, parameters, auth and user roles.
5. Research a candidate CVE only when the service/version/preconditions match.
6. Choose a single verified entry path; record every step to access.
7. Once you have a foothold, capture the initial-access evidence first.
8. Enumerate operating system, effective rights, services and misconfigurations.
9. Validate privilege escalation and record the elevated account context.
10. Return to untested services or the next assigned target.

**Exam file-transfer restriction:** OffSec forbids downloading applications, files or source code from exam targets to Kali **except when necessary to compromise the machine**; permitted local copies must be deleted after objectives. Do not treat FTP `get`, `scp`, downloading JavaScript/source, or copying from NFS/SMB as a routine exam step. Refer to the [official guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide).

**Cross-references:** [Nmap](../01-Enumeration/nmap.md), [Services](../01-Enumeration/service-enumeration.md), [Web](../02-Web-Application/web-enumeration.md), [Initial Access](../03-Initial-Access/initial-access.md), [Linux](../04-Privilege-Escalation/linux-privesc.md), [Windows](../04-Privilege-Escalation/windows-privesc.md), [AD](../05-Active-Directory/ad-enumeration.md).

## 5. Active Directory approach

The official guide states that the AD set starts with **provided credentials**, simulating a breach. Begin by validating the assigned identity, domain DNS, reachable hosts and share permissions. Draw the domain, record groups/SPNs/ACLs and reason about the next allowed host. Treat the three machines as a related set and track your position and evidence after each step.

## 6. Time management

Use these as **personal practice heuristics**, not OffSec rules:

- Spend the initial phase building service maps and noting likely paths; do not commit immediately to a CVE headline.
- If a hypothesis produces no evidence after a reasonable interval, document what failed and switch to the next lead.
- Take breaks and reserve time for screenshots, proof submissions and final reporting.
- Keep a short decision log: tested, observed, rejected, next. Avoid repeated blind scans.

## 7. Tool policy (checked 2026-11-03)

**Explicitly permitted in official exam guide:** Nmap/NSE, Nikto, Burp Free, DirBuster; msfvenom and exploit/multi/handler have the published exception explained below.

**Prohibited:** automatic exploitation (including SQLmap/SQLninja), mass vulnerability scanners, commercial Burp Pro and similar, spoofing, AI chatbots/LLMs. Tools with prohibited features cannot use those features merely because some other functions are allowed.

**Restricted to one selected target:** Metasploit Auxiliary/Exploit/Post modules and the Meterpreter payload. Once chosen, the one-target restriction sticks even if an attempt fails. Metasploit pivoting across targets is prohibited. OffSec expressly allows **msfvenom** and **exploit/multi/handler** against multiple targets, except that **Meterpreter payload use** remains one-target restricted.

OffSec does not individually bless every third-party tool; evaluate actual functionality. See the [official guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide).

## 8. Proof requirements — do not lose points

Per OffSec:
- Retrieve each required **local.txt/proof.txt** and submit it in the exam control panel **before exam ends**.
- Include a screenshot of the **original file's contents displayed by cat or type in an interactive shell on the target**.
- The screenshot must also show the target IP using ip addr / ifconfig or ipconfig.
- A web shell or any other method of obtaining proof contents is not accepted for this purpose.
- Document every command and result to make the exploit reproducible.

Full target points require an appropriate elevated shell; consult the guide for Windows SYSTEM/Administrator and Linux root requirements. Never place actual proof values in public study notes.

## 9. End-of-exam and report workflow

1. Confirm control panel submissions and required screenshots.
2. Organize commands, findings and images by target.
3. Draft a professional step-by-step report using [Reporting](./reporting.md).
4. Export to PDF, review every screenshot and command for readability.
5. Create the required unencrypted 7z archive, verify file naming and size, then upload within the official deadline.
6. Confirm final submission and matching checksum.

## Final checklist

- [ ] No prohibited tools or AI assistance used.
- [ ] All target scopes and Metasploit limitations respected.
- [ ] Full TCP coverage and service detection on every assigned host; UDP coverage explicitly considered.
- [ ] Exam file-download restriction respected and any necessary local copies removed after objectives.
- [ ] Evidence captured before leaving each host.
- [ ] Proof values submitted through control panel before exam ends.
- [ ] Interactive-shell proof screenshots show target IP.
- [ ] Every path reproducible from the report.
- [ ] PDF and unencrypted 7z submission reviewed.
- [ ] Upload confirmed and checksum verified.

## References

- [OffSec OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide)
- [OffSec AI Usage Policy](https://help.offsec.com/hc/en-us/articles/35549468971156-AI-Usage-Policy-in-OffSec-Exams)
