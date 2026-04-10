import random
import sys
import subprocess
import platform
import netifaces
from contextlib import contextmanager


def _get_default_interface() -> str:
    """Return the name of the default network interface."""
    gateways = netifaces.gateways()
    return gateways["default"][netifaces.AF_INET][1]


def _get_current_mac(iface: str) -> str:
    """Return the current MAC address of an interface."""
    addrs = netifaces.ifaddresses(iface)
    return addrs[netifaces.AF_LINK][0]["addr"]


def generate_random_mac() -> str:
    """
    Generate a random locally administered unicast MAC address.
    Sets the locally administered bit and clears the multicast bit.
    """
    mac = [random.randint(0x00, 0xFF) for _ in range(6)]
    mac[0] = (mac[0] & 0xFE) | 0x02  # unicast + locally administered
    return ":".join(f"{b:02x}" for b in mac)


def _set_mac_linux(iface: str, mac: str) -> None:
    subprocess.run(["ip", "link", "set", iface, "down"], check=True)
    subprocess.run(["ip", "link", "set", iface, "address", mac], check=True)
    subprocess.run(["ip", "link", "set", iface, "up"], check=True)


def _set_mac_windows(iface: str, mac: str) -> None:
    # Format MAC for Windows registry: no separators
    mac_clean = mac.replace(":", "").upper()

    # Find adapter registry key by interface GUID
    result = subprocess.run(
        ["netsh", "interface", "show", "interface", "name=" + iface],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Interface '{iface}' not found via netsh.")

    # Set MAC via registry (requires admin)
    reg_path = (
        r"HKLM\SYSTEM\CurrentControlSet\Control\Class"
        r"\{4D36E972-E325-11CE-BFC1-08002BE10318}"
    )
    # Enumerate subkeys to find the matching adapter
    enum = subprocess.run(
        ["reg", "query", reg_path],
        capture_output=True, text=True
    )
    for key in enum.stdout.splitlines():
        key = key.strip()
        if not key:
            continue
        name_result = subprocess.run(
            ["reg", "query", key, "/v", "DriverDesc"],
            capture_output=True, text=True
        )
        if iface.lower() in name_result.stdout.lower():
            subprocess.run(
                ["reg", "add", key, "/v", "NetworkAddress", "/d", mac_clean, "/f"],
                check=True
            )
            # Disable then re-enable adapter to apply
            subprocess.run(["netsh", "interface", "set", "interface", iface, "disable"], check=True)
            subprocess.run(["netsh", "interface", "set", "interface", iface, "enable"], check=True)
            return

    raise RuntimeError(f"Could not find registry key for interface '{iface}'.")


def _set_mac_macos(iface: str, mac: str) -> None:
    subprocess.run(["sudo", "ifconfig", iface, "ether", mac], check=True)


def set_mac(iface: str, mac: str) -> None:
    """Apply a MAC address to the given interface (cross-platform)."""
    os_name = platform.system()
    if os_name == "Linux":
        _set_mac_linux(iface, mac)
    elif os_name == "Windows":
        _set_mac_windows(iface, mac)
    elif os_name == "Darwin":
        _set_mac_macos(iface, mac)
    else:
        raise NotImplementedError(f"Unsupported OS: {os_name}")


@contextmanager
def stealth_session(iface: str = None):
    """
    Context manager that applies a random MAC for the duration of the block,
    then restores the original MAC.

    Usage:
        with stealth_session() as fake_mac:
            scan_hosts()
    """
    if iface is None:
        iface = _get_default_interface()

    original_mac = _get_current_mac(iface)
    fake_mac = generate_random_mac()

    print(f"[stealth] Interface     : {iface}")
    print(f"[stealth] Original MAC  : {original_mac}")
    print(f"[stealth] Spoofed MAC   : {fake_mac}")

    try:
        set_mac(iface, fake_mac)
        print("[stealth] Identity applied — scan starting...")
        yield fake_mac
    finally:
        set_mac(iface, original_mac)
        print(f"[stealth] Original MAC restored: {original_mac}")
