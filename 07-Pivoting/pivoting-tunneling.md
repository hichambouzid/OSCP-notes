# Pivoting and Tunneling — OSCP Lab Field Guide

> Scope: Authorized hosts and subnets only. An internal service may be reachable from a compromised lab host but not from your Kali VPN interface. A tunnel forwards traffic; it **does not grant permission** to access that service.

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
- [ ] Pivot identity legitimately authorized.
- [ ] Correct tunnel direction and bind addresses.
- [ ] Service manually verified after forwarding.
- [ ] DNS and proxy client configuration checked.
- [ ] Tunnel and evidence documented.
- [ ] Metasploit pivot restriction observed.

## References

- [OpenSSH ssh manual](https://man.openbsd.org/ssh)
- [OffSec OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide)
