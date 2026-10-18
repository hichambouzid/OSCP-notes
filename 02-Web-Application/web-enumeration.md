# Web Application Enumeration — OSCP Practical Workflow

> **Scope:** Authorized OSCP labs and explicitly permitted targets only. Start with a web service already discovered during [service enumeration](../01-Enumeration/service-enumeration.md).
>
> **Objective:** Map the application's hostnames, routes, technologies, authentication, exposed content and likely weaknesses before attempting exploitation.

## 0. Prepare and establish the correct URL

```bash
export IP=192.168.56.101  # Replace with assigned target
export URL="http://$IP:80" # Change scheme and port to match Nmap
mkdir -p scans/web evidence/web
curl -i "$URL/"
```

Check the response status, `Location` redirects, cookies, page title, and any hostname mentioned in HTML or TLS certificates. If the lab provides a hostname, add it to `/etc/hosts` and use the hostname as your URL. Do not assume HTTP is always on 80 or HTTPS on 443.

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

## 4. Identify virtual hosts and hostnames

Look for hostnames in redirects, HTML, certificates and DNS results. When an in-scope hostname is found, map it locally:

```bash
echo "$IP app.example.lab" | sudo tee -a /etc/hosts
curl -i "http://app.example.lab/"
```

Replace `app.example.lab` with a hostname grounded in your lab. Do not invent or scan unrelated domains.

For authorized virtual-host discovery, test the `Host` header against the assigned IP. For example, with ffuf and an approved subdomain wordlist:

```bash
ffuf -w /path/to/authorized-wordlist.txt -u "http://$IP/" -H "Host: FUZZ.example.lab" -rate 20 -of json -o scans/web/vhosts.json
```

Replace the wordlist and base domain. **Filter by response size/words only after measuring the default response**, since many applications return identical pages for unknown hosts.

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

## 10. Troubleshooting

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

## 11. Evidence template

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

- [ ] Confirm correct IP, hostname, scheme and port.
- [ ] Fingerprint headers, application and technologies.
- [ ] Explore manually before automated content discovery.
- [ ] Inspect robots.txt, sitemap and linked JavaScript.
- [ ] Discover directories/files with a controlled request rate.
- [ ] Check for wildcard responses and misleading status codes.
- [ ] Investigate in-scope virtual hosts.
- [ ] Review authentication and session behavior.
- [ ] Enumerate APIs and parameters.
- [ ] Review uploads/downloads using harmless test files.
- [ ] Research relevant advisories and validate potential findings.
- [ ] Save sanitized evidence and next actions.

## References

- [OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [OWASP Testing Guide — Information Gathering](https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/)
- [Nmap NSE Documentation](https://nmap.org/book/man-nse.html)
- [PortSwigger Web Security Academy](https://portswigger.net/web-security)

---

**Previous:** [Service-Specific Enumeration](../01-Enumeration/service-enumeration.md)
