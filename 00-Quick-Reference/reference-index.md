# Fast reference index — find the right page

Start here when you need to locate a topic without scrolling through long guides. Use the references for authorized practice, and review the official exam policy before the actual exam.

| What I need | Where to find it |
| --- | --- |
| Basic Kali/Linux/Windows inspection commands | [Beginner desk reference](beginner-desk-reference.md#2-command-memory-local-machine-and-existing-authorized-session) |
| Local terminal exercises with expected output | [Hands-on drills](../09-Lab-Writeups/hands-on-terminal-drills.md) |
| Quick workflow | [Quick reference](quick-reference.md) |
| Host discovery and VPN | [Host discovery](../01-Enumeration/host-discovery.md) |
| Understand TCP/UDP service inventory | [Nmap notes](../01-Enumeration/nmap.md) |
| Protocol and service explanations | [Service enumeration](../01-Enumeration/service-enumeration.md) |
| Web testing concepts | [Web testing](../02-Web-Application/web-vulnerability-testing.md) |
| Initial-access concepts and prerequisites | [Initial-access concepts](../03-Initial-Access/initial-access-concepts.md) |
| Linux permissions and escalation concepts | [Linux guide](../04-Privilege-Escalation/linux-privesc.md) |
| Windows token and permission concepts | [Windows guide](../04-Privilege-Escalation/windows-privesc.md) |
| Kerberos TGT, TGS, SPN, clock skew and encryption | [Kerberos concept cards](../05-Active-Directory/kerberos-concepts.md) |
| Password versus hash versus checksum | [Password auditing notes](../06-Passwords/password-auditing.md) and [local drill 3](../09-Lab-Writeups/hands-on-terminal-drills.md#drill-3--hashes-versus-passwords) |
| Network routing and tunnel concepts | [Pivoting guide](../07-Pivoting/pivoting-tunneling.md) |
| Connection refused, HTTP 403, access denied | [Troubleshooting cards](../08-Exam-Workflow/troubleshooting-cards.md) |
| Record observations, hypotheses and evidence | [Private worksheet](../09-Lab-Writeups/target-review-worksheet.md) |
| Proof format and exam restrictions | [Exam methodology](../08-Exam-Workflow/exam-methodology.md) |
| Report packaging and submission | [Reporting](../08-Exam-Workflow/reporting.md) |
| What to practice next | [Readiness scorecard](../08-Exam-Workflow/readiness-scorecard.md) |

## Search from the repository root

~~~bash
rg -n -i --glob '*.md' 'clock skew' .
rg -n -i --glob '*.md' 'connection refused' .
rg -n -i --glob '*.md' 'proof' 08-Exam-Workflow
~~~

Search output shows file and line number. The command is for local documentation, not scanning targets. If ripgrep is missing, grep -Rin 'keyword' . is an alternative.

## How to read a command example

1. Identify which machine and shell it is intended for.
2. Identify required privileges, tools, files and configuration.
3. Replace placeholders only with appropriate values from your authorized scope.
4. Read each argument and understand expected output.
5. Distinguish a failed test from a confirmed finding.
6. Record actual results privately and clean up as required.

## External references

- [OffSec OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide) — official rules and requirements.
- [OffSec OSCP+ FAQ](https://help.offsec.com/hc/en-us/articles/4412170923924-OSCP-Exam-FAQ) — resources, exam logistics and template links.
- [OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/) — security concepts and methodology.
- [Repository comparison](../08-Exam-Workflow/reference-comparison.md) — why these notes are structured this way.
