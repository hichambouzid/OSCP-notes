# Hands-on terminal drills — commands, results and troubleshooting

Run these on your own Linux/Kali machine before the exam. They use synthetic data and loopback only; they do not contact an exam target or perform exploitation. The objective is to develop muscle memory and understand command output.

## Drill 0 — automated local self-test (Python 3, no dependencies)

From the repository root:

~~~bash
python3 09-Lab-Writeups/local_drills.py
~~~

Expected output (POSIX/Linux):
~~~text
Original SHA-256: 5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03
Changed checksum differs: PASS
File mode 0600: PASS
GET / -> 200: PASS
GET /login -> 401: PASS
GET /private -> 403: PASS
GET /missing -> 404: PASS
All local drills passed; temporary files and server cleaned up.
~~~

The script starts an ephemeral server bound only to 127.0.0.1, disables proxy use for its local requests, tests file permissions and SHA-256 on dummy data, and cleans up automatically. On non-POSIX systems the permissions check is skipped. This is a pre-exam learning tool, not an exam attack tool.

## Drill 1 — HTTP client basics

Prerequisites: Python 3 and curl. Start a dedicated temporary directory and leave the first terminal open.

~~~bash
LAB_DIR=$(mktemp -d)
printf 'hello from local lab\n' > "$LAB_DIR/index.html"
printf 'Lab directory: %s\n' "$LAB_DIR"
python3 -m http.server 8765 --bind 127.0.0.1 --directory "$LAB_DIR"
~~~

In a second terminal:

~~~bash
curl --noproxy '*' -i http://127.0.0.1:8765/
curl --noproxy '*' -I http://127.0.0.1:8765/
curl --noproxy '*' -i http://127.0.0.1:8765/does-not-exist
ss -ltn | grep ':8765'
~~~

Expected:
- First request: HTTP 200, headers and the hello body.
- HEAD request: HTTP 200 and headers, without a body.
- Missing route: HTTP 404.
- Socket: local listener on 127.0.0.1:8765. The PID may not be shown by this command.

Interpretation: curl -i includes headers; -I sends HEAD. A listening socket is an observation about your local machine, not proof of remote reachability. The loopback bind prevents exposure on other interfaces.

Troubleshooting:
- Address already in use: choose a different unused high port, changing both server and client.
- Connection refused: verify the first terminal still runs and both commands use the same port.
- Proxy interference: --noproxy '*' ensures the loopback request stays local.
- Python not found: check command -v python3 and install from your distribution before the exam.

Cleanup: Ctrl+C in the server terminal, then:
~~~bash
rm -- "$LAB_DIR/index.html"
rmdir -- "$LAB_DIR"
~~~

## Drill 2 — file permissions and identity

~~~bash
LAB_DIR=$(mktemp -d)
id
printf 'synthetic private note\n' > "$LAB_DIR/note.txt"
chmod 600 "$LAB_DIR/note.txt"
ls -l "$LAB_DIR/note.txt"
stat -c '%a %U %n' "$LAB_DIR/note.txt"
chmod 640 "$LAB_DIR/note.txt"
stat -c '%a %U %n' "$LAB_DIR/note.txt"
rm -- "$LAB_DIR/note.txt"
rmdir -- "$LAB_DIR"
~~~

Expected: first permission mode 600 (owner read/write); second 640 (owner read/write, group read). Your username and temporary path vary. Mode bits do not show every ACL or effective permission; the owner, group, directory traversal and execution context matter.

Troubleshooting: stat -c is GNU/Linux syntax; macOS stat differs. Do not use sudo or modify unrelated files to make this drill work.

## Drill 3 — hashes versus passwords

~~~bash
LAB_DIR=$(mktemp -d)
printf 'hello\n' > "$LAB_DIR/sample.txt"
sha256sum "$LAB_DIR/sample.txt"
printf 'hello!\n' > "$LAB_DIR/sample.txt"
sha256sum "$LAB_DIR/sample.txt"
rm -- "$LAB_DIR/sample.txt"
rmdir -- "$LAB_DIR"
~~~

Expected: first checksum begins 5891b5b5; the second is different. Even one byte changes the checksum. An ordinary file digest is not a Kerberos service ticket or a password verifier. Do not select a password-auditing format based on length alone.

## Drill 4 — find the right note in seconds

From the repository root:

~~~bash
rg -n -i --glob '*.md' 'clock skew' .
rg -n -i --glob '*.md' 'proof' 08-Exam-Workflow
rg -l -i --glob '*.md' 'troubleshoot' .
~~~

If ripgrep is absent, use grep -Rin 'clock skew' . instead. Expected: matching file paths and line numbers (or just paths for rg -l). Search for a symptom, concept or command name, then read the surrounding context. Do not run a found command before understanding its scope and prerequisites.

## Drill 5 — evidence rehearsal with dummy files

~~~bash
LAB_DIR=$(mktemp -d)
date -Is > "$LAB_DIR/session.txt"
hostname >> "$LAB_DIR/session.txt"
id >> "$LAB_DIR/session.txt"
cat "$LAB_DIR/session.txt"
(cd "$LAB_DIR" && sha256sum session.txt > checksums.txt && sha256sum -c checksums.txt)
~~~

Expected: date, host and local identity, followed by session.txt: OK. A checksum detects changes relative to the recorded digest; it is not encryption or proof of privileged access. Take a practice screenshot of your terminal and write two sentences describing each observation. Actual exam evidence must follow the official rules.

Cleanup: rm -- "$LAB_DIR/session.txt" "$LAB_DIR/checksums.txt"; rmdir -- "$LAB_DIR"

## Drill 6 — Windows inspection on a Windows machine you own

Use PowerShell:
~~~powershell
whoami
whoami /all
Get-Location
Get-ChildItem -Force
Get-Date
Get-Help Get-ChildItem -Examples
$demo = Join-Path $env:TEMP ("oscp-demo-" + [guid]::NewGuid() + ".txt")
Set-Content -LiteralPath $demo -Value "synthetic note"
Get-Item -LiteralPath $demo
Get-Acl -LiteralPath $demo
Get-FileHash -LiteralPath $demo -Algorithm SHA256
Remove-Item -LiteralPath $demo
~~~

Expected: your own identity, local files, a newly created temporary file, its ACL and a SHA-256 digest. Output varies by machine and PowerShell version. No administrative privileges are required for these operations in your own temporary directory.

## Completion criteria

- [ ] Can explain each option without a walkthrough.
- [ ] Can distinguish HTTP 401, 403 and 404.
- [ ] Can read permission modes and explain identity versus authorization.
- [ ] Can explain a checksum without confusing it with a password hash.
- [ ] Can find the right reference in under a minute.
- [ ] Can preserve and verify dummy evidence.
- [ ] Can clean up all temporary practice files.

Continue with assigned PEN-200 exercises for the penetration-testing objectives. These drills do not substitute for those labs.

[Beginner desk reference](../00-Quick-Reference/beginner-desk-reference.md) · [Troubleshooting](../08-Exam-Workflow/troubleshooting-cards.md) · [Readiness](../08-Exam-Workflow/readiness-scorecard.md)
