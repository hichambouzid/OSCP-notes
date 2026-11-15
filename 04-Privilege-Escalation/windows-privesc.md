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

**Goal:** Identify insecure permissions on files, directories, registry keys and application configurations that are relevant to an authorized Windows lab. Begin with read-only checks. A writable object is only a meaningful privilege-escalation lead when a more privileged process actually uses it.

### 5.1 Establish the current account and inspect file ACLs

CMD:

~~~cmd
whoami
whoami /groups
icacls "C:\Program Files\ExampleApp"
icacls "C:\Program Files\ExampleApp\app.exe"
icacls "C:\ProgramData\ExampleApp"
~~~

Replace the example paths with actual installed application paths. Inspect both the file and its parent directory: a protected executable may still be affected by permissions on its containing directory.

| ACL indicator | Interpretation |
| --- | --- |
| F | Full control |
| M | Modify |
| W | Write |
| RX | Read and execute |
| R | Read |
| I | Inherited entry |
| OI / CI | Object / container inheritance |

An allow entry for Users or Authenticated Users is a lead, not proof of your effective access. Consider deny entries, inherited permissions, group membership, ownership, token integrity and the specific object.

PowerShell:

~~~powershell
$path = 'C:\Program Files\ExampleApp'
Get-Acl -LiteralPath $path | Format-List Owner,AccessToString
(Get-Acl -LiteralPath $path).Access |
  Format-Table IdentityReference,FileSystemRights,AccessControlType,IsInherited
~~~

### 5.2 Inspect relevant application files and directories

~~~cmd
dir /a "C:\Program Files"
dir /a "C:\Program Files (x86)"
dir /a "C:\ProgramData"
dir /a "%APPDATA%"
dir /a "%LOCALAPPDATA%"
~~~

PowerShell (file metadata, not file contents):

~~~powershell
Get-ChildItem -LiteralPath 'C:\ProgramData\ExampleApp' -Force |
  Select-Object Name,FullName,Mode,LastWriteTime
~~~

Review actual application configuration directories, scripts, service binaries, logs and startup files. Record paths and ACLs. Check which account consumes each file and whether it is loaded automatically. User-owned AppData files being writable is normally expected; a privileged service trusting a low-privilege writable path is a different situation.

### 5.3 Registry basics and permissions

| Registry hive | Purpose |
| --- | --- |
| HKCU | Settings for the current user |
| HKLM | Machine-wide configuration |
| HKU | Loaded user profiles |
| HKCR | Merged class registration view |

HKCU is tied to the account running the command. It does not automatically show another user's settings.

CMD:

~~~cmd
reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
reg query "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"
reg query "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"
~~~

On 64-bit Windows, inspect the 32-bit registry view when appropriate:

~~~cmd
reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall" /reg:64
reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall" /reg:32
~~~

Use PowerShell to inspect the ACL rather than assuming a readable key is writable:

~~~powershell
$key = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run'
Get-Acl -Path $key | Format-List Owner,AccessToString
(Get-Acl -Path $key).Access |
  Format-Table IdentityReference,RegistryRights,AccessControlType,IsInherited
~~~

Registry rights such as SetValue, CreateSubKey, WriteKey and FullControl deserve investigation if granted to an unexpected low-privilege identity. ReadKey alone does not imply write access. Use the actual key and check effective permissions before drawing conclusions.

### 5.4 PuTTY — saved session configuration

PuTTY on Windows normally stores saved sessions in the current user's registry:

~~~text
HKEY_CURRENT_USER\Software\SimonTatham\PuTTY\Sessions
~~~

SSH server host-key records are stored under the separate SshHostKeys subkey. These are server identity records, not the user's SSH private keys.

List saved session names and inspect registry permissions:

~~~cmd
reg query "HKCU\Software\SimonTatham\PuTTY\Sessions"
~~~

~~~powershell
$putty = 'HKCU:\Software\SimonTatham\PuTTY\Sessions'
if (Test-Path $putty) {
    Get-ChildItem -Path $putty | Select-Object PSChildName
    Get-Acl -Path $putty | Format-List Owner,AccessToString
} else {
    Write-Output 'No PuTTY Sessions key in the current user profile.'
}
~~~

For an actual session in the authorized lab, inspect only non-secret connection metadata, such as its protocol and port. Replace SESSION_NAME with the exact listed registry subkey name (including any percent-encoded characters).

~~~cmd
reg query "HKCU\Software\SimonTatham\PuTTY\Sessions\SESSION_NAME" /v Protocol
reg query "HKCU\Software\SimonTatham\PuTTY\Sessions\SESSION_NAME" /v PortNumber
~~~

~~~powershell
$session = Join-Path $putty 'SESSION_NAME'
Get-Acl -Path $session | Format-List Owner,AccessToString
~~~

**Interpretation:** A saved PuTTY session is a configuration record, not proof of an available password, a successful login or an elevation path. PuTTY does not normally save SSH login passwords in session settings. Do not dump session secrets, private keys or other users' profile data. A missing key can mean PuTTY was not used by the current account, no sessions were saved, or a different storage mechanism is used.

### 5.5 Other remote-access applications

Check installed applications first. For programs actually present, review their configuration location and ACLs instead of dumping their contents.

| Application | Configuration location / check |
| --- | --- |
| PuTTY | HKCU\Software\SimonTatham\PuTTY |
| WinSCP | HKCU\Software\Martin Prikryl\WinSCP 2, or an INI file depending on configuration |
| Windows Remote Desktop | Current user's Remote Desktop client configuration and user-authorized .rdp files |
| Other SSH/SFTP clients | Vendor-documented settings in the current user's profile |

Example ACL-only inspection for WinSCP if it is installed:

~~~powershell
$key = 'HKCU:\Software\Martin Prikryl\WinSCP 2'
if (Test-Path $key) {
    Get-Acl -Path $key | Format-List Owner,AccessToString
}
~~~

The existence of a configuration key or remote-access application is not a vulnerability. Keep credentials, tokens, private keys and sensitive target details out of public notes.

### 5.6 Service registry keys and startup paths

Compare registry configuration with the service inventory from section 2.

~~~cmd
sc.exe qc SERVICE_NAME
icacls "C:\Path\To\ServiceFolder"
~~~

~~~powershell
$key = 'HKLM:\SYSTEM\CurrentControlSet\Services\SERVICE_NAME'
Get-Acl -Path $key | Format-List Owner,AccessToString
~~~

Replace SERVICE_NAME and the executable path with the actual service. Review its run-as account, binary path, start mode and ACLs. For startup entries, identify whether they run for the current user or a more privileged account and inspect the referenced file and directory permissions. Check scheduled task actions using section 3.

Do not change service settings, registry values or file permissions during enumeration. A configuration that can only affect your existing user context does not demonstrate privilege escalation.

### 5.7 Decide whether the finding is meaningful

| Observation | Next check |
| --- | --- |
| Writable application folder | Does a privileged process load a file from that folder? |
| Writable service registry key | Which service uses the key, what rights exist, and what account runs it? |
| Writable startup entry or script | Which identity executes it, and when? |
| PuTTY or WinSCP configuration exists | Verify current-user scope and ACLs; do not assume credentials or elevated rights |
| Access denied | Record the restriction; do not assume a missing file or key |
| No relevant weak permissions | Return to services, tasks, token privileges and patch review |

**Evidence template:** record the target, current user, actual object path, owner, relevant access-control entry, consuming process/account, and why the permission is unexpected. Keep only the permitted evidence in private lab notes.

**References:** [Microsoft icacls](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/icacls), [Microsoft Get-Acl](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.security/get-acl), [PuTTY documentation — stored settings](https://the.earth.li/~sgtatham/putty/0.68/htmldoc/AppendixA.html#faq-settings), [WinSCP configuration storage](https://winscp.net/eng/docs/config).

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
- [ ] Relevant file and registry ACLs reviewed, including current-user PuTTY/WinSCP configuration when present.
- [ ] Confirm which privileged process uses a suspicious writable object before treating it as escalation.
- [ ] Local listeners and permissions investigated.
- [ ] CVE applicability validated against actual target build.
- [ ] Privilege change demonstrated in the target context.
- [ ] Evidence and proof screenshots captured according to OffSec rules.

## References

- [OffSec OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide)
- [Microsoft Windows commands](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/windows-commands)
- [Microsoft Learn: Sysinternals](https://learn.microsoft.com/en-us/sysinternals/)
