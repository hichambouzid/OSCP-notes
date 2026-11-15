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


#### PuTTY deeper triage: identity, key references and proxy configuration

A saved session can give a useful lead for an authorized lab, particularly when an application or administrator has configured SSH access. Enumerate relevant properties by name, avoid printing stored secret values, and keep any lab-specific hostnames, usernames and paths private.

~~~powershell
$root = 'HKCU:\Software\SimonTatham\PuTTY\Sessions'
if (Test-Path $root) {
    Get-ChildItem -LiteralPath $root | ForEach-Object {
        $p = Get-ItemProperty -LiteralPath $_.PSPath
        [pscustomobject]@{
            Session = $_.PSChildName
            HostName = $p.HostName
            UserName = $p.UserName
            Protocol = $p.Protocol
            PortNumber = $p.PortNumber
            PublicKeyFile = $p.PublicKeyFile
            ProxyMethod = $p.ProxyMethod
            HasProxyPasswordField = ($null -ne $p.PSObject.Properties['ProxyPassword'])
        }
    } | Format-Table -AutoSize
}
~~~

| Setting | Meaning / follow-up |
| --- | --- |
| HostName, PortNumber, Protocol | Destination and protocol; confirm it is assigned and in scope |
| UserName | Configured SSH username; not necessarily a Windows administrator |
| PublicKeyFile | Path to a configured private-key file, despite the historical setting name; verify existence, owner and ACL |
| ProxyMethod, ProxyHost, ProxyUsername | Proxy routing and identity; not evidence of privilege |
| ProxyPassword | A proxy authentication setting may exist; it is not the SSH login password and its presence is not proof of usable credentials |
| SshHostKeys | Cached server identities; not private authentication keys |
| Pageant | SSH agent; running process does not demonstrate a loaded or usable key |

~~~powershell
Get-Process putty,pageant,plink -ErrorAction SilentlyContinue |
    Select-Object Name,Id,Path
Get-ChildItem -LiteralPath $HOME -Filter '*.ppk' -File -Recurse -ErrorAction SilentlyContinue |
    Select-Object FullName,Length,LastWriteTime
Get-ChildItem -LiteralPath "$HOME\.ssh" -Force -ErrorAction SilentlyContinue |
    Select-Object Name,FullName,Mode
# Replace with an actual in-scope configured key path:
Get-Acl -LiteralPath 'C:\Lab\example.ppk' | Format-List Owner,AccessToString
~~~

Check portable installations, saved session exports and related client settings only when present. PuTTY's HKCU hive belongs to the process identity; service accounts and other loaded profiles can have different settings. Do not load or copy other user hives just to search for secrets.

**Lab decision:** if an explicitly authorized SSH key or supplied credential is associated with an assigned target, confirm the intended destination and identity and test authentication via the appropriate SSH client. An SSH login may be another low-privileged account, a separate host (lateral movement), or an administrator/root account. Confirm the actual resulting identity before classifying it as escalation. A .ppk may be encrypted and a saved session may be obsolete. Never commit private keys, proxy passwords or session dumps. See the [current PuTTY FAQ](https://www.chiark.greenend.org.uk/~sgtatham/putty/faq.html).

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

## 8. Practical Windows privilege-escalation playbook

Use these additional checks after the first pass. Each technique needs a real boundary: current identity -> controllable input or permission -> higher-privileged consumer -> trigger -> verified elevated identity. Commands use illustrative paths and service names, not real target data. Run only in disposable authorized labs, keep changes reversible, and do not interrupt essential services.

### 8.1 Token, integrity, groups and impersonation

~~~cmd
whoami /all
whoami /priv
whoami /groups
net localgroup administrators
net localgroup "Remote Management Users"
net localgroup "Backup Operators"
~~~

| Privilege / context | Candidate mechanism and prerequisite |
| --- | --- |
| SeImpersonatePrivilege | A service-context token may impersonate a suitably privileged client; requires a compatible impersonation flow and OS |
| SeAssignPrimaryTokenPrivilege | Token assignment with a compatible process/token creation path |
| SeBackupPrivilege | Backup-aware reading despite ordinary file DACLs; not arbitrary code execution by itself |
| SeRestorePrivilege | Restore-aware writes/ownership operations; verify exact privilege and target |
| SeTakeOwnershipPrivilege | Taking ownership of a protected object may permit further ACL changes; ownership alone is not execution |
| SeDebugPrivilege | Access to other processes subject to protection levels; investigate PPL restrictions |
| SeLoadDriverPrivilege | Driver-loading rights and signing policy; high-risk, kernel-specific |
| SeManageVolumePrivilege | Volume-management functionality; version/filesystem dependent |
| Administrator group (deny-only) | Filtered UAC token; membership is not the same as elevated execution |

Historical lab tools include PrintSpoofer, GodPotato, JuicyPotato, RoguePotato and similar impersonation demonstrations. Do not treat them as interchangeable: match Windows build, service account, required privilege, RPC/COM or named-pipe mechanism, architecture, mitigations and any network prerequisites. JuicyPotato's traditional approach is not appropriate for newer Windows builds. The [OffSec exam FAQ](https://help.offsec.com/hc/en-us/articles/4412170923924-OSCP-Exam-FAQ) explicitly lists PrintSpoofer among examples of permitted tools, subject to restrictions; that does not certify every other tool or feature.

UAC: distinguish a standard user from a local administrator with a filtered token. An authorized administrator can request normal elevation; a UAC bypass generally assumes existing administrator membership and is not equivalent to escalating an arbitrary standard user. Check actual integrity and elevated identity.

### 8.2 Service object permissions, binary replacement and registry ACLs

~~~cmd
sc.exe qc ExampleService
sc.exe queryex ExampleService
sc.exe sdshow ExampleService
icacls "C:\Lab\ExampleService\service.exe"
icacls "C:\Lab\ExampleService"
~~~

~~~powershell
Get-CimInstance Win32_Service |
    Select-Object Name,StartName,PathName,StartMode,State
$key = 'HKLM:\SYSTEM\CurrentControlSet\Services\ExampleService'
Get-Acl -Path $key | Format-List Owner,AccessToString
Get-ItemProperty -Path $key | Select-Object ImagePath,ObjectName,Start
~~~

Check distinct security boundaries: the SCM service object DACL, registry key DACL, binary file DACL, parent directory, and any DLL/configuration or scripts it consumes.

| Finding | Why it matters |
| --- | --- |
| SERVICE_CHANGE_CONFIG (SDDL DC) | May allow changing the executable the service runs |
| WRITE_DAC (WD) / WRITE_OWNER (WO) | May allow modifying the service object's access rights |
| SERVICE_START (RP) / SERVICE_STOP (WP) | Can help trigger a confirmed change; not escalation alone |
| Writable service executable | Privileged service may run altered code |
| Writable executable parent directory | File replacement may be possible even with protected file ACL |
| Writable service registry key | Relevant configuration may be modifiable; confirm what SCM actually consumes and when |

Optional [AccessChk](https://learn.microsoft.com/en-us/sysinternals/downloads/accesschk) checks:

~~~cmd
accesschk.exe -accepteula -uwcqv "%USERNAME%" *
accesschk.exe -accepteula -qv "%USERNAME%" "C:\Lab\ExampleService"
~~~

Use actual account/group and inspect the specific service. Do not confuse service access rights with filesystem permissions. Microsoft describes the rights in [Service Security and Access Rights](https://learn.microsoft.com/en-us/windows/win32/services/service-security-and-access-rights).

**Disposable lab validation:** use a deliberately vulnerable test service configured to run as LocalSystem. Establish which exact file/configuration your user can change. Use a harmless service-compatible test binary that writes the effective identity to a dedicated lab log; trigger only via the permitted test service, verify the log and restore the original configuration/binary. A normal console EXE may cause error 1053 even if it executes, because SCM expects a service entry point. Avoid changing system services or using a persistent admin account as proof. If a lab requires a shell, verify its actual interactive token separately.

### 8.3 Unquoted service paths

~~~powershell
Get-CimInstance Win32_Service | Where-Object {
    $_.PathName -and $_.PathName -notmatch '^\s*"' -and
    $_.PathName -match '(?i)^.*?\s+.*?\.exe'
} | Select-Object Name,StartName,PathName,StartMode
~~~

This is a candidate filter, not a parser or vulnerability detector; arguments may produce false positives. For an observed image path such as C:\Program Files\Example App\service.exe (unquoted), possible earlier executable candidates can include C:\Program.exe and C:\Program Files\Example.exe. Check actual Windows executable parsing, whether candidates already exist, writable parent directories and the service account.

~~~cmd
icacls C:\
icacls "C:\Program Files"
icacls "C:\Program Files\Example App"
sc.exe qc ExampleService
~~~

Both a writable candidate path and a higher-privileged service start are needed. A quoted executable followed by unquoted arguments is not this vulnerability. Do not place test executables at global paths such as C:\Program.exe on shared systems. Use an isolated training service.

### 8.4 DLL hijacking, search order, PATH and COM

~~~powershell
Get-Process | Select-Object Name,Id,Path -ErrorAction SilentlyContinue
[Environment]::GetEnvironmentVariable('Path','Machine') -split ';'
[Environment]::GetEnvironmentVariable('Path','User') -split ';'
Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager' |
    Select-Object SafeDllSearchMode
~~~

Use [Process Monitor](https://learn.microsoft.com/en-us/sysinternals/downloads/procmon) when permitted in a disposable lab: filter by the actual service/process, file operations, paths ending in .dll, and NAME NOT FOUND results. Capture successful loads too. A missing DLL is only a lead.

- DLL side-loading/search-order hijacking: confirm the process searches a writable location for the exact DLL and that the DLL is actually loaded. KnownDLLs, manifests, package dependencies, absolute paths and safe loading flags can change resolution.
- PATH executable hijacking: privileged application calls a relative executable and includes an attacker-writable directory in its actual search path; inspect machine vs process/user PATH.
- COM registration: check relevant HKLM/HKCU Software\Classes\CLSID entries, InprocServer32/LocalServer32 paths, bitness and actual caller. Per-user registrations are not necessarily used by elevated processes.
- Application plugins, update agents and interpreters: inspect the privileged consumer, plugin directory and ACLs.
- DLL proxying: a replacement may require correct architecture, exports and initialization; verify in a lab with a harmless marker rather than breaking dependencies.

A 32-bit process on 64-bit Windows may see different system directories and registry views. See [Microsoft DLL search order](https://learn.microsoft.com/en-us/windows/win32/dlls/dynamic-link-library-search-order).

### 8.5 Scheduled tasks, autoruns and startup folders

~~~cmd
schtasks /query /fo LIST /v
schtasks /query /tn "\ExampleTask" /xml
reg query "HKLM\Software\Microsoft\Windows\CurrentVersion\Run"
reg query "HKLM\Software\Microsoft\Windows\CurrentVersion\RunOnce"
icacls "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup"
~~~

~~~powershell
Get-ScheduledTask | ForEach-Object {
    $t = $_
    foreach ($a in $t.Actions) {
        [pscustomobject]@{
            Task = $t.TaskPath + $t.TaskName
            User = $t.Principal.UserId
            RunLevel = $t.Principal.RunLevel
            Execute = $a.Execute
            Arguments = $a.Arguments
            WorkingDirectory = $a.WorkingDirectory
        }
    }
} | Format-Table -Wrap
~~~

Check the task principal, trigger, action, script and interpreter permissions, working directory and task registration ACL (not just the task XML file). A SYSTEM task executing a user-writable script is high priority. A task with HighestAvailable still depends on its principal's privileges. HKCU Run and a user's startup folder usually execute as that same user. HKLM Run is not automatically SYSTEM. Use [Autoruns](https://learn.microsoft.com/en-us/sysinternals/downloads/autoruns) for broader enumeration; inspect the actual account and consumer, not just whether an entry exists.

### 8.6 Registry and installer policy: AlwaysInstallElevated

~~~cmd
reg query "HKLM\Software\Policies\Microsoft\Windows\Installer" /v AlwaysInstallElevated
reg query "HKCU\Software\Policies\Microsoft\Windows\Installer" /v AlwaysInstallElevated
~~~

Both values must normally be 1 for the classic unsafe policy to apply to the current user. One enabled value alone is not evidence of an elevated installation. Confirm Windows Installer policy and application-control restrictions. In a disposable lab with both values enabled, a known benign test MSI can demonstrate its actual installation context; do not install an arbitrary package on production systems. See [Microsoft AlwaysInstallElevated](https://learn.microsoft.com/en-us/windows/win32/msi/alwaysinstallelevated).

Other registry leads: service ImagePath and Parameters\ServiceDll, machine-wide startup entries, IFEO debugger configuration, COM registrations and application-specific plugin or update settings. Check SetValue/CreateSubKey/WriteDac/WriteOwner rights and actual privileged use. Read access or write access to one's own HKCU is not a boundary crossing. Review the 32/64-bit views when applicable.

### 8.7 Credential and application configuration inventory

Use the expanded PuTTY section above as the pattern: identify the installed product, inspect relevant configuration paths and ACLs, distinguish identity references from secrets, and verify any allowed credential use only on assigned systems.

| Candidate | Common location / context | Interpretation |
| --- | --- | --- |
| PuTTY / Pageant | HKCU\Software\SimonTatham\PuTTY, configured .ppk | Session and key references; SSH passwords not normally saved |
| WinSCP | HKCU\Software\Martin Prikryl\WinSCP 2 or WinSCP.ini | Saved connection/configuration; storage depends on configuration |
| FileZilla | %APPDATA%\FileZilla | Site and recent-server settings; inspect ACL and version |
| RDP | HKCU\Software\Microsoft\Terminal Server Client; .rdp files | Destination or username hints; saved credentials are separate |
| Credential Manager | cmdkey /list | Target and username metadata, not plaintext credentials |
| PowerShell history | PSReadLine history path | May contain sensitive command arguments; keep private |
| Unattended setup | C:\Windows\Panther, C:\Windows\System32\Sysprep | Answer-file ACLs and deployment leftovers |
| IIS / web apps | C:\inetpub\wwwroot, web.config, application config | App identity and config permissions; secrets may be encrypted |
| Deployment and backup tools | C:\ProgramData, vendor folders, backup scripts | Privileged task or service may consume editable config |
| OpenSSH | %USERPROFILE%\.ssh; C:\ProgramData\ssh | Identity/key references and service configuration |
| VNC / remote support | Vendor-specific registry/config directories | Version-specific storage and ACLs; no universal decoder |
| KeePass / password databases | Authorized profile/document locations, .kdbx | Database existence is not access to its contents |

~~~powershell
Get-Command Get-PSReadLineOption -ErrorAction SilentlyContinue
if (Get-Command Get-PSReadLineOption -ErrorAction SilentlyContinue) {
    $history = (Get-PSReadLineOption).HistorySavePath
    if (Test-Path $history) { Get-Item -LiteralPath $history | Select FullName,Length }
}
$locations = @('C:\Windows\Panther','C:\Windows\System32\Sysprep','C:\inetpub\wwwroot','C:\ProgramData',"$env:APPDATA\FileZilla","$HOME\.ssh")
foreach ($d in $locations) {
    if (Test-Path -LiteralPath $d) {
        Get-ChildItem -LiteralPath $d -Force -ErrorAction SilentlyContinue |
            Select-Object FullName,Mode,LastWriteTime
    }
}
~~~

~~~cmd
cmdkey /list
reg query "HKCU\Software\Microsoft\Terminal Server Client\Servers"
~~~

Additional leads: Winlogon automatic-logon settings, legacy deployment XML, service-account configuration, configuration backups, saved database connections, local password-reuse risks, DPAPI-protected data and browser storage. Record metadata and protection boundaries; do not indiscriminately dump LSASS, SAM, SECURITY, browser vaults or profile data. DPAPI protection, profile scope, key encryption and credential restrictions matter. A discovered credential or administrator name is not a successful privilege change.

If a lab supplies an authorized credential for another account, use normal authentication, then repeat whoami /all. For AD-only relationships see [AD attack paths](../05-Active-Directory/ad-attack-paths.md). Lateral movement is not automatically local escalation.

### 8.8 Local groups, shares and application trust boundaries

~~~cmd
net localgroup
net share
netstat -ano
tasklist /svc
~~~

~~~powershell
Get-LocalGroup | Select-Object Name,Description
Get-SmbShare -ErrorAction SilentlyContinue | Select-Object Name,Path
Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Select-Object LocalAddress,LocalPort,OwningProcess
~~~

Review groups such as Backup Operators, Server Operators (on appropriate servers/DCs), Print Operators, Hyper-V Administrators, and service-specific groups. Membership is a lead, not blanket administrator access; effective rights, role and OS matter. Review writable SMB shares consumed by higher-privileged processes, loopback admin interfaces, named pipes, local databases and RPC services. Use a specific authorized application function, not broad guessing.

### 8.9 Installed software, OS builds and historical CVEs

~~~powershell
Get-CimInstance Win32_OperatingSystem |
    Select-Object Caption,Version,BuildNumber,OSArchitecture
Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion' |
    Select-Object ProductName,DisplayVersion,CurrentBuild,UBR
Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 20
$uninstall = @(
 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
 'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*',
 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*'
)
Get-ItemProperty -Path $uninstall -ErrorAction SilentlyContinue |
    Select-Object DisplayName,DisplayVersion,Publisher,InstallLocation
~~~

| Historical example | Research preconditions |
| --- | --- |
| PrintNightmare (CVE-2021-34527) | Spooler role, updates and relevant policy; do not assume remote or local applicability |
| HiveNightmare / SeriousSAM (CVE-2021-36934) | Affected build, sensitive-file ACL and applicable shadow copies |
| CLFS (CVE-2023-28252) | Exact affected Windows build and vendor update status |
| Other kernel/driver LPEs | Driver version, architecture, build, signing, HVCI and mitigations |
| Third-party service/update software | Exact vendor release and actual vulnerable component/configuration |

Get-HotFix is not a complete update inventory. Use the [Microsoft Security Update Guide](https://msrc.microsoft.com/update-guide) and vendor advisories. Prefer verified configuration flaws before kernel exploitation. Historical exploit availability is not proof a modern build is affected; do not disable endpoint protection to make a candidate work. Use snapshots for potentially unstable lab research.

### 8.10 Tools, manual validation and exam proof

- [WinPEAS](https://github.com/peass-ng/PEASS-ng) and [PowerUp](https://github.com/PowerShellMafia/PowerSploit): enumeration functions can generate leads; review each function and avoid automatic exploitation.
- [Sysinternals](https://learn.microsoft.com/en-us/sysinternals/): AccessChk, Autoruns, Process Monitor and Process Explorer help verify permissions and actual process behavior.
- [LOLBAS](https://lolbas-project.github.io/): legitimate binary behavior reference; running a signed binary is not automatically escalation.
- Check the current [OffSec exam guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide) and FAQ for restrictions. Do not use AI chatbots during the exam/reporting or forbidden automatic exploitation features.

~~~cmd
whoami
whoami /all
hostname
ipconfig
~~~

For full Windows target credit, OffSec requires an interactive shell with SYSTEM, Administrator or administrator privileges. Confirm the effective token, not merely an Administrators group listing. Read assigned proof files from their original locations using type, include the target IP in the required screenshot, submit the value in the control panel and document the exact path. Keep exam and target-specific evidence private.

### 8.11 Expanded checklist

- [ ] Identity, groups, integrity, UAC and token privileges.
- [ ] Service object DACL, binary and parent ACLs, registry key and run-as identity.
- [ ] Unquoted paths, DLL loading, executable search path, COM and plugins.
- [ ] Scheduled task principal/action, startup entries and privileged scripts.
- [ ] AlwaysInstallElevated and machine-wide registry permissions.
- [ ] PuTTY, WinSCP, RDP, FileZilla, SSH, Credential Manager and app configuration leads.
- [ ] Privileged groups, shares, management software, named pipes and local listeners.
- [ ] Exact Windows and third-party package builds; vendor-confirmed CVEs.
- [ ] Manually verify prerequisite, elevated consumer and trigger; restore authorized test changes.
- [ ] Confirm elevated shell and capture required evidence privately.

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

- [OffSec PEN-200 learning plan](https://help.offsec.com/hc/en-us/articles/15541765522196-OffSec-PEN-200-Learning-Plan-12-Week)
- [OffSec OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide)
- [Microsoft Windows commands](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/windows-commands)
- [Microsoft Learn: Sysinternals](https://learn.microsoft.com/en-us/sysinternals/)
