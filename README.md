# Net Explorer

A Python-based network exploration tool that scans and visualizes active hosts, open ports, and network flows through an interactive web dashboard.

## Features

- Local network discovery (hosts, IPs, MAC addresses)
- Open port scanning
- Real-time network flow visualization
- Interactive graph dashboard built with Dash & Cytoscape

## Stack

- **Backend:** Python (Scapy, Nmap, Psutil)
- **Frontend:** Dash + Dash Cytoscape

## Requirements

- Python 3.10+
- Administrator / root privileges (required for packet capture and ARP scanning)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

Then open your browser at `http://localhost:8050`

## License

MIT
