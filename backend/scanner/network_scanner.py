import nmap
import psutil
import socket
import netifaces


def get_local_network() -> str:
    """Detect the local network CIDR (e.g. 192.168.1.0/24)."""
    gateways = netifaces.gateways()
    default_iface = gateways["default"][netifaces.AF_INET][1]
    iface_info = netifaces.ifaddresses(default_iface)[netifaces.AF_INET][0]
    ip = iface_info["addr"]
    netmask = iface_info["netmask"]

    # Convert IP + netmask to CIDR notation
    ip_parts = list(map(int, ip.split(".")))
    mask_parts = list(map(int, netmask.split(".")))
    network = ".".join(str(ip_parts[i] & mask_parts[i]) for i in range(4))
    prefix = sum(bin(x).count("1") for x in mask_parts)

    return f"{network}/{prefix}"


def scan_hosts(network: str = None) -> list[dict]:
    """
    Scan the network for active hosts.
    Returns a list of dicts: {ip, hostname, mac, status}
    """
    if network is None:
        network = get_local_network()

    nm = nmap.PortScanner()
    nm.scan(hosts=network, arguments="-sn")  # Ping scan, no port scan

    hosts = []
    for host in nm.all_hosts():
        info = nm[host]
        hostname = info.hostname() or host
        mac = info["addresses"].get("mac", "N/A")
        vendor = info.get("vendor", {}).get(mac, "Unknown") if mac != "N/A" else "Unknown"
        hosts.append({
            "ip": host,
            "hostname": hostname,
            "mac": mac,
            "vendor": vendor,
            "status": info["status"]["state"],
        })

    return hosts


def scan_ports(ip: str, ports: str = "1-1024") -> list[dict]:
    """
    Scan open ports on a given host.
    Returns a list of dicts: {port, protocol, state, service}
    """
    nm = nmap.PortScanner()
    nm.scan(hosts=ip, arguments=f"-sV -p {ports}")

    open_ports = []
    if ip not in nm.all_hosts():
        return open_ports

    for proto in nm[ip].all_protocols():
        for port, info in nm[ip][proto].items():
            open_ports.append({
                "port": port,
                "protocol": proto,
                "state": info["state"],
                "service": info["name"],
                "version": info.get("version", ""),
            })

    return open_ports


def get_local_connections() -> list[dict]:
    """
    Get active network connections on the local machine via psutil.
    Returns a list of dicts: {local_ip, local_port, remote_ip, remote_port, status, pid}
    """
    connections = []
    for conn in psutil.net_connections(kind="inet"):
        if conn.status == psutil.CONN_ESTABLISHED:
            connections.append({
                "local_ip": conn.laddr.ip,
                "local_port": conn.laddr.port,
                "remote_ip": conn.raddr.ip if conn.raddr else None,
                "remote_port": conn.raddr.port if conn.raddr else None,
                "status": conn.status,
                "pid": conn.pid,
            })
    return connections
