# SMBClient — OSCP Practical Cheat Sheet

> Scope: assigned OSCP targets and authorized practice labs only. Use the actual target/share and known authorized credentials. Examples are illustrative. Do not commit credentials, raw files, keys or proof screenshots to public Git. See the [OffSec exam guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide) for restrictions on downloading target files during the exam.

## 1. Install and identify SMB

~~~bash
sudo apt install smbclient
smbclient --version
export IP=192.168.56.101    # Replace with assigned lab target
nmap -Pn -sV -p 139,445 "$IP"
nmap -Pn -p 445 --script smb-protocols,smb2-security-mode "$IP"
~~~

SMB commonly uses TCP 445; legacy NetBIOS session service uses TCP 139. SMBClient is the Samba suite's file-share client and works against both Windows and Linux Samba servers. It is not a remote shell or an SMB exploit.

## 2. Authentication and listing shares

~~~bash
smbclient -L "$IP" -N                        # No password supplied
smbclient -L "$IP" -U 'guest' -N             # Explicit guest identity
smbclient -L "$IP" -U 'username'            # Prompt for password
smbclient -L "$IP" -U 'DOMAIN/username'     # Domain identity
smbclient -L "$IP" -U 'HOSTNAME/username'   # Local account on named Windows host
smbclient -L "$IP" -U 'username' -W DOMAIN  # Alternative domain selection
~~~

-N suppresses the password prompt; it does not guarantee a null session or guest access. If no username is specified the client may use your current local username. A failed list does not necessarily mean every known share is inaccessible. Try a specific in-scope share if its name is known from other evidence. Do not brute-force authentication or repeatedly retry invalid credentials.

### Example share types

| Name | What to check |
| --- | --- |
| ADMIN$, C$, D$ | Administrative shares, ordinarily require appropriate administrator rights |
| IPC$ | Named-pipe/RPC service, not a regular file share |
| NETLOGON | Domain logon scripts on domain controllers |
| SYSVOL | Domain policy and scripts on domain controllers |
| Public, Documents, Backup, Users | Illustrative custom shares; inspect actual ACLs and purpose |

A share name ending in $ is hidden from normal browsing, not a permission bypass. Enumeration output is not proof of access.

## 3. Connect to a share

~~~bash
smbclient "//$IP/Backup" -N
smbclient "//$IP/Backup" -U 'DOMAIN/username'
smbclient "//$IP/Shared Documents" -U 'username'
smbclient "//$IP/C\$" -U 'HOSTNAME/administrator'
smbclient "//$IP/NETLOGON" -U 'DOMAIN/username'
smbclient "//$IP/SYSVOL" -U 'DOMAIN/username'
~~~

Replace share names with real results. The administrative-share example is only for an explicitly supplied authorized administrator account; it does not elevate your privileges. Enter passwords interactively rather than putting them in shell history, process arguments or public notes. Passwordless access may be guest-mapped rather than authenticated as the requested user.

## 4. Interactive commands (smb: prompt)

| Command | Purpose |
| --- | --- |
| help or ? | List supported client commands |
| help get | Explain a command |
| pwd | Current remote working directory |
| ls / dir | List remote entries |
| ls *.txt | List matching remote files |
| cd Documents | Change remote directory |
| cd .. | Go to parent directory |
| cd \ | Go to root of the current share |
| lcd | Show local working directory |
| lcd /absolute/local/path | Change local working directory |
| ! pwd | Run pwd locally, not on the target |
| ! ls -la | List files locally |
| allinfo report.txt | Request remote file metadata |
| more readme.txt | Retrieve and view a remote file through local pager |
| get report.txt | Download one file to the local working directory |
| get "report 2026.txt" local-report.txt | Download and rename the local copy |
| mget *.txt | Download matching files |
| put note.txt remote-note.txt | Upload one local file (requires write access) |
| mput *.txt | Upload matching local files |
| mkdir LabTest | Create a remote folder (requires permission) |
| rename old.txt new.txt | Rename a remote file |
| del note.txt | Delete matching remote file(s); use exact name only for your own test file |
| rmdir LabTest | Remove an empty remote directory |
| recurse | Toggle recursive multi-file transfers |
| prompt | Toggle per-file confirmation for multi-file transfers |
| mask *.txt | Set filename filter for recursive transfers |
| du | Display share usage information when supported |
| exit / quit | Close the connection |

Commands are entered at the SMB prompt, not the Kali shell. Double-quote paths containing spaces. Remote operations are constrained by server implementation and permissions. Avoid destructive commands against existing target files. Local shell escape (!) runs on Kali, not the remote host.

## 5. Download a selected file

On Kali, create a private workspace (outside your public repository):

~~~bash
umask 077
mkdir -p "$HOME/oscp-local/$IP/smb"
cd "$HOME/oscp-local/$IP/smb"
smbclient "//$IP/Backup" -U 'DOMAIN/username'
~~~

At the SMB prompt:

~~~text
pwd
ls
cd Documents
ls
get readme.txt
get "backup notes.txt" backup-notes.txt
exit
~~~

Back on Kali:

~~~bash
ls -la
file readme.txt
less readme.txt
sha256sum readme.txt
~~~

The local files are saved in the directory from which smbclient was started, unless you change it with lcd. Do not execute downloaded files. During the exam, download target files only when necessary to compromise the target under the current OffSec rules, remove them as required and keep permitted evidence private.

## 6. Multiple files and recursive transfers

In a disposable practice share, first inspect the directory and decide which files are needed:

~~~text
ls
mget *.txt
~~~

For a known, small, in-scope folder with text files in subdirectories, start a fresh SMBClient session (recursion is initially off; prompting is initially on):

~~~text
cd LabDocuments
recurse
mask *.txt
mget *
recurse
mask *
~~~

The command recurse toggles recursion, not an explicit on/off setting. During recursive mget, the mget wildcard selects directories and mask selects files; without recursion, mget's own wildcard selects files. Keep interactive confirmation enabled for selective downloads. In an isolated lab, prompt can toggle off confirmation, but toggle it back afterward. Avoid downloading entire shares or sensitive files unnecessarily, especially in an exam. Use lcd to choose a dedicated destination first.

## 7. Upload and validate write permission

Write access alone does not imply code execution or privilege escalation. In a practice share where you are authorized to create/delete a test file, use a unique, non-executable marker. Never overwrite or remove existing remote content.

Kali:

~~~bash
cd "$HOME/oscp-local/$IP/smb"
marker="oscp-write-$(date +%s)-$$.txt"
printf 'Authorized SMB write test\n' > "$marker"
smbclient "//$IP/Backup" -U 'DOMAIN/username' \
  -c "put $marker $marker; ls $marker"
~~~

Record the exact name. If successfully uploaded, delete only your marker when authorized:

~~~bash
smbclient "//$IP/Backup" -U 'DOMAIN/username' -c "del $marker"
~~~

For an interactive session use put local-filename remote-filename, then ls and del with that exact test filename. An upload failure may be caused by share ACL, NTFS/POSIX ACL, quota, read-only export or other controls. Do not change permissions to force access.

## 8. One-line commands and connection options

~~~bash
smbclient "//$IP/Backup" -N -c 'ls'
smbclient "//$IP/Backup" -U 'DOMAIN/username' -c 'cd Documents; ls'
smbclient "//$IP/Backup" -U 'DOMAIN/username' -D Documents -c 'ls'
smbclient -g -L "$IP" -N
smbclient -L "$IP" -N -p 445
smbclient -L "$IP" -N -p 139
smbclient -L HOSTNAME -I "$IP" -U 'DOMAIN/username'
smbclient "//$IP/Backup" -N -m SMB3 -c 'ls'
~~~

| Option | Meaning |
| --- | --- |
| -L | List shares on host |
| -N | Suppress password prompt |
| -U | User identity; DOMAIN/username supported |
| -W | Workgroup/domain |
| -c | Semicolon-separated commands, then exit |
| -D | Initial remote directory |
| -p | Destination TCP port |
| -I | Explicit destination IP, useful with a server name |
| -m | Maximum SMB dialect, not necessarily the negotiated dialect |
| -g | Machine-readable share list with -L |
| -d 3 | Debug detail; keep output private |
| -t 30 | Per-request timeout |
| -A | Authentication file; avoid plaintext files where possible |
| --client-protection=sign | Require signing on current clients |
| --client-protection=encrypt | Require encryption on current clients |

Check smbclient --help and the installed man page for supported options; old Samba releases differ. With modern Samba, an "SMB1 disabled -- no workgroup available" line following a successful share listing may refer only to legacy workgroup browsing, not a failed SMB2/3 connection.

Only if an isolated legacy lab is confirmed to support SMB1 exclusively, a per-command compatibility test is:

~~~bash
smbclient -L "$IP" -N -m NT1 --option='client min protocol=NT1'
~~~

SMB1 is obsolete and unsafe. Do not enable it globally or downgrade modern servers to make a connection succeed.

## 9. AD-specific authentication (when authorized)

~~~bash
smbclient -L dc01.example.test -U 'EXAMPLE/username'
smbclient //dc01.example.test/SYSVOL -U 'EXAMPLE/username'
~~~

For a lab-provided Kerberos identity, use the actual realm, correctly configured DNS and synchronized time. A hostname matching the SMB service principal is needed; an IP address generally cannot substitute for it.

~~~bash
kinit username@EXAMPLE.TEST
klist
smbclient //dc01.example.test/SYSVOL --use-kerberos=required -N -c 'ls'
~~~

Current Samba also supports --pw-nt-hash for an explicitly supplied authorized NT hash (not a plaintext password or NTLMv2 challenge response). Prefer a prompt rather than passing secrets as shell arguments:

~~~bash
smbclient "//$IP/Backup" -U 'DOMAIN/username' --pw-nt-hash
~~~

Enter the authorized NT hash at the password prompt. Success depends on NTLM being permitted, account rights and server policy. Never guess or reuse credentials outside the assigned scope. Check current exam rules before employing any credential-related technique.

## 10. OSCP workflow: from share to next investigation

1. Identify host, SMB dialect and signing configuration; list shares once with guest/no password and once with a known assigned account if appropriate.
2. Connect to relevant shares separately; record listing, read and write permissions independently.
3. Inspect accessible file names, timestamps, folder names and selected relevant files. Look for application configurations, deployment scripts, backups and documentation. Keep sensitive contents private.
4. A readable file containing a lab-relevant service identity is a lead, not proof of privilege. Confirm the intended host and user before any authorized authentication.
5. A writable share consumed by a privileged service/task may be relevant to [Windows privilege escalation](../04-Privilege-Escalation/windows-privesc.md) or [Linux privilege escalation](../04-Privilege-Escalation/linux-privesc.md); prove the real privileged consumer and actual permissions before drawing conclusions.
6. On a domain controller, NETLOGON and SYSVOL can contain legitimate scripts/policies readable by domain users. Inspect relevant assigned-domain records and refer to [AD enumeration](../05-Active-Directory/ad-enumeration.md).
7. SMBClient is for share access, not executing commands remotely. An administrative share does not by itself create a shell; use the separate authorized methodology if another objective requires it.

### Windows-side comparison (if you already have an authorized Windows shell)

~~~cmd
net view \\192.168.56.101
dir \\192.168.56.101\Backup
net use \\192.168.56.101\Backup /user:DOMAIN\username *
net use \\192.168.56.101\Backup /delete
~~~

The * requests an interactive password prompt. Windows may reject simultaneous connections to the same server under different accounts. Delete only your own test connection. These are Windows native commands, not smbclient commands.

## 11. Troubleshooting

| Output | Check |
| --- | --- |
| NT_STATUS_LOGON_FAILURE | Correct identity/domain and known authorized credential; avoid repeated attempts |
| NT_STATUS_ACCESS_DENIED | Share/underlying filesystem ACL, guest mapping, token or policy |
| NT_STATUS_BAD_NETWORK_NAME | Exact share name; connect to an actual share, not a directory name |
| NT_STATUS_OBJECT_NAME_NOT_FOUND | File path, spelling, current directory |
| NT_STATUS_CONNECTION_REFUSED / timeout | VPN, route, assigned IP, port and firewall |
| NT_STATUS_NOT_SUPPORTED / negotiation failure | SMB dialect, signing/encryption and client version |
| SMB1 disabled -- no workgroup available | If shares listed, legacy workgroup browse warning may be harmless |
| Kerberos errors | DNS, realm, clock, ticket validity and server hostname/SPN |
| put fails | Actual write permission, destination name, free space, file locks |
| get appears successful but file missing | lcd/local working directory, local permissions and file name |

Diagnostic example:

~~~bash
ip route get "$IP"
smbclient -L "$IP" -U 'DOMAIN/username' -d 3 -t 15
~~~

Do not share verbose debug logs without sanitizing them.

## 12. Quick copy-paste reference

~~~bash
smbclient -L "$IP" -N
smbclient -L "$IP" -U 'DOMAIN/username'
smbclient "//$IP/SHARE" -N
smbclient "//$IP/SHARE" -U 'DOMAIN/username'
smbclient "//$IP/SHARE" -U 'DOMAIN/username' -c 'ls'
~~~

At smb: prompt: ls -> cd -> ls -> get -> exit. Use lcd for the local destination and put only when authorized.

## References

- [Official Samba smbclient manual](https://www.samba.org/samba/docs/current/man-html/smbclient.1.html)
- [Service enumeration — SMB](service-enumeration.md#2-smb--windows-file-sharing-139445)
- [OffSec OSCP+ exam guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide)
