# Linux Privilege Escalation — OSCP Field Guide

> Scope: Authorized practice labs and assigned exam targets only. Work from an established interactive shell. The aim is a repeatable **manual privilege-escalation workflow**, not running every tool at once.

## Quick decision tree

1. Record your current identity, groups, environment and OS version.
2. Check explicit permissions (sudo rules), then SUID/SGID and capabilities.
3. Inspect scheduled jobs, services, writable scripts, startup paths and local listeners.
4. Look for relevant misconfigurations and credible version-specific advisories.
5. Verify the exact precondition of a candidate before attempting it.
6. Record the original finding, commands, outcome and current privilege level.

## 1. Establish context

~~~bash
whoami
id
hostname
uname -a
cat /etc/os-release
pwd
echo "$PATH"
env | sort
ip -br addr
ip route
ss -lntup
~~~

Observe groups, home directory, kernel, distributions and listening services. Output from **ss** may be limited without root.

## 2. Sudo permissions — first priority

~~~bash
sudo -l
sudo -V | head
~~~

Look for commands explicitly allowed as another user, NOPASSWD rules, environment inheritance and command arguments. Check whether an allowed utility supports a legitimate privilege boundary crossing before taking action. See [GTFOBins](https://gtfobins.github.io/) as a **research reference**, not evidence of an exploitable configuration. Do not guess passwords or change sudoers blindly.

## 3. SUID/SGID, Linux capabilities

~~~bash
find / -xdev -type f -perm -4000 2>/dev/null
find / -xdev -type f -perm -2000 2>/dev/null
getcap -r / 2>/dev/null
~~~

Investigate unexpected custom executables and unusually powerful capabilities (for example, CAP_SETUID or CAP_DAC_READ_SEARCH). The presence of a SUID binary **alone** is not a vulnerability. Inspect version, owner, permissions and behavior.

## 4. Writable files, directories and configuration

~~~bash
find /etc /opt /usr/local /var/www -type f -writable 2>/dev/null
find /etc /opt /usr/local -type d -writable 2>/dev/null
ls -la /opt /usr/local/bin /var/www 2>/dev/null
find /home -maxdepth 3 -type f -name '*.sh' 2>/dev/null
~~~

Review scripts only when they are in scope and your account can legitimately access them. Look for root-executed jobs that depend on writable script paths, relative executable names, unsafe permissions or insecure configuration. Inspect the actual **parent directory** permissions too.

## 5. Scheduled tasks, processes and services

~~~bash
cat /etc/crontab
ls -la /etc/cron.d /etc/cron.daily /etc/cron.hourly 2>/dev/null
systemctl list-timers --all --no-pager
systemctl list-units --type=service --state=running --no-pager
ps auxww
~~~

Note root-owned tasks that invoke writable files, systemd units with unusual ExecStart paths, application services and locally bound admin interfaces. Do not modify any service before verifying that you understand the impact.

## 6. Application credentials and local-only access

Inspect **only files accessible in the authorized lab**: web application configuration, backup files, user-owned shell history and systemd environment settings. Avoid copying or publishing secrets. Compare any discovered credential with the lab's scope before attempting reuse. The host may expose a local-only web or database service; document its binding and authentication before deciding whether to access it.

## 7. Version and CVE validation

~~~bash
uname -r
dpkg -l 2>/dev/null | head
rpm -qa 2>/dev/null | head
searchsploit "sudo"
~~~

Compare the **exact installed package build**, distro backports, configuration and exploit prerequisites with vendor advisories. Do not run random kernel exploits based only on a banner or search hit. Keep working exploit code from trusted sources in a separate lab-only folder and record modifications.

## 8. Interactive shell and evidence

~~~bash
python3 -c 'import pty; pty.spawn("/bin/bash")'
export TERM=xterm
id
hostname
~~~

If no Python or Bash is present, work with the shell you have; avoid assuming an upgrade is always possible. Capture each successful privilege change with the original entry point and commands used.

## Troubleshooting

| Observation | What to check |
| --- | --- |
| sudo -l requests a password | Confirm whether you have authorized credentials; do not assume NOPASSWD |
| A SUID binary is present | Is it custom? Can it actually cross a privilege boundary? |
| Cron script writable but no effect | Is the scheduled job active? Which user runs it? |
| Kernel exploit mismatch | Distribution backports, compiler, architecture, patches |
| Permission denied | Ownership, directory permissions, mount options, MAC policies |
| Shell closes or lacks TTY | Listener, interpreter availability, session handling |

## OSCP checklist

- [ ] Identity, groups, OS and kernel documented.
- [ ] Sudo, SUID/SGID and capabilities reviewed.
- [ ] Scheduled tasks, services, processes and writable paths reviewed.
- [ ] Local listeners and accessible application configuration reviewed.
- [ ] Candidate misconfiguration manually verified.
- [ ] Evidence captured without exposing sensitive data.
- [ ] Proof captured per current OffSec interactive-shell/screenshot requirements.

## References

- [OffSec OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide)
- [GTFOBins](https://gtfobins.github.io/)
- [Linux manual pages](https://man7.org/linux/man-pages/)
