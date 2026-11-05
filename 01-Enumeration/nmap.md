# Nmap Enumeration — OSCP Step-by-Step Methodology

> **Scope:** Use these commands only on assigned exam machines, authorized labs, or explicitly permitted targets.
>
> **Previous step:** [Host Discovery](./host-discovery.md)
>
> **Goal:** Discover TCP and UDP services, identify versions, investigate possible weaknesses, and record actionable next steps.

## Quick workflow

1. Confirm the target and VPN route.
2. Scan **all 65,535 TCP ports**.
3. Run an initial **top-100 UDP pass**, then decide whether targeted, top-1,000 or full-UDP expansion is needed; the first pass is **not comprehensive**.
4. Identify versions and run default Nmap scripts.
5. Select service-specific enumeration and vulnerability checks.
6. Research versions and CVEs; **manually validate** findings.
7. Save evidence and move to the relevant service checklist.

## Step 0 — Prepare

```bash
export IP=192.168.56.101  # Replace with your assigned target
mkdir -p scans
ip route get "$IP"
```

`-Pn` below skips host discovery for a **known assigned target**; it does not prove that the host is online.

## Step 1 — Find all open TCP ports

```bash
sudo nmap -Pn -n -sS -p- -T4 \
  --min-rate 300 \
  --max-retries 1 \
  --max-scan-delay 100ms \
  --open -v -oA scans/tcp-all "$IP"
```

| Option | Meaning |
| --- | --- |
| `-Pn` | Skip host discovery; does not prove target is online |
| `-n` | Do not perform reverse DNS resolution |
| `-sS -p-` | SYN scan across all 65,535 TCP ports |
| `-T4` | Aggressive timing template for reasonably reliable networks |
| `--min-rate 300` | Aim to send at least 300 probes/second; **not** a maximum |
| `--max-retries 1` | At most one retransmission per probe; faster but may miss services |
| `--max-scan-delay 100ms` | Cap adaptive scan delay; can miss rate-limited responses |
| `--open -v` | Display only open/possibly open ports and verbose scan progress |
| `-oA` | Save `.nmap`, `.gnmap` and `.xml` for later analysis |

**Fast discovery profile requested for the lab:** The timing and retry flags prioritize speed. `-p-` still sends probes to all TCP ports, **but `--max-retries 1` can miss an open port** if packets are lost or the host rate-limits responses. `--max-scan-delay 100ms` may also cap a delay Nmap needs to accommodate rate limiting. This is **not** an accuracy guarantee. If few/no ports appear, the VPN is unstable, or a known service is missing, run an accuracy-focused verification:

```bash
sudo nmap -Pn -n -sS -p- --reason -oA scans/tcp-verify "$IP"
```

Compare results and enumerate the **union of confirmed open ports** before concluding the host has no additional services. The user-supplied example IP `192.168.230.10` is represented here by `$IP` to keep the public notes reusable. See [Nmap Timing and Performance](https://nmap.org/book/man-performance.html).

**Interpretation:**
- `open`: A service responded as listening.
- `closed`: The host responded but the port is not listening.
- `filtered`: Nmap cannot determine the state due to filtering or lack of response.

### Extract open TCP ports automatically

```bash
# Use the .gnmap file written by -oA, AFTER the scan finishes
PORTS=$(grep -oE '[0-9]+/open/tcp' scans/tcp-all.gnmap \
  | cut -d/ -f1 | sort -nu | paste -sd, -)
echo "Open TCP ports: $PORTS"
```

If the variable is empty, confirm `scans/tcp-all.gnmap` exists and the scan has **completed**, check the current directory, target IP, routing, VPN, results and packet loss. If a verification scan found additional ports, add those ports to the list rather than relying on the first pass.  Do **not** run the next command with an empty `PORTS` variable.

## Step 2 — Scan UDP ports separately

**A TCP SYN scan does not scan UDP.** Start with common UDP ports:

```bash
sudo nmap -Pn -sU --top-ports 100 -oA scans/udp-top100 "$IP"
```

Expand when needed:

```bash
sudo nmap -Pn -sU --top-ports 1000 -oA scans/udp-top1000 "$IP"
```

For a complete UDP scan when time and scope allow:

```bash
sudo nmap -Pn -sU -p- -oA scans/udp-all "$IP"
```

UDP scans can be much slower than TCP scans. **A completed top-100 scan does NOT mean UDP enumeration is complete.** Use the top-100 results as a first pass; check common service-related UDP ports indicated by TCP/AD findings, and broaden to top 1,000 when leads are missing or UDP is relevant. Consider `-sU -p-` only when time, scope and the situation justify it. Keep broad scans scoped to assigned hosts and interpret `open|filtered` as inconclusive, **not** confirmed open. Use `-sV` or service-specific checks to investigate promising ports.

**Decision gate:** Before moving on, record whether UDP coverage was *top 100 only*, *top 1,000*, *targeted*, or *all*. If only top 100 was scanned, keep a visible follow-up task instead of marking UDP finished.

## Step 3 — Detect TCP services, versions and default script findings

Use the ports discovered in Step 1:

```bash
if [ -n "$PORTS" ]; then
  sudo nmap -Pn -sC -sV -p "$PORTS" -oA scans/tcp-services "$IP"
else
  echo 'No confirmed open TCP ports; review scan results first.'
fi
```

- `-sC`: run Nmap's default NSE scripts.
- `-sV`: detect service products and versions.

Example output:

```text
PORT    STATE SERVICE VERSION
22/tcp  open  ssh     OpenSSH
80/tcp  open  http    Apache httpd
445/tcp open  microsoft-ds
```

This output is illustrative; do not assume these services exist on your target.

**Next action:** Note each open port, identified service, possible version, and any unusual script output. Versions may be hidden, misleading, or backported.

## Step 4 — Detect versions on interesting UDP ports

Replace the example ports with relevant results:

```bash
sudo nmap -Pn -sU -sV -p 53,69,123,161 -oA scans/udp-services "$IP"
```

Common UDP services: DNS (53), TFTP (69), NTP (123), SNMP (161). Nonstandard ports are possible.

## Step 5 — Run targeted enumeration scripts

First review available scripts and their behavior:

```bash
nmap --script-help http-title
nmap --script-help smb-os-discovery
nmap --script-help snmp-info
```

Then select only scripts relevant to services actually found. Examples:

### HTTP on port 80

```bash
sudo nmap -Pn -p 80 --script http-title,http-headers -oA scans/http-info "$IP"
```

### SMB on port 445

```bash
sudo nmap -Pn -p 445 --script smb-os-discovery,smb2-security-mode -oA scans/smb-info "$IP"
```

### SNMP on UDP port 161

```bash
sudo nmap -Pn -sU -p 161 --script snmp-info -oA scans/snmp-info "$IP"
```

Scripts can require permissions or produce inconclusive results. Review their help and use them only where authorized.

## Step 6 — Investigate potential vulnerabilities

Start with the exact identified product, version, configuration, and exposed functionality.

```bash
searchsploit "OpenSSH"
searchsploit "Apache httpd"
```

Replace these broad examples with the actual discovered product and version. Cross-check with vendor security advisories and CVE details.

Nmap also provides vulnerability-check scripts. **Do not blindly run an entire script category:** individual scripts may be intrusive or disruptive.

```bash
nmap --script-help 'http-vuln*'
```

Choose a specific script only after reading its help, understanding its impact, and verifying that the target is in scope.

**Remember:** A SearchSploit result, old-looking banner, or NSE alert is a lead, **not proof** of a vulnerability. Check patch backports, prerequisites, affected configurations, and corroborating evidence.

## Step 7 — Decide what to enumerate next

| Discovered service | Follow-up questions |
| --- | --- |
| FTP (21) | Is anonymous access allowed? What files are exposed? |
| SSH (22) | What authentication methods and versions are supported? |
| DNS (53) | What records and authorized zone-transfer behavior exist? |
| HTTP/HTTPS (80/443) | What application, routes, virtual hosts and technologies are present? |
| SMB (139/445) | What shares, permissions, signing and domain details are exposed? |
| SNMP (161/UDP) | What authorized management information is available? |
| RDP (3389) | What certificate and security settings are presented? |

Always use the **detected service**, not just the port number. Applications often use nonstandard ports.

## Step 8 — Troubleshooting

| Problem | Response |
| --- | --- |
| Host appears down | Confirm IP, VPN, route; use `-Pn` for assigned targets |
| No open TCP ports | Check routing, filtering and packet loss; retry at a slower rate |
| Scan results differ | Rescan specific ports with `-T2 --reason` |
| Version is unknown | Inspect protocol responses manually; do not guess |
| UDP says `open\|filtered` | Use `-sV` or service-specific probes |
| No vulnerability script findings | Do not assume the service is secure |

Slower TCP verification example:

```bash
sudo nmap -Pn -sS -T2 --reason -p 22,80,443 "$IP"
```

## Step 9 — Record evidence

```text
Target: 192.168.56.101
TCP ports: 22, 80, 445
UDP: 161 open|filtered (requires verification)
Service: HTTP on TCP/80
Version: Not yet confirmed
Potential weakness: Under investigation
Evidence: scans/tcp-services.nmap
Next action: HTTP application enumeration
```

For every suspected issue, record the affected port, product/version, prerequisites, reference advisory/CVE, exact supporting evidence, and whether it is unverified, ruled out, or verified.

## OSCP checklist

- [ ] Confirm authorized target and routing.
- [ ] Run a full TCP port scan.
- [ ] Run an initial UDP pass and explicitly record its coverage; top 100 alone is not comprehensive.
- [ ] Decide whether to scan relevant UDP ports, top 1,000 or all UDP ports based on findings and time.
- [ ] If the fast scan is empty/inconsistent or known services are missing, run an accuracy-focused full-TCP rescan and check both outputs.
- [ ] Extract confirmed open TCP ports from the completed `.gnmap` output; include newly verified ports.
- [ ] Save all Nmap outputs.
- [ ] Extract open TCP ports.
- [ ] Run `-sC -sV` on discovered TCP ports.
- [ ] Investigate interesting UDP results.
- [ ] Run relevant, reviewed NSE scripts.
- [ ] Research software versions and CVEs.
- [ ] Manually validate suspected weaknesses.
- [ ] Enumerate each discovered service.
- [ ] Record findings and next actions.

## References

- [Nmap Port Scanning Techniques](https://nmap.org/book/man-port-scanning-techniques.html)
- [Nmap Port Specification](https://nmap.org/book/man-port-specification.html)
- [Nmap Timing and Performance](https://nmap.org/book/man-performance.html)
- [Nmap Service and Version Detection](https://nmap.org/book/man-version-detection.html)
- [Nmap Scripting Engine](https://nmap.org/book/man-nse.html)
- [SearchSploit](https://www.exploit-db.com/searchsploit)

---

**Previous:** [Host Discovery](./host-discovery.md)  
**Next:** [Service-Specific Enumeration](./service-enumeration.md)
