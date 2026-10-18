# Host Discovery — OSCP Field Guide

> **Objective:** Identify reachable hosts and validate connectivity in authorized OSCP labs and penetration tests.
>
> **Important:** A failed ping does **not** mean the host is offline. Always check routing and try alternate probes.

## Quick reference

| Goal | Command |
| --- | --- |
| Check interface and route | `ip -br addr; ip route get "$IP"` |
| ICMP echo | `ping -c 4 "$IP"` |
| Nmap host discovery | `sudo nmap -sn "$IP"` |
| Discover hosts in a scoped subnet | `sudo nmap -sn "$SUBNET"` |
| ICMP echo probes | `sudo nmap -sn -PE "$SUBNET"` |
| TCP SYN discovery | `sudo nmap -sn -PS22,80,443 "$IP"` |
| TCP ACK discovery | `sudo nmap -sn -PA80,443 "$IP"` |
| UDP discovery | `sudo nmap -sn -PU53,161 "$IP"` |
| Skip host discovery for a known target | `sudo nmap -Pn -p 22,80,443,445 "$IP"` |
| Local Ethernet ARP discovery | `sudo arp-scan -I eth0 --localnet` |

## 1. Prepare your environment

Use the **assigned** IP and subnet, not the example addresses:

```bash
export IP=192.168.56.101
export SUBNET=192.168.56.0/24
mkdir -p scans
ip -br addr
ip route
ip route get "$IP"
```

Confirm that the VPN is connected (often `tun0`) and that a route exists to the target. A VPN interface with an address does not by itself prove target reachability.

## 2. ICMP discovery

```bash
ping -c 4 "$IP"
sudo nmap -sn -PE "$IP"
```

- **Replies received:** the target address responded to ICMP.
- **100% packet loss:** could mean filtering, packet loss, routing issues, or an offline target; it is **not** proof the host is down.
- **TTL:** may hint at the OS (common initial values include 64 for Linux and 128 for Windows), but routing and configuration make this unreliable for identification.

Other ICMP probes:

```bash
sudo nmap -sn -PP "$IP"   # timestamp request
sudo nmap -sn -PM "$IP"   # address-mask request
```

These are frequently filtered. On local Ethernet, privileged Nmap may prefer ARP discovery; `--send-ip` can force IP-level probes.

## 3. Discover hosts in an authorized subnet

```bash
sudo nmap -sn "$SUBNET" -oA scans/host-discovery
```

Example:

```text
Nmap scan report for 192.168.56.101
Host is up (0.0020s latency).
Nmap scan report for 192.168.56.105
Host is up (0.0031s latency).
```

These hosts responded to Nmap's discovery methods; silent hosts may still be running.

Extract responding addresses from the grepable output:

```bash
awk '/Up$/{print $2}' scans/host-discovery.gnmap > live-hosts.txt
cat live-hosts.txt
```

`-oA` saves `.nmap`, `.gnmap`, and `.xml` formats.

## 4. TCP-based discovery

Useful when ICMP Echo is blocked:

```bash
sudo nmap -sn -PS22,80,443 "$IP"
sudo nmap -sn -PA80,443 "$IP"
sudo nmap -sn -PE -PS22,80,443 -PA80,443 "$IP"
```

- `-PS`: TCP SYN discovery. SYN/ACK or RST can indicate a reachable host.
- `-PA`: TCP ACK discovery. A RST may indicate a reachable host, but stateful firewalls may drop unsolicited ACKs.
- No response remains inconclusive.

Check an individual TCP port:

```bash
nc -nvz -w 3 "$IP" 80
```

A successful connection confirms that the TCP port accepted a connection.

## 5. UDP-based discovery

```bash
sudo nmap -sn -PU53,161 "$IP"
```

`-PU` sends UDP probes; UDP replies or certain ICMP errors may indicate an active host. Silence is inconclusive.

To enumerate UDP ports rather than discover hosts:

```bash
sudo nmap -sU -p 53,69,123,161 "$IP"
```

## 6. ARP discovery (local Layer 2 only)

```bash
ip -br addr
sudo arp-scan -I eth0 --localnet
sudo nmap -sn -PR 192.168.56.0/24
```

Replace `eth0` with your local Ethernet interface. ARP generally **does not traverse routed VPNs**; do not use it to discover remote lab subnets.

## 7. Known target with no discovery response

When the exam or lab explicitly assigns a target IP, you can proceed to port scanning:

```bash
sudo nmap -Pn -p 22,80,443,445 "$IP"
sudo nmap -Pn -p- --min-rate 1000 -oA scans/tcp-all "$IP"
```

`-Pn` skips host discovery; it **does not** confirm that the host is alive. `-p-` scans all 65,535 TCP ports. Aggressive packet rates can lose results on unstable links; reduce speed and rescan if necessary.

After identifying open ports, replace the example list:

```bash
sudo nmap -Pn -sC -sV -p 22,80,445 -oA scans/tcp-services "$IP"
```

- `-sC`: default NSE scripts.
- `-sV`: service/version detection.

## 8. Troubleshooting

| Symptom | Checks | Next action |
| --- | --- | --- |
| Ping fails | `ip route get "$IP"`; VPN status | Try TCP probes, then `-Pn` for assigned target |
| Nmap says host seems down | Correct IP and lab machine state | `sudo nmap -Pn -p 22,80,443 "$IP"` |
| No route to host | `ip -br addr`; `ip route` | Reconnect VPN or correct route |
| All ports filtered | Scope, route, firewall, packet loss | Retry selected ports more slowly |
| Inconsistent scan results | Timing and packet loss | `sudo nmap -Pn -sS -T2 --reason -p 22,80,443 "$IP"` |
| ARP finds nothing | Local interface and Layer 2 reachability | Use IP-level probes for routed networks |
| DNS name resolves but no response | `dig +short target.example` | Treat DNS resolution as address information, not proof of uptime |

A slower TCP-connect check can help diagnose raw-packet issues:

```bash
sudo nmap -Pn -sT -p 22,80,443 --max-retries 3 "$IP"
```

## 9. Practical workflow

1. Confirm authorized scope, target IP, VPN, and routing.
2. Try `ping -c 4 "$IP"` and `sudo nmap -sn "$IP"`.
3. If silent, try TCP SYN/ACK and selected UDP probes.
4. For an assigned target, proceed with `-Pn` even if discovery fails.
5. Run TCP port enumeration and service detection.
6. Save outputs and note the evidence for each conclusion.
7. Enumerate discovered services in their dedicated notes.

### Example notes

```text
Target: 192.168.56.101
Interface: tun0
ICMP: no response
TCP 22: open
TCP 80: open
TCP 445: open
Conclusion: reachable over TCP despite no ICMP Echo response
Next: SSH, HTTP, and SMB enumeration
Evidence: scans/tcp-all.nmap
```

## 10. Exam checklist

- [ ] Confirm target is in authorized scope.
- [ ] Confirm VPN and route to target.
- [ ] Save the target IP and working directory.
- [ ] Test ICMP and Nmap host discovery.
- [ ] Try TCP-based discovery when ICMP fails.
- [ ] Use ARP only for local Layer 2 targets.
- [ ] Use `-Pn` when scanning a known assigned target.
- [ ] Scan all TCP ports and investigate relevant UDP services.
- [ ] Run service/version enumeration on open ports.
- [ ] Save commands, outputs, and relevant evidence.
- [ ] Record failures, interpretations, and next steps.

## Common mistakes

- Treating ping failure as proof of an offline host.
- Forgetting to check the VPN route.
- Trying ARP discovery across a routed VPN.
- Mistaking `-Pn` for proof that a host is online.
- Scanning too aggressively and missing responses.
- Forgetting to save results and explain findings.

## References

- [Nmap Host Discovery](https://nmap.org/book/man-host-discovery.html)
- [Nmap Port Scanning Basics](https://nmap.org/book/man-port-scanning-basics.html)
- [Nmap Reference Guide](https://nmap.org/book/man.html)
- [arp-scan](https://github.com/royhills/arp-scan)

---

**Next:** [Nmap Enumeration](./nmap.md)

## 11. UDP port scanning — follow-up after host discovery

**Important:** The full TCP scan (`-sS -p-`) does **not** include UDP. Run UDP scans separately on assigned targets. The earlier `-sn -PU` command is for **host discovery**, not UDP port enumeration.

### Step 1 — Scan the top 100 UDP ports

```bash
sudo nmap -Pn -sU --top-ports 100 -oA scans/udp-top100 "$IP"
```

This is a practical starting point because UDP scans can take considerably longer than TCP scans.

### Step 2 — Expand if necessary

```bash
sudo nmap -Pn -sU --top-ports 1000 -oA scans/udp-top1000 "$IP"
```

For a comprehensive UDP scan when time and lab scope permit:

```bash
sudo nmap -Pn -sU -p- -oA scans/udp-all "$IP"
```

### Step 3 — Identify interesting UDP services

Replace the example ports with those identified in your results:

```bash
sudo nmap -Pn -sU -sV -p 53,69,123,161 -oA scans/udp-services "$IP"
```

Common services include DNS (53), TFTP (69), NTP (123), and SNMP (161). Services can run on nonstandard ports.

### Step 4 — Run relevant, reviewed NSE scripts

For an authorized SNMP service on UDP/161:

```bash
nmap --script-help snmp-info
sudo nmap -Pn -sU -p 161 --script snmp-info -oA scans/snmp-check "$IP"
```

Read script help first; use scripts relevant to the actual service and lab authorization. A script finding requires manual validation before being treated as a confirmed vulnerability.

### Interpret UDP scan results

| State | Meaning |
| --- | --- |
| `open` | Nmap received evidence that a UDP service is listening |
| `closed` | An ICMP port-unreachable response indicates the port is closed |
| `filtered` | Filtering prevents a determination |
| `open|filtered` | No definitive response; the port might be open or filtered |

**OSCP reminder:** Don't mark `open|filtered` as confirmed open. Try service-specific probes or `-sV` to gather more evidence.

### UDP checklist

- [ ] Run a top-100 UDP scan after the TCP scan.
- [ ] Investigate promising UDP ports with `-sV`.
- [ ] Use service-specific NSE scripts only after reviewing them.
- [ ] Expand to more UDP ports if the target and available time justify it.
- [ ] Save all scan outputs and document inconclusive results.
