import random
import socket
import psutil
from contextlib import contextmanager


def generate_random_mac() -> str:
    """
    Generate a random locally administered unicast MAC address.
    Sets the locally administered bit and clears the multicast bit.
    """
    mac = [random.randint(0x00, 0xFF) for _ in range(6)]
    mac[0] = (mac[0] & 0xFE) | 0x02  # unicast + locally administered
    return ":".join(f"{b:02x}" for b in mac)


def get_real_mac() -> str:
    """Return the MAC of the interface used for the default route."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    finally:
        s.close()

    for _, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == socket.AF_INET and addr.address == local_ip:
                for a in addrs:
                    if a.family == psutil.AF_LINK:
                        return a.address
    raise RuntimeError("Could not determine real MAC address.")


@contextmanager
def stealth_session():
    """
    Context manager that yields a spoofed MAC address to inject into
    nmap's --spoof-mac flag. No OS-level interface changes — safe on all platforms.

    Usage:
        with stealth_session() as fake_mac:
            nm.scan(hosts=network, arguments=f"-sn --spoof-mac {fake_mac}")
    """
    real_mac = get_real_mac()
    fake_mac = generate_random_mac()

    print(f"[stealth] Real MAC   : {real_mac}")
    print(f"[stealth] Spoofed MAC: {fake_mac}")
    print("[stealth] Scan running with spoofed identity...")

    yield fake_mac

    print(f"[stealth] Scan complete — real identity: {real_mac}")
