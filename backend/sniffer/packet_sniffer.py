import logging
import threading
from collections import defaultdict
from datetime import datetime

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import sniff, IP, TCP, UDP, ARP, ICMP  # noqa: E402


class PacketSniffer:
    """
    Captures packets on the network interface and builds
    a live flow table: {(src_ip, dst_ip, port, proto): flow_data}
    """

    def __init__(self):
        self._flows: dict = defaultdict(lambda: {
            "src_ip": None,
            "dst_ip": None,
            "port": None,
            "protocol": None,
            "packet_count": 0,
            "first_seen": None,
            "last_seen": None,
        })
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._running = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self, iface: str = None, packet_filter: str = "ip or arp"):
        """Start packet capture in a background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._capture,
            args=(iface, packet_filter),
            daemon=True,
        )
        self._thread.start()
        print(f"[sniffer] Capture started on {'default iface' if iface is None else iface}")

    def stop(self):
        """Stop the packet capture."""
        self._running = False
        print("[sniffer] Capture stopped.")

    def get_flows(self) -> list[dict]:
        """Return a snapshot of current flows."""
        with self._lock:
            return list(self._flows.values())

    def get_top_talkers(self, n: int = 10) -> list[dict]:
        """Return the top N flows by packet count."""
        flows = self.get_flows()
        return sorted(flows, key=lambda f: f["packet_count"], reverse=True)[:n]

    def clear(self):
        """Reset all captured flows."""
        with self._lock:
            self._flows.clear()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _capture(self, iface: str | None, packet_filter: str):
        sniff(
            iface=iface,
            filter=packet_filter,
            prn=self._process_packet,
            stop_filter=lambda _: not self._running,
            store=False,
        )

    def _process_packet(self, pkt):
        now = datetime.utcnow().isoformat()

        if IP in pkt:
            src = pkt[IP].src
            dst = pkt[IP].dst

            if TCP in pkt:
                port = pkt[TCP].dport
                proto = "TCP"
            elif UDP in pkt:
                port = pkt[UDP].dport
                proto = "UDP"
            elif ICMP in pkt:
                port = None
                proto = "ICMP"
            else:
                port = None
                proto = "IP"

        elif ARP in pkt:
            src = pkt[ARP].psrc
            dst = pkt[ARP].pdst
            port = None
            proto = "ARP"

        else:
            return

        key = (src, dst, port, proto)

        with self._lock:
            flow = self._flows[key]
            flow["src_ip"] = src
            flow["dst_ip"] = dst
            flow["port"] = port
            flow["protocol"] = proto
            flow["packet_count"] += 1
            flow["last_seen"] = now
            if flow["first_seen"] is None:
                flow["first_seen"] = now


# Singleton accessible depuis toute l'app
sniffer = PacketSniffer()
