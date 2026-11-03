# Windows Privilege Escalation — OSCP Field Guide

> Scope: Authorized labs and assigned targets only. Begin from a legitimate low-privilege Windows shell. Compare configuration and effective permissions instead of treating every old version as vulnerable.

## Quick decision tree

1. Who am I? Identify user, groups and token privileges.
2. What OS and patch level? Check architecture and Windows build.
3. Are there service permissions, scheduled tasks, writable binaries or autoruns?
4. Are application secrets or privileged credential contexts available **within scope**?
5. Is a relevant exploit demonstrably applicable to this build?
6. Verify, document, and record the resulting privileges.

## 1. Inventory and token

~~~cmd
whoami
whoami /all
hostname
systeminfo
ipconfig /all
net user
net localgroup administrators
~~~

If PowerShell is available:

~~~powershell
Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, OsBuildNumber, OsArchitecture
Get-LocalUser
Get-LocalGroupMember -Group Administrators
Get-Process | Select-Object -First 20 Name,Id,Path
~~~

Some commands require elevated rights or are unavailable on older systems. Missing results do not imply missing protections.

## 2. Services and service permissions

~~~cmd
sc query state= all
sc qc SERVICE_NAME
icacls "C:\Path\To\ServiceFolder"
~~~

Check the **service's account**, binary path, executable ACL, writable parent directories, and the right to reconfigure or restart the service. An unquoted service path is interesting only if a realistic unquoted-path resolution and writable location exist. Do not tamper with running services just because a name is unquoted.

~~~powershell
Get-CimInstance Win32_Service | Select-Object Name,StartName,PathName,State,StartMode
~~~

## 3. Scheduled tasks, programs and startup

~~~cmd
schtasks /query /fo LIST /v
dir "C:\Program Files"
reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
~~~

Avoid Win32_Product inventory queries because they can have installer side effects. Prefer the following read-only checks for installed apps:

~~~powershell
Get-ItemProperty 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue | Select-Object DisplayName,DisplayVersion,InstallLocation
Get-ScheduledTask | Select-Object TaskName,TaskPath,State
Get-ChildItem 'C:\ProgramData' -Force -ErrorAction SilentlyContinue
~~~

Review task actions, owners and access rights. An editable script invoked by an elevated task may merit controlled validation.

## 4. Token privileges and local security settings

~~~cmd
whoami /priv
whoami /groups
net accounts
cmdkey /list
~~~

Some sensitive privileges (such as SeImpersonatePrivilege) require a specific execution context; possession of the privilege **does not guarantee escalation**. Search OS-version-specific vendor guidance before considering a technique. Do not copy local credentials or password vaults outside the lab scope.

## 5. File and registry permissions

~~~cmd
icacls "C:\Program Files\ExampleApp"
reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
reg query "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
~~~

For application services, compare ownership and writable access to configuration and executable paths. Avoid registry writes or service modifications until the full preconditions are understood.

## 6. Network and patch observations

~~~cmd
netstat -ano
tasklist /svc
systeminfo
~~~

Look for local services and opportunities to interact with **approved** application functions. For a suspected CVE, verify exact architecture, patch level, prerequisites and vendor security update history. Do not infer vulnerability from a generic build number alone.

## 7. Validate success and record evidence

~~~cmd
whoami
whoami /all
hostname
ipconfig
~~~

An administrator-group membership is not the same thing as an **elevated** token. UAC may affect your effective rights. For full Windows target points, consult the current OffSec proof/shell requirements.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Access denied when inspecting service | Effective ACLs and token rights |
| Service path contains spaces | Quoting *and* writable candidate directories |
| Task never runs | Trigger, context, account, schedule and permissions |
| Missing PowerShell cmdlet | OS/PowerShell version, privilege restrictions |
| Administrator member but not elevated | UAC, token and integrity level |
| A suggested CVE fails | Patch level, architecture and exploit preconditions |

## OSCP checklist

- [ ] Identity, token privileges, groups and integrity context recorded.
- [ ] Services, binary ACLs and scheduled tasks reviewed.
- [ ] Installed apps, startup entries and writable paths checked.
- [ ] Local listeners and permissions investigated.
- [ ] CVE applicability validated against actual target build.
- [ ] Privilege change demonstrated in the target context.
- [ ] Evidence and proof screenshots captured according to OffSec rules.

## References

- [OffSec OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide)
- [Microsoft Windows commands](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/windows-commands)
- [Microsoft Learn: Sysinternals](https://learn.microsoft.com/en-us/sysinternals/)
