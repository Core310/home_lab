# Phase: Pi-hole & Tailscale Integration - Research

**Researched:** 2026-07-07
**Domain:** DNS, Containers, VPN
**Confidence:** HIGH

## Summary

The requested stack pairs Pi-hole with Cloudflared in Docker for DNS-over-HTTPS (DoH) and configures Tailscale MagicDNS to route all mesh clients to the Pi-hole. While this is a standard and robust pattern, a critical update is required: **the `proxy-dns` feature in `cloudflared` was deprecated and removed from new releases starting February 2, 2026.** Thus, the standard stack must pivot from `cloudflared` to an alternative DoH proxy such as `dnscrypt-proxy`. 

Tailscale MagicDNS handles `.ts.net` local resolutions natively. By adding the Pi-hole's Tailscale IP as a Global Custom Nameserver and enabling "Override local DNS", MagicDNS will automatically forward all non-Tailscale queries to the Pi-hole for resolution.

**Primary recommendation:** Use `dnscrypt-proxy` instead of `cloudflared` for DoH upstream, and set the Pi-hole's Tailscale IP as a Custom Nameserver in Tailscale with "Override local DNS" enabled.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pi-hole | latest | Network-wide ad blocking and DNS | Standard lightweight DNS sinkhole |
| dnscrypt-proxy | latest | DNS-over-HTTPS proxy | Replaces deprecated `cloudflared proxy-dns` |
| Tailscale | latest | Mesh VPN and MagicDNS | Provides zero-config secure mesh networking |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| cloudflared | dnscrypt-proxy | `cloudflared` `proxy-dns` command was deprecated/removed (Feb 2026). `dnscrypt-proxy` is the widely accepted DoH replacement in the self-hosting community. |

## Architecture Patterns

### Recommended Project Structure
```text
pihole/
├── docker-compose.yml     # Pi-hole + dnscrypt-proxy
├── etc-pihole/            # Pi-hole config volume
└── etc-dnsmasq.d/         # dnsmasq config volume
```

### Pattern 1: Pi-hole + dnscrypt-proxy over shared Docker network
**What:** Deploy Pi-hole and the DoH proxy in a single `docker-compose.yml`, using a shared bridge network.
**When to use:** Whenever self-hosting Pi-hole with encrypted upstream DNS in containers.
**Example:**
```yaml
services:
  dnscrypt-proxy:
    image: klizhentas/dnscrypt-proxy:latest
    container_name: dnscrypt-proxy
    restart: unless-stopped
    networks:
      - dnsnet

  pihole:
    image: pihole/pihole:latest
    container_name: pihole
    restart: unless-stopped
    ports:
      - "53:53/tcp"
      - "53:53/udp"
      - "80:80/tcp"
    environment:
      TZ: 'UTC'
      WEBPASSWORD: 'yourpassword'
      FTLCONF_DNS_UPSTREAMS: 'dnscrypt-proxy#53'
    volumes:
      - './etc-pihole:/etc/pihole'
      - './etc-dnsmasq.d:/etc/dnsmasq.d'
    depends_on:
      - dnscrypt-proxy
    networks:
      - dnsnet

networks:
  dnsnet:
    driver: bridge
```

### Pattern 2: Tailscale MagicDNS Forwarding
**What:** Force all Tailscale clients to use the Pi-hole for non-Tailscale DNS queries.
**How:**
1. Log into the Tailscale Admin Console and navigate to the DNS tab.
2. Ensure MagicDNS is enabled.
3. Click "Add nameserver" -> Custom, and provide the Pi-hole's `100.x.y.z` (Tailscale IP).
4. Enable the **Override local DNS** toggle.

## Common Pitfalls

### Pitfall 1: cloudflared `proxy-dns` Deprecation
**What goes wrong:** Container fails to start or resolve DNS when using the `cloudflare/cloudflared` image with the `proxy-dns` command.
**Why it happens:** Cloudflare removed the `proxy-dns` command starting February 2, 2026 due to underlying security vulnerabilities.
**How to avoid:** Use `dnscrypt-proxy` or built-in DoH configurations instead of `cloudflared`.

### Pitfall 2: Pi-hole Blocking Tailscale Queries
**What goes wrong:** Devices on Tailscale can't resolve any DNS queries.
**Why it happens:** By default, Pi-hole only allows queries from its local subnet (e.g., `192.168.1.0/24`). Tailscale traffic arrives on the `tailscale0` interface, which is treated as an external origin.
**How to avoid:** In Pi-hole Settings -> DNS -> Interface Settings (Expert mode), enable **Permit all origins**. Since the Pi-hole is protected by Tailscale and not exposed to the public internet, this is safe.

### Pitfall 3: DNS Query Loop on Pi-hole Host
**What goes wrong:** The host machine running Pi-hole loses internet connectivity or causes a recursive DNS loop.
**Why it happens:** If the host machine uses MagicDNS (via Tailscale) for its own DNS resolution, it asks Tailscale, which asks Pi-hole, which then asks Tailscale.
**How to avoid:** Run `tailscale up --accept-dns=false` on the machine hosting the Pi-hole so it bypasses Tailscale's MagicDNS for its own local resolution.

## Code Examples

### Tailscale Host Bypass Configuration
```bash
# Prevents the Pi-hole host from querying its own Tailscale IP, avoiding a loop
sudo tailscale up --accept-dns=false
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `cloudflared proxy-dns` | `dnscrypt-proxy` | Feb 2026 | The standard pattern of using `cloudflared` for Pi-hole upstream DoH is no longer viable and requires migrating to `dnscrypt-proxy`. |

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Verified Cloudflare deprecation notice (Feb 2026) and widely adopted Docker alternatives.
- Architecture: HIGH - Architecture pattern natively matches official Tailscale documentation.
- Pitfalls: HIGH - Pitfalls cover documented community challenges with Split-DNS loops and interface blocking.

**Research date:** 2026-07-07
**Valid until:** 30 days
