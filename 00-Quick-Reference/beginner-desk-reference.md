# Beginner desk reference — when your mind goes blank

This is a static study aid for authorized practice and OSCP preparation. Use only within the assigned scope. Review the [exam rules](../08-Exam-Workflow/exam-methodology.md) before relying on any tool. Do not ask an AI or another person for exam assistance.

## 1. Before touching a target

- [ ] Record assigned address, objective, allowed scope and current time in private notes.
- [ ] Confirm the VPN is connected and your machine's clock is correct.
- [ ] Open a private target worksheet; do not store exam evidence in this repository.
- [ ] Note which facts are provided versus inferred; record the exact observed service, not only its port number.
- [ ] Choose one question at a time. Record result, interpretation and uncertainty.

## 2. Command memory: local machine and existing authorized session

These commands inspect your own Kali machine or an already authorized interactive session. They do not grant access or change privileges.

| Question | Linux / Kali | Windows PowerShell or CMD |
| --- | --- | --- |
| Who am I? | `id`, `whoami` | `whoami`, `whoami /all` |
| Which machine? | `hostname` | `hostname` |
| Where am I? | `pwd` | `Get-Location` |
| List files | `ls -lah` | `Get-ChildItem -Force` |
| OS / architecture | `uname -a`, `cat /etc/os-release` | `systeminfo`, `$env:PROCESSOR_ARCHITECTURE` |
| Addresses | `ip -br addr` | `ipconfig /all` |
| Routing table | `ip route` | `route print` |
| Current time | `date -Is`, `timedatectl status` | `Get-Date`, `w32tm /query /status` |
| Local listening sockets | `ss -lntup` | `Get-NetTCPConnection -State Listen` |
| Free storage | `df -h` | `Get-PSDrive -PSProvider FileSystem` |
| File metadata | `stat FILE`, `file FILE` | `Get-Item FILE` |
| File permissions | `ls -l FILE` | `Get-Acl FILE` |
| Help | `man COMMAND`, `COMMAND --help` | `Get-Help COMMAND -Examples`, `COMMAND /?` |

Replace FILE and COMMAND with a real path or command. PowerShell and cmd.exe differ; run PowerShell cmdlets only in PowerShell. Some inspection commands require local privileges and may show incomplete results.

## 3. Terminal habits to practice

| Need | Command / shortcut | Reminder |
| --- | --- | --- |
| Stop current foreground command | Ctrl+C | Does not necessarily stop unrelated processes. |
| Clear screen | Ctrl+L | Output may remain in scrollback. |
| Search local notes | `grep -in 'keyword' notes.md` | Case-insensitive, line numbers. |
| Search Markdown across your notes | `rg -n -i --glob '*.md' 'keyword' .` | Requires ripgrep. |
| Read long output | `less FILE` | / to search; n next; q quit. |
| Inspect first/last lines | `head -n 20 FILE`, `tail -n 20 FILE` | Never publish raw secrets. |
| Check installed command | `command -v COMMAND` | No output means not on PATH. |
| Check shell syntax | `bash -n SCRIPT` | Syntax only; not a safety review. |
| Print a variable | `printf '%s\\n' "$VAR"` | Quotes preserve spaces. |
| File integrity | `sha256sum FILE` | A checksum is not encryption. |

Use Ctrl+R carefully: shell history may contain sensitive values. Do not put real passwords on the command line or in Git.

## 4. Common mental traps

- A port is an observation; a service version is an inference until verified.
- Authentication success proves an identity was accepted, not that it is authorized for every operation.
- A vulnerability identifier is not evidence of exploitability: vendor patches, configuration and prerequisites matter.
- A negative result is not proof of absence. Record the exact conditions of the test.
- A session running as a user is not necessarily elevated.
- A hostname may point to different addresses depending on DNS or VPN.
- A ticket is not a plaintext password; a checksum is not a password hash.
- A proof screenshot and the control-panel entry are separate obligations.

## 5. When something fails

Open [troubleshooting](../08-Exam-Workflow/troubleshooting-cards.md). Distinguish transport, DNS, TLS, authentication, authorization and application errors before repeating a test. If unsure, review the relevant concept in your own study material; do not improvise a destructive action.

## 6. Study navigation

- [Kerberos and identity glossary](../05-Active-Directory/kerberos-concepts.md)
- [Exam readiness and mock scorecard](../08-Exam-Workflow/readiness-scorecard.md)
- [Private practice worksheet](../09-Lab-Writeups/target-review-worksheet.md)
- [Exam workflow and evidence](../08-Exam-Workflow/exam-methodology.md)
- [Reporting](../08-Exam-Workflow/reporting.md)

The goal is to recall the meaning of commands, not to run every command in a list.
