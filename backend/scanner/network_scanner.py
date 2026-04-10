import ipaddress
import nmap
import psutil
import socket


def _get_local_ip() -> str:
    """Get the local IP used to reach the outside world."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


def get_local_network() -> str:
    """Detect the local network CIDR (e.g. 192.168.1.0/24)."""
    local_ip = _get_local_ip()
    for addrs in psutil.net_if_addrs().values():
        for addr in addrs:
            if addr.family == socket.AF_INET and addr.address == local_ip:
                network = ipaddress.IPv4Network(
                    f"{addr.address}/{addr.netmask}", strict=False
                )
                return str(network)
    raise RuntimeError("Could not determine local network.")


def get_default_interface() -> str:
    """Return the name of the interface used for the default route."""
    local_ip = _get_local_ip()
    for iface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == socket.AF_INET and addr.address == local_ip:
                return iface
    raise RuntimeError("Could not determine default interface.")


def scan_hosts(network: str = None, spoof_mac: str = None) -> list[dict]:
    """
    Scan the network for active hosts.
    Returns a list of dicts: {ip, hostname, mac, vendor, status}
    """
    if network is None:
        network = get_local_network()

    args = "-sn"
    if spoof_mac:
        args += f" --spoof-mac {spoof_mac}"

    nm = nmap.PortScanner()
    nm.scan(hosts=network, arguments=args)

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
    Returns a list of dicts: {port, protocol, state, service, version}
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
