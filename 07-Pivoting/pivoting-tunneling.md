# Pivoting and Tunneling — OSCP Lab Field Guide

> Scope: Authorized hosts and subnets only. An internal service may be reachable from a compromised lab host but not from your Kali VPN interface. A tunnel forwards traffic; it **does not grant permission** to access that service.

## After RCE: privilege escalation or pivot?

A **reverse shell** from the [Initial Access RCE PoCs](../03-Initial-Access/initial-access.md) is a foothold, not inherently a privileged shell and **not a pivot**.

1. **Confirm identity:** on an authorized Linux foothold run `whoami; id; hostname; ip -br addr; ip route` (or `whoami /all`, `hostname`, `ipconfig` on Windows).
2. **Escalate locally when the objective requires it:** use [Linux Privilege Escalation](../04-Privilege-Escalation/linux-privesc.md) or [Windows Privilege Escalation](../04-Privilege-Escalation/windows-privesc.md). Do not assume a web-service account has root/SYSTEM.
3. **Pivot only if the next authorized machine or service is reachable through that foothold but not directly from Kali.** Determine the exact reachable target subnet and forwarding direction first. Pivoting does **not** automatically require high privileges: a supplied SSH account with appropriate forwarding rights can suffice.
4. **Stay within scope:** inspect only assigned hosts, avoid uncontrolled network scans, and document each hop. If the next objective is local privilege escalation, tunneling usually adds unnecessary work.

**Decision:** RCE shell → verify account → local privilege escalation **or** documented network pivot → enumerate the next in-scope service; the order depends on actual permissions and lab topology, not a mandatory exploit chain.

## 0. Draw the route first

~~~text
Kali VPN:          10.10.14.2
Pivot host:        192.168.56.10  (SSH login supplied by lab)
Internal service:  172.16.50.20:443
~~~

Replace these illustrative addresses and hosts with your own in-scope lab values.

From Kali:

~~~bash
ip -br addr
ip route
ip route get 172.16.50.20
~~~

On an authorized Linux pivot:

~~~bash
ip -br addr
ip route
ss -lnt
~~~

Identify the actual network path before choosing a tunnel. Note host firewall and service binding (127.0.0.1 versus a routable address).

## 1. SSH local port forwarding (-L)

Access an internal HTTPS service via a reachable SSH pivot:

~~~bash
ssh -N -L 8443:172.16.50.20:443 student@192.168.56.10
~~~

Then, in another Kali terminal:

~~~bash
curl -k -I https://127.0.0.1:8443/
~~~

Interpretation: Kali port 8443 forwards through the SSH session to the pivot, then to 172.16.50.20:443. The -N option runs no remote shell command. Certificate hostname warnings are expected when browsing through 127.0.0.1; prefer correct SNI/hostnames where possible.

## 2. SSH SOCKS dynamic forwarding (-D)

For several **in-scope** internal services:

~~~bash
ssh -N -D 127.0.0.1:1080 student@192.168.56.10
~~~

Configure a local client to use SOCKS5 at 127.0.0.1:1080. For a manual HTTP check with remote DNS resolution:

~~~bash
curl --socks5-hostname 127.0.0.1:1080 http://internal.example.lab/
~~~

If using proxychains, inspect your local configuration and note that not every network utility or scan type works through a TCP SOCKS proxy. DNS behavior and UDP/ICMP support require special attention.

## 3. SSH remote forwarding (-R)

Forward a remote port back to a service listening on Kali:

~~~bash
ssh -N -R 9000:127.0.0.1:8000 student@192.168.56.10
~~~

This example allows a client on the SSH server to reach **Kali's** local port 8000 through remote port 9000, subject to SSH server policy. Remote binds are commonly loopback-only. Confirm direction before troubleshooting.

## 4. SSH jump host (-J)

If you have valid authorized credentials for both systems:

~~~bash
ssh -J student@192.168.56.10 analyst@172.16.50.20
~~~

This is an authenticated SSH connection through the jump host; it is not the same as a network-wide route.


## 4A. Pivoting decision sheet — choose the simplest working route

| Situation | Method | Where the service connection originates |
| --- | --- | --- |
| One internal TCP service, SSH login to pivot | SSH local forward (-L) | SSH server / pivot |
| Several internal TCP services, SSH login to pivot | SSH dynamic SOCKS (-D) | SSH server / pivot |
| A service on Kali is needed from pivot | SSH remote forward (-R) | Kali SSH client |
| SSH access to a second host via first host | SSH jump (-J) | Jump host |
| Authorized pivot can connect outbound but has no reachable SSH server | Chisel reverse SOCKS or Ligolo-ng | Agent/client on pivot |
| Multiple assigned hosts and tools need normal IP routing | Ligolo-ng TUN interface | Agent on pivot |

Do not run a tunnel simply because you obtained a shell. Confirm the next assigned IP, route and service first. A local port on Kali is not the same as a port on the pivot. A tunnel does not grant authorization to any internal service.

### Step 1 — Confirm the topology

Example only: Kali VPN = 192.168.45.219; assigned SSH pivot = 192.168.56.10; assigned internal host = 172.16.50.20. Replace every value with the actual lab topology.

On Kali:

~~~bash
export LHOST=192.168.45.219
export PIVOT=192.168.56.10
export INTERNAL=172.16.50.20
ip -br addr
ip route get "$PIVOT"
ip route get "$INTERNAL"
~~~

On an authorized Linux pivot:

~~~bash
ip -br addr
ip route
ip route get 172.16.50.20
ss -lntup
~~~

On an authorized Windows pivot:

~~~powershell
ipconfig /all
route print
Get-NetTCPConnection -State Listen
Test-NetConnection 172.16.50.20 -Port 80
~~~

A route entry alone does not prove reachability. Confirm an assigned internal service with the relevant client. Do not assume every address on a discovered interface is in scope.

### Step 2 — One internal service via SSH

Kali terminal 1:

~~~bash
ssh -N -o ExitOnForwardFailure=yes -L 127.0.0.1:8080:172.16.50.20:80 student@192.168.56.10
~~~

Kali terminal 2:

~~~bash
ss -lntp | grep ':8080'
curl -i --connect-timeout 10 http://127.0.0.1:8080/
~~~

For a service on the pivot's own loopback, use 127.0.0.1 as the forwarding destination (the address is interpreted on the SSH server):

~~~bash
ssh -N -o ExitOnForwardFailure=yes -L 127.0.0.1:8081:127.0.0.1:8080 student@192.168.56.10
~~~

Browse http://127.0.0.1:8081/ on Kali to reach the pivot's localhost:8080. For name-based web services, preserve the application's hostname with an appropriate Host header; for HTTPS use the correct hostname and TLS SNI. Do not assume a localhost response is from a different host without verifying the forward.

### Step 3 — Several internal TCP services via SSH SOCKS

Kali terminal 1:

~~~bash
ssh -N -o ExitOnForwardFailure=yes -D 127.0.0.1:1080 student@192.168.56.10
~~~

Kali terminal 2:

~~~bash
ss -lntp | grep ':1080'
curl --socks5-hostname 127.0.0.1:1080 --connect-timeout 10 http://172.16.50.20/
~~~

For a browser, configure SOCKS v5 at 127.0.0.1 port 1080 and use remote DNS resolution if supported. Turn off the proxy when finished.

If a specific TCP application does not support SOCKS itself, ProxyChains-NG may work for compatible dynamically linked applications. Use a separate configuration, not a blind change to the system-wide file.

~~~bash
mkdir -p "$HOME/oscp-local"
cat > "$HOME/oscp-local/proxychains.conf" <<'EOF'
strict_chain
proxy_dns
tcp_read_time_out 15000
tcp_connect_time_out 8000
[ProxyList]
socks5 127.0.0.1 1080
EOF
proxychains4 -f "$HOME/oscp-local/proxychains.conf" curl -I http://172.16.50.20/
~~~

**Scan limitation:** ordinary SSH SOCKS is TCP application forwarding. Raw SYN scans (-sS), ICMP ping, ARP discovery and ordinary UDP scans do not pass through it. If an approved TCP-connect scan is needed, use only assigned addresses, a compatible TCP-connect client and a verified proxy path; prefer testing one known service first. ProxyChains cannot make every program or packet type proxy-aware. A direct Kali scan is not automatically routed through SOCKS.

### Step 4 — Let the SSH pivot reach a temporary HTTP server on Kali

Kali terminal 1: start the dedicated [HTTP server](../03-Initial-Access/file-transfer.md), bound to loopback when only the SSH client will use it.

~~~bash
python3 -m http.server 8000 --bind 127.0.0.1 --directory "$HOME/oscp-local/transfer"
~~~

Kali terminal 2:

~~~bash
ssh -N -o ExitOnForwardFailure=yes -R 127.0.0.1:9000:127.0.0.1:8000 student@192.168.56.10
~~~

On the authorized SSH pivot:

~~~bash
curl -f http://127.0.0.1:9000/test.txt
~~~

This does not expose the listener to the entire internal network. The destination 127.0.0.1:8000 is interpreted on Kali, and the listening 127.0.0.1:9000 belongs to the pivot. Remote binds depend on SSH server policy. Do not disable GatewayPorts restrictions or broadly expose a private HTTP directory.

## 4B. Alternative pivot tools — Chisel and Ligolo-ng

Use these only in authorized labs and after reviewing exam restrictions and the installed version's help. A standalone tunnel is not a license to access additional machines. Prepare compatible binaries before the exam; verify hashes and architecture and transfer only required tools using the [file-transfer guide](../03-Initial-Access/file-transfer.md). Never use Metasploit for pivoting across targets during the exam.

### Chisel: reverse SOCKS when the pivot must connect out

Chisel uses an encrypted SSH transport carried over HTTP. The server runs on Kali, and the authorized client on the pivot connects to it. In reverse SOCKS mode, TCP applications connect to the SOCKS port on Kali and their destination connections originate from the client. See [official Chisel documentation](https://github.com/jpillora/chisel).

Before use, check both binaries' versions and help. Choose an unused server port, restrict the server bind to the actual lab VPN IP, and use server authentication and fingerprint verification. The example credential is a placeholder; do not copy it as a real shared secret.

Kali terminal:

~~~bash
chisel server --help
chisel server --host 192.168.45.219 --port 8080 --reverse --auth 'labuser:REPLACE_WITH_LAB_SECRET'
~~~

Record the full fingerprint printed by the server. On the authorized pivot (Linux client shown; use the matching Windows executable in a Windows lab):

~~~bash
./chisel client --help
./chisel client --fingerprint 'REPLACE_WITH_SERVER_FINGERPRINT' --auth 'labuser:REPLACE_WITH_LAB_SECRET' http://192.168.45.219:8080 R:socks
~~~

On Kali, confirm the reverse SOCKS listener and test an assigned internal service:

~~~bash
ss -lntp | grep ':1080'
curl --socks5-hostname 127.0.0.1:1080 http://172.16.50.20/
~~~

Do not publish command histories containing credentials. For repeated practice, prefer a protected authfile as described upstream. The ordinary R:socks remote is TCP-only. Recent Chisel versions may support separate UDP SOCKS features, but both peers and the client must support them; ordinary Nmap raw-packet scanning is not made proxy-aware. If the client cannot reach the server, troubleshoot routes and authorized egress rather than bypassing security controls.

### Ligolo-ng: routed access to a specific assigned internal host

Ligolo-ng uses a TUN interface on Kali and an agent on the authorized pivot. Unlike SOCKS, it provides an interface and route for supported traffic; not every raw-packet behavior is equivalent to a directly connected host. It requires permission to create/manage the TUN interface on Kali and outbound connectivity from the agent. Use a current, matching proxy/agent release. See the [official Quickstart](https://docs.ligolo.ng/Quickstart/).

Kali, prepare a uniquely named TUN interface:

~~~bash
sudo ip tuntap add user "$(id -un)" mode tun oscp-ligolo
sudo ip link set oscp-ligolo up
./proxy -h
./proxy -selfcert -laddr 192.168.45.219:11601
~~~

In the proxy console, request the certificate fingerprint:

~~~text
certificate_fingerprint
~~~

On the authorized pivot, use the correct agent architecture and the actual server fingerprint. Example Linux command:

~~~bash
./agent -connect 192.168.45.219:11601 -accept-fingerprint REPLACE_WITH_CERTIFICATE_FINGERPRINT
~~~

Windows equivalent uses the matching agent.exe in the authorized directory and the same options. Do not disable certificate verification by default.

In the Kali proxy console, select the actual agent session, check its interfaces and start the tunnel:

~~~text
session
ifconfig
tunnel_start --tun oscp-ligolo
~~~

Choose the intended session at the prompt. Check the installed version's help if the console command names differ. In a separate Kali terminal, add the smallest route that is necessary for the assigned internal target:

~~~bash
sudo ip route add 172.16.50.20/32 dev oscp-ligolo
ip route get 172.16.50.20
curl -i --connect-timeout 10 http://172.16.50.20/
~~~

The /32 route covers exactly one IPv4 address. Use a larger subnet only when the entire subnet is explicitly assigned and necessary. Never replace the default route or VPN route. For TCP service discovery through this tunnel, use a compatible TCP-connect approach and verify actual service reachability; do not assume direct raw SYN/UDP scan semantics.

When finished, stop the selected tunnel using its console help, close the agent/proxy sessions and remove only your own route/interface:

~~~bash
sudo ip route del 172.16.50.20/32 dev oscp-ligolo
sudo ip link del oscp-ligolo
~~~

If cleanup says the route or interface is absent, inspect ip route and ip link before changing anything else. For double pivots, consult the [official advanced pivoting guide](https://docs.ligolo.ng/Advanced%20Pivoting/) and draw each hop separately. Do not chain tunnels unless required by the assigned topology.

### End-to-end troubleshooting

| Observation | Action |
| --- | --- |
| Listener exists but no client session | Verify the correct VPN address, port, client-to-server route and version |
| Session connects but internal HTTP fails | Verify target IP, target service, exit-side route and internal firewall |
| SOCKS works in curl but not another tool | Check that tool's proxy support, DNS and TCP connection type |
| Direct scan bypasses tunnel | Verify route or explicit SOCKS configuration before testing |
| Ligolo route conflicts with VPN | Remove only the added route; use the specific assigned host route |
| HTTP transfer works locally but not remotely | Check bind address, HTTP path, direction, listener and client reachability |
| Tool says certificate mismatch | Check real server fingerprint and destination, not an insecure bypass |
| Need another hop | Confirm exact assigned destination and routing before choosing another tunnel |

**Record:** tunnel type, source, pivot, assigned destination, route, ports, verified service, and cleanup. Keep evidence private. Close all tunnels and temporary file servers when the exercise is done.

## 5. Troubleshooting

~~~bash
ss -lnt
ssh -v student@192.168.56.10
curl -v --socks5-hostname 127.0.0.1:1080 http://internal.example.lab/
~~~

| Symptom | Likely issue |
| --- | --- |
| Cannot establish SSH | Routing, sshd service, firewall, credential |
| SSH works, forwarded app fails | Wrong destination from pivot perspective |
| Local port already used | Choose a different unused local port |
| Name fails behind SOCKS | DNS resolution occurring locally instead of remotely |
| UDP/ICMP does not traverse | Standard SOCKS/SSH forwards are mostly TCP |
| Forward allowed locally but not remotely | SSH server forwarding policy / bind behavior |
| HTTPS certificate warning | Hostname/SNI mismatch over localhost forwarding |

## 6. Exam policy and evidence

OffSec prohibits using Metasploit as a pivot when it would operate on multiple targets. Ordinary SSH forwarding and manual clients are not listed as prohibited by name, but **tool features and scope still matter**. Check the [current official OSCP+ guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide). Avoid broad scanning of networks not explicitly assigned to you.

Record each tunnel with a simple map:

~~~text
From / local listening port:
Pivot identity and IP:
Forward type (-L / -D / -R / -J):
Remote destination:
Client configured to use tunnel:
Command and result:
Time opened / closed:
~~~

## Checklist

- [ ] Destination and route in scope.
- [ ] Confirmed whether local privilege escalation is actually necessary before any pivot, and mapped the authorized next hop.
- [ ] Pivot identity legitimately authorized.
- [ ] Correct tunnel direction and bind addresses.
- [ ] Service manually verified after forwarding.
- [ ] DNS and proxy client configuration checked.
- [ ] Tunnel and evidence documented.
- [ ] Metasploit pivot restriction observed.

## References

- [Chisel documentation](https://github.com/jpillora/chisel)
- [Ligolo-ng Quickstart](https://docs.ligolo.ng/Quickstart/)
- [ProxyChains-NG](https://github.com/rofl0r/proxychains-ng)
- [HTTP and File Transfer](../03-Initial-Access/file-transfer.md)

- [OpenSSH ssh manual](https://man.openbsd.org/ssh)
- [OffSec OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide)
