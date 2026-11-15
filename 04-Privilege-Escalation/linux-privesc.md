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

`-xdev` is a speed/scope optimization: it **excludes other mounted filesystems**. Check `findmnt` or `mount`, and inspect additional **in-scope** mounted locations (for example `/mnt`, `/opt`, or user home mounts) separately when relevant, rather than assuming the initial search was exhaustive.

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

## 9. Practical privilege-escalation playbook

Use this section after the initial inventory. Commands are examples for disposable, authorized lab targets; replace paths and identities with the observed values. Start read-only, confirm an actual higher-privilege execution context, and prefer a reversible test. A useful result is an elevated identity, not merely a suspicious file.

### 9.1 Fast triage and effective permissions

~~~bash
id; groups; umask
getent passwd
getent group sudo wheel docker lxd disk adm shadow
findmnt -o TARGET,SOURCE,FSTYPE,OPTIONS
ls -la /home /opt /srv /usr/local/bin /var/backups
ps -eo user,pid,ppid,args --forest
ss -lntup
~~~

For a candidate path:

~~~bash
namei -l /opt/example/backup.sh
stat /opt/example/backup.sh
getfacl -p /opt/example/backup.sh /opt/example
test -w /opt/example/backup.sh && echo writable
~~~

Check ACL masks, supplementary groups, symlink targets, parent directory replacement rights, read-only mounts, sticky bits, SELinux/AppArmor and filesystem boundaries. A writable directory can permit replacing a file even when that file is not writable.

### 9.2 Sudo: command escapes, arguments, environment and delegation

~~~bash
sudo -n -l     # non-interactive check; failure may mean password required
sudo -l
sudo -V | head -n 5
~~~

| Candidate | What makes it interesting |
| --- | --- |
| Editors, pagers, interpreters | Shell escape or arbitrary code execution in the permitted run-as context |
| find, awk, tar, rsync | Command hooks or options; exact allowed arguments matter |
| cp, tee, chmod, chown, install | File write or ownership changes affecting a privileged resource |
| Wrapper or custom script | Writable script, imports, configuration or executable resolution |
| sudoedit | Editable target, symlink protections and version-specific bugs |
| SETENV / env_keep | Loader or interpreter variables accepted by policy |
| Wildcards | Unexpected argument expansion, traversal or option injection |
| Runas restrictions | Check whether the target user is root or another account; another user is not necessarily root |

**Lab example:** if the exact rule permits unrestricted root execution of /usr/bin/find, a manual demonstration is:

~~~bash
sudo /usr/bin/find /tmp -maxdepth 0 -exec /bin/sh \;
id
exit
~~~

This is not applicable to a rule that fixes incompatible arguments or a different run-as user. A password prompt is not evidence that a passwordless path exists. Consult the matching [GTFOBins](https://gtfobins.org/) context; sudo, SUID and capabilities are distinct. Do not modify sudoers just to prove a lab finding.

### 9.3 SUID, SGID, custom binaries and capabilities

~~~bash
find / -xdev -type f -perm /6000 -ls 2>/dev/null
getcap -r /usr /opt /home 2>/dev/null
file /opt/example/helper
stat /opt/example/helper
strings -a /opt/example/helper | head -n 100
readelf -d /opt/example/helper
~~~

SUID changes effective user ID; SGID changes effective group ID. Check owner and group, mount nosuid, executable type and whether the program drops elevated IDs. Investigate custom helpers first, especially ones invoking external tools by relative name or accepting user-controlled paths.

| Capability | Candidate impact |
| --- | --- |
| CAP_SETUID / CAP_SETGID | Identity changes if the program exposes a suitable operation |
| CAP_DAC_READ_SEARCH | Bypass file read/search checks |
| CAP_DAC_OVERRIDE | Bypass many discretionary file access checks |
| CAP_CHOWN / CAP_FOWNER | Ownership or permission-related operations |
| CAP_SYS_ADMIN | Broad administrative functionality, namespace-dependent |
| CAP_SYS_PTRACE | Inspect or manipulate processes subject to additional restrictions |

If a disposable lab intentionally provides a root-owned SUID Bash binary and the mount honors SUID, the matching validation is /path/to/bash -p followed by id. Ordinary Bash is not SUID; the command is not an escalation by itself. Avoid creating new SUID files as a shortcut.

### 9.4 Cron, systemd timers, anacron and log rotation

~~~bash
cat /etc/crontab
ls -la /etc/cron* /var/spool/cron /var/spool/cron/crontabs 2>/dev/null
crontab -l
cat /etc/anacrontab 2>/dev/null
systemctl list-timers --all --no-pager
systemctl cat example.timer example.service
systemctl show example.service -p User -p Group -p ExecStart -p FragmentPath -p DropInPaths
ls -la /etc/logrotate.d /etc/systemd/system /usr/lib/systemd/system
~~~

For each job follow the entire chain: scheduler -> run-as identity -> executable -> interpreter/imports -> configuration -> files consumed. Check root-run backups, archive wildcards, relative commands, writable PATH directories, logrotate pre/post scripts, systemd unit overrides and environment files. A root-owned script does not necessarily run as root.

A reversible lab proof for a deliberately editable root-run script is to have it write its effective identity to a dedicated, non-sensitive lab marker in a controlled directory, observe the next authorized run, then restore the original file and remove the marker. Do not interrupt critical jobs. [pspy](https://github.com/DominicBreuker/pspy) can help observe short-lived jobs without root; process arguments may contain secrets, so keep output private.

### 9.5 PATH, wildcard, library and interpreter hijacking

~~~bash
printf '%s\n' "$PATH" | tr ':' '\n'
type -a tar python3
readelf -d /opt/example/helper | grep -E 'NEEDED|RPATH|RUNPATH'
grep -nE 'PATH=|LD_|PYTHONPATH|import |source |(^|[[:space:]])\.[[:space:]]' /opt/example/backup.sh
ls -l /etc/ld.so.conf /etc/ld.so.conf.d /etc/ld.so.preload 2>/dev/null
~~~

- PATH: privileged process invokes a command without an absolute path and searches a directory controlled by the lower-privilege user.
- Wildcards: a privileged utility interprets attacker-controlled filenames as options; inspect actual invocation and whether -- terminates options.
- Shared libraries: check loader search order, RPATH/RUNPATH and writable library locations. LD_PRELOAD/LD_LIBRARY_PATH may be ignored in secure-execution mode; sudo can sanitize the environment.
- Python/Perl/Ruby: privileged script imports from a writable module location or invokes a writable interpreter/plugin. Confirm import order and actual runtime.
- Shell scripts: unsafe source/include, eval, temporary file names and symlink races. Confirm actual access and timing.

Prefer readelf over running ldd on untrusted executables. A writable path alone is not enough: identify the privileged caller and the real resolution order.

### 9.6 Credentials, backups, SSH and application footprints

~~~bash
ls -la "$HOME" "$HOME/.ssh" /var/backups /opt /srv /var/www 2>/dev/null
find /opt /srv /var/www "$HOME" -maxdepth 4 -type f \
  \( -name '.env' -o -name '*.bak' -o -name '*.old' -o -name 'wp-config.php' \
     -o -name 'config.php' -o -name 'settings.py' -o -name '*.kdbx' \) \
  -readable -print 2>/dev/null
ls -l /etc/passwd /etc/shadow /etc/sudoers /etc/sudoers.d 2>/dev/null
~~~

Check accessible application database configuration, deployment files, backup copies, shell history, Git configuration, SSH identity files and authorized_keys ACLs. Inspect only the relevant in-scope records; do not assume readable private keys are unencrypted, authorized on another host, or associated with a privileged user. A service account password may lead to another local user, not root. Validate only known authorized credentials using an appropriate local login, then repeat id and sudo -l. Do not publish any raw credentials or key material.

Also review process/service footprints (systemctl cat, readable config paths, local database listeners), package-manager credentials, mounted shares and application-specific admin functions. A loopback service is not automatically accessible without authentication.

### 9.7 Privileged groups, containers and management sockets

~~~bash
id
ls -l /var/run/docker.sock /run/containerd/containerd.sock /var/lib/lxd/unix.socket /var/snap/lxd/common/lxd/unix.socket 2>/dev/null
ls -l /dev/sd* /dev/vd* 2>/dev/null
cat /proc/self/cgroup
lsns 2>/dev/null
cat /proc/self/uid_map /proc/self/gid_map
~~~

| Group / resource | What to validate |
| --- | --- |
| docker / rootful Docker socket | Daemon access, authorization plugin, rootless vs rootful, host mount permissions |
| lxd / incus | Administrative socket, project restrictions and privileged instance permissions |
| disk | Raw block device access and whether it contains the host filesystem; do not write to devices |
| adm / systemd-journal | Readable logs may disclose useful context, not direct root |
| shadow | Sensitive credential file access, not automatic root |
| libvirt / kvm | Actual management rights and host resource exposure |
| sudo / wheel | Effective sudo policy, not just group name |

Container root is not necessarily host root. Check namespace mapping, capabilities, bind mounts, privileged mode, exposed management sockets and runtime policies. Do not launch privileged containers or mount host filesystems unless the specific lab permits it. For read-only confirmation of a Docker management API exposure, docker info is useful if available; it does not prove host-level control by itself.

### 9.8 NFS, mounts, writable privileged files and ACL inheritance

~~~bash
findmnt -t nfs,nfs4,cifs
cat /etc/fstab
cat /etc/exports 2>/dev/null
ls -l /etc/passwd /etc/shadow /etc/sudoers
getfacl -p /etc/passwd /etc/sudoers 2>/dev/null
~~~

On a separately authorized NFS server, showmount -e HOST can enumerate exports, although NFSv4-only setups may not expose mountd. Check export source restrictions, root_squash vs no_root_squash, client UID mapping, writable export and whether the server consumes exported files with privilege. no_root_squash by itself is not sufficient; you need authorized access and the relevant filesystem relationship. Review CIFS mount permissions, writable PAM/service config, root scripts and writable account databases without altering authentication files.

### 9.9 Other elevated execution paths

| Technique | Manual validation |
| --- | --- |
| Polkit / pkexec | Check installed policy rules and package build; determine authorized actions and authentication requirements |
| D-Bus / local IPC | List exposed services, inspect policy and application-specific privileged methods |
| Package managers / maintenance | Check sudo delegation, root-run package hooks and writable configuration; do not install arbitrary packages |
| Mail, backup, monitoring agents | Identify root-run actions, plugins, scripts and writable inputs |
| SSH forced commands / restricted shells | Verify allowed commands and real run-as identity; a shell escape may only restore the same user's access |
| Writable startup files | Verify which user reads the file and whether it executes in a privileged context |

~~~bash
command -v pkexec busctl
ls -la /etc/polkit-1/rules.d /usr/share/polkit-1/rules.d 2>/dev/null
busctl --system list 2>/dev/null
ls -la /etc/profile.d /etc/sudoers.d /etc/apt/apt.conf.d 2>/dev/null
~~~

### 9.10 Kernel and package CVEs — last resort

| Historical example | Check first |
| --- | --- |
| Dirty COW (CVE-2016-5195) | Kernel package, distro patch/backport status, architecture |
| Dirty Pipe (CVE-2022-0847) | Affected kernel version and distribution fixes |
| Copy Fail (CVE-2026-31431) | Running kernel, AF_ALG/algif_aead availability, vendor patch status; see section 9.10.1 |
| Baron Samedit (CVE-2021-3156) | Exact sudo package and vendor advisory |
| PwnKit (CVE-2021-4034) | Exact polkit package, pkexec installation and vendor fixes |
| OverlayFS / namespace issues | Specific CVE, distro build, namespace configuration and required filesystem |

~~~bash
uname -a
cat /etc/os-release
dpkg-query -W sudo policykit-1 polkitd 2>/dev/null
rpm -q sudo polkit kernel 2>/dev/null
sysctl kernel.unprivileged_userns_clone user.max_user_namespaces 2>/dev/null
~~~

These are research leads, not universal exploits. Verify exact CVE prerequisites, review source, match architecture and libc, and use a disposable snapshot for crash-prone practice. Prefer configuration-based escalation over risky kernel exploitation. References: [Ubuntu CVEs](https://ubuntu.com/security/cves), [Debian security tracker](https://security-tracker.debian.org/tracker/), [Red Hat security](https://access.redhat.com/security/).

### 9.10.1 Copy Fail (CVE-2026-31431) — Linux local privilege escalation

Disclosed April 29, 2026 by Theori / Xint Code. CVSS 3.1: 7.8 (High). An error in the kernel's algif_aead implementation of the AF_ALG userspace crypto interface permits a local unprivileged user to modify cached file data; a published proof of concept targets a setuid binary and can yield root on affected systems. The modification is in the page cache, not an ordinary on-disk file write. This is a local post-foothold vulnerability, not remote code execution.

**Prerequisites and enumeration**

- A shell or local code execution on an explicitly authorized vulnerable Linux host.
- An affected, unpatched running kernel with the relevant crypto interface accessible. Distribution backports and mitigation policies matter; kernel version alone is insufficient.
- Python 3.10+ for the original Python PoC; standard library only.
- A disposable VM with a snapshot, not a production server or a container on a shared host. Containers share the host kernel and can have additional restrictions or cross-container effects.

~~~bash
id
uname -r
cat /etc/os-release
python3 --version
grep -E '^CONFIG_CRYPTO_USER_API_AEAD=' "/boot/config-$(uname -r)" 2>/dev/null
grep '^algif_aead ' /proc/modules
modinfo algif_aead 2>/dev/null
ls -l /usr/bin/su
findmnt -T /usr/bin/su -o TARGET,OPTIONS
~~~

An absent module listing does not establish safety: it may be built into the kernel, available for autoload, disabled by policy, or unavailable. On Ubuntu, compare the exact running kernel package and flavour against the vendor security tracker; on Debian/RHEL use the corresponding vendor advisory. An installed fixed kernel is not necessarily the currently booted kernel.

**Original PoC and script**

- [Original Theori source](https://github.com/theori-io/copy-fail-CVE-2026-31431/blob/main/copy_fail_exp.py)
- [Local Python retrieval helper](vulnerabilities/copy_fail.py) — retrieves the published 732-byte script, verifies its SHA-256 against the researcher's disclosure, refuses to overwrite a file, and never executes it.
- Original SHA-256: a567d09b15f6e4440e70c9f2aa8edec8ed59f53301952df05c719aa3911687f9.

From the repository root on your preparation workstation:

~~~bash
python3 04-Privilege-Escalation/vulnerabilities/copy_fail.py --output copy_fail_exp.py
sha256sum copy_fail_exp.py
less copy_fail_exp.py
~~~

Review the original source, then use the verified script only in your disposable, assigned practice VM. The upstream demonstration targets /usr/bin/su by default; after manually running the PoC, invoking su is the researcher's documented way to enter the resulting shell. Check id before and after; successful Python execution alone does not prove root. Restore the VM snapshot after the exercise, since the PoC alters the cached privileged executable. Do not use the script on a production machine, shared container host or any target outside your explicit authorization. Do not assume an old build is vulnerable or disable security controls to make it work.

**Patch and mitigation**

Update the distribution kernel to a fixed package and reboot into that kernel. The upstream fix is commit a664bf3d603d; vendors may backport it with different package versions. Blocking the affected AF_ALG feature or disabling the algif_aead module where supported can be a temporary vendor-approved mitigation, but may affect applications. Do not use a missing module listing or on-disk file integrity alone to establish that a host is patched or uncompromised.

**References**

- [Researcher disclosure and original PoC hash](https://copy.fail/)
- [CERT/CC VU#260001](https://kb.cert.org/vuls/id/260001)
- [Ubuntu CVE tracker](https://ubuntu.com/security/CVE-2026-31431)
- [Debian CVE tracker](https://security-tracker.debian.org/tracker/CVE-2026-31431)
- [Red Hat advisory](https://access.redhat.com/security/vulnerabilities/RHSB-2026-002)
- [OffSec OSCP+ exam guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide) — check current restrictions before using any exploit in an exam; AI assistance is not permitted during the exam.

### 9.11 Enumeration helpers and evidence

- [LinPEAS](https://github.com/peass-ng/PEASS-ng): enumeration aid; manually verify every candidate. Avoid automatic exploitation features.
- [GTFOBins](https://gtfobins.org/): consult the exact execution context and binary version.
- [pspy](https://github.com/DominicBreuker/pspy): observe processes and periodic jobs; do not publish sensitive arguments.

Record the original identity, relevant command output, exact permission, privileged consumer and reproducible lab test. After a successful escalation, confirm effective UID 0 with id; an ordinary user with access to one sensitive file is not a root shell. For assigned exam targets use the original proof file and target IP in an interactive-shell screenshot per current OffSec rules. Keep target evidence private, and restore test changes where permitted.

### 9.12 Expanded checklist

- [ ] Sudo rules, run-as, arguments, environment, wrappers, sudoedit.
- [ ] SUID/SGID, capabilities, custom helpers, all relevant mounts.
- [ ] Cron, timers, anacron, logrotate, root-owned process chains.
- [ ] PATH, loader, interpreter imports, wildcards, writable parent directories.
- [ ] Application config, user trails, SSH, backups and local services.
- [ ] Privileged groups, management sockets, containers and namespace boundaries.
- [ ] NFS/other mounts, ACLs, account file permissions, privileged IPC.
- [ ] Vendor-confirmed package/kernel CVEs only if applicable.
- [ ] Effective root identity, proof, cleanup and sanitized notes.

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
- [ ] Sudo, SUID/SGID and capabilities reviewed, with relevant additional mounts checked where `-xdev` skipped them.
- [ ] Scheduled tasks, services, processes and writable paths reviewed.
- [ ] Local listeners and accessible application configuration reviewed.
- [ ] Candidate misconfiguration manually verified.
- [ ] Evidence captured without exposing sensitive data.
- [ ] Proof captured per current OffSec interactive-shell/screenshot requirements.

## References

- [OffSec PEN-200 learning plan](https://help.offsec.com/hc/en-us/articles/15541765522196-OffSec-PEN-200-Learning-Plan-12-Week)
- [OffSec OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide)
- [GTFOBins](https://gtfobins.github.io/)
- [Linux manual pages](https://man7.org/linux/man-pages/)
