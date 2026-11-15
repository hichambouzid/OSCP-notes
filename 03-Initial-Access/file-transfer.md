# HTTP and File Transfer — OSCP Lab Command Sheet

> Scope: explicitly assigned lab machines only. Keep source files, tools and lab evidence private. This chapter is about transferring authorized files and checking connectivity, not assuming that any file transfer grants code execution.

## 0. Choose the direction

| Need | Method |
| --- | --- |
| Kali → Linux target | Temporary HTTP server + curl/wget, or authorized SCP |
| Kali → Windows target | Temporary HTTP server + Invoke-WebRequest or curl.exe |
| Authorized SSH client → server | SCP/SFTP when the account has access |
| Target → Kali | Exam download exception only; see below |
| Target cannot reach Kali | Check actual routes; use an authorized SSH forward if appropriate |

**Exam restriction:** [OffSec's OSCP+ guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide) prohibits downloading applications, files or source code from exam machines to Kali unless necessary to compromise an exam machine. Delete permitted downloads after completing objectives. This is not a general permission to copy credentials, files or entire shares. Retain required screenshots and report evidence privately. Never upload target-specific data to public Git or external services.

## 1. Start an HTTP server on Kali

Open a dedicated Kali terminal. Find the VPN interface/address and choose the IP reachable from the assigned target. The address below is illustrative.

~~~bash
ip -br addr
ip route get 192.168.56.101
export LHOST=192.168.45.219
export HTTP_PORT=8000
mkdir -p "$HOME/oscp-local/transfer"
printf 'authorized transfer test\n' > "$HOME/oscp-local/transfer/test.txt"
python3 -m http.server "$HTTP_PORT" --bind "$LHOST" --directory "$HOME/oscp-local/transfer"
~~~

The process stays in the foreground. Do not start it from your home directory, Git checkout or an evidence directory. It provides no authentication and may expose directory listings. Use a dedicated directory with only intended files; do not put credentials, keys, hashes or reports there. If you are practicing on one machine only, bind to 127.0.0.1 instead.

In a second Kali terminal (set the same variables again if this is a fresh shell):

~~~bash
export LHOST=192.168.45.219
ss -lntp | grep ':8000'
curl -f "http://$LHOST:8000/test.txt"
sha256sum "$HOME/oscp-local/transfer/test.txt"
~~~

Expected: the file contains the marker and the server log records a GET with status 200. A local request proves the HTTP server works locally, not that the target can reach it.

## 2. Download to an authorized Linux machine

Run on the assigned Linux target, not Kali. Replace the sample IP and port.

~~~bash
curl -f --connect-timeout 10 -o /tmp/oscp-test.txt http://192.168.45.219:8000/test.txt
cat /tmp/oscp-test.txt
sha256sum /tmp/oscp-test.txt
~~~

Alternative if curl is missing:

~~~bash
wget -O /tmp/oscp-test.txt http://192.168.45.219:8000/test.txt
~~~

Compare the checksum to the original. A successful HTTP response does not execute a file. Use only appropriate approved tools, verify their provenance and architecture, and do not blindly execute a downloaded file.

## 3. Download to an authorized Windows machine

PowerShell:

~~~powershell
$uri = 'http://192.168.45.219:8000/test.txt'
$out = Join-Path $env:TEMP 'oscp-test.txt'
Invoke-WebRequest -Uri $uri -OutFile $out
Get-Content -LiteralPath $out
Get-FileHash -LiteralPath $out -Algorithm SHA256
~~~

On Windows PowerShell 5.1, use -UseBasicParsing if the legacy HTML parser causes a problem. In Windows CMD or PowerShell, when the actual curl.exe binary is available:

~~~cmd
curl.exe -f -o "%TEMP%\oscp-test.txt" http://192.168.45.219:8000/test.txt
type "%TEMP%\oscp-test.txt"
~~~

The CMD example uses CMD environment-variable expansion. In PowerShell use $env:TEMP and Join-Path, not %TEMP%. Older Windows builds may not include curl.exe. PowerShell's curl alias is not necessarily the real curl client.

## 4. SSH file transfer with an approved account

If the assigned host already has SSH access, encrypted SSH file transfer avoids exposing an unauthenticated HTTP directory.

~~~bash
# Kali → authorized remote account
scp -P 22 "$HOME/oscp-local/transfer/test.txt" student@192.168.56.101:/tmp/oscp-test.txt
~~~

Replace port, identity and destination with actual authorized values. Verify the server host key and the destination's write permissions; SCP -P is uppercase. SFTP is another option if the server supports it. Target-to-Kali transfers are subject to the exam rule in section 0.

## 5. Troubleshoot HTTP before changing anything

| Symptom | Check |
| --- | --- |
| Connection refused | Server running, correct bind address and port |
| Timeout | VPN route, target egress, firewall, actual reachable Kali IP |
| 404 | File is not in the served directory, wrong path or case |
| 403 / permission error | File and destination permissions |
| Address already in use | Check ss -lntp; choose another free port |
| Unexpected HTML instead of file | Wrong server, redirect, proxy or error page |
| File is corrupted | Check size and SHA256 at both ends |
| Target has no direct route | Verify an authorized tunnel or SSH transfer is available; see [Pivoting](../07-Pivoting/pivoting-tunneling.md) |

Linux target connectivity: ip route; ip route get 192.168.45.219; curl -v --connect-timeout 5 http://192.168.45.219:8000/test.txt

Windows target connectivity: Test-NetConnection 192.168.45.219 -Port 8000; route print

Stop the server with Ctrl+C, remove only your own temporary test files, and record which transfer was necessary. Do not leave unauthenticated listeners running.

## References

- [Python http.server documentation](https://docs.python.org/3/library/http.server.html)
- [OpenSSH scp manual](https://man.openbsd.org/scp)
- [PowerShell Invoke-WebRequest](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/invoke-webrequest)
- [OffSec OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide)

**Next:** [Initial Access](./initial-access.md) · [Pivoting](../07-Pivoting/pivoting-tunneling.md)
