# Nmap Enumeration — OSCP Step-by-Step Methodology

> **Scope:** Use these commands only on assigned exam machines, authorized labs, or explicitly permitted targets.
>
> **Previous step:** [Host Discovery](./host-discovery.md)
>
> **Goal:** Discover TCP and UDP services, identify versions, investigate possible weaknesses, and record actionable next steps.

## Quick workflow

1. Confirm the target and VPN route.
2. Scan **all 65,535 TCP ports**.
3. Scan the **top 100 UDP ports**, expanding as necessary.
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
sudo nmap -Pn -sS -p- --min-rate 1000 --reason -oA scans/tcp-all "$IP"
```

| Option | Meaning |
| --- | --- |
| `-Pn` | Skip host discovery |
| `-sS` | TCP SYN scan |
| `-p-` | Scan TCP ports 1–65535 |
| `--min-rate 1000` | Request a minimum probe rate; reduce on unreliable links |
| `--reason` | Show evidence behind port states |
| `-oA` | Save `.nmap`, `.gnmap`, and `.xml` outputs |

**Interpretation:**
- `open`: A service responded as listening.
- `closed`: The host responded but the port is not listening.
- `filtered`: Nmap cannot determine the state due to filtering or lack of response.

### Extract open TCP ports automatically

```bash
PORTS=$(python3 - <<'PY'
import xml.etree.ElementTree as ET
root = ET.parse("scans/tcp-all.xml").getroot()
ports = sorted({
    int(p.attrib["portid"])
    for p in root.findall(".//port")
    if p.attrib.get("protocol") == "tcp"
    and (p.find("state") is not None)
    and p.find("state").attrib.get("state") == "open"
})
print(",".join(map(str, ports)))
PY
)
echo "Open TCP ports: $PORTS"
```

If the variable is empty, check the target IP, routing, VPN, scan results, and packet loss before proceeding. Do **not** run the next command with an empty `PORTS` variable.

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

UDP scans can be much slower than TCP scans. `open|filtered` means Nmap cannot distinguish an open port from a filtered one; it is **not** a confirmed open port.

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
- [ ] Scan at least the top 100 UDP ports.
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
- [Nmap Service and Version Detection](https://nmap.org/book/man-version-detection.html)
- [Nmap Scripting Engine](https://nmap.org/book/man-nse.html)
- [SearchSploit](https://www.exploit-db.com/searchsploit)

---

**Previous:** [Host Discovery](./host-discovery.md)  
**Next:** [Service-Specific Enumeration](./service-enumeration.md)
