import socket
from dash import Input, Output, State, callback, html, no_update
import dash_bootstrap_components as dbc

from backend.scanner.network_scanner import scan_hosts, scan_ports, get_local_network
from backend.sniffer.packet_sniffer import sniffer
from backend.stealth.stealth_manager import stealth_session


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hosts_to_table(hosts: list[dict]):
    if not hosts:
        return html.P("No hosts found.", className="text-muted small")
    rows = [
        html.Tr([
            html.Td(h["ip"]),
            html.Td(h["hostname"][:20] if h["hostname"] else "—"),
            html.Td(h["mac"]),
            html.Td(h["vendor"][:16] if h["vendor"] else "—"),
        ])
        for h in hosts
    ]
    return dbc.Table(
        [
            html.Thead(html.Tr([html.Th("IP"), html.Th("Hostname"), html.Th("MAC"), html.Th("Vendor")])),
            html.Tbody(rows),
        ],
        bordered=False, hover=True, responsive=True, size="sm", dark=True,
    )


def _ports_to_table(ports: list[dict]):
    if not ports:
        return html.P("No open ports.", className="text-muted small")
    rows = [
        html.Tr([
            html.Td(p["port"]),
            html.Td(p["protocol"].upper()),
            html.Td(p["state"]),
            html.Td(p["service"]),
            html.Td(p.get("version", "") or "—"),
        ])
        for p in ports if p["state"] == "open"
    ]
    if not rows:
        return html.P("No open ports.", className="text-muted small")
    return dbc.Table(
        [
            html.Thead(html.Tr([
                html.Th("Port"), html.Th("Proto"), html.Th("State"), html.Th("Service"), html.Th("Version"),
            ])),
            html.Tbody(rows),
        ],
        bordered=False, hover=True, responsive=True, size="sm", dark=True,
    )


def _flows_to_table(flows: list[dict]):
    if not flows:
        return html.P("No flows captured.", className="text-muted small")
    top = sorted(flows, key=lambda f: f["packet_count"], reverse=True)[:50]
    rows = [
        html.Tr([
            html.Td(f["src_ip"]),
            html.Td(f["dst_ip"]),
            html.Td(str(f["port"]) if f["port"] else "—"),
            html.Td(f["protocol"]),
            html.Td(str(f["packet_count"])),
        ])
        for f in top
    ]
    return dbc.Table(
        [
            html.Thead(html.Tr([
                html.Th("Source"), html.Th("Destination"), html.Th("Port"), html.Th("Proto"), html.Th("Pkts"),
            ])),
            html.Tbody(rows),
        ],
        bordered=False, hover=True, responsive=True, size="sm", dark=True,
    )


def _build_graph_elements(hosts: list[dict], flows: list[dict]) -> list[dict]:
    local_ip = socket.gethostbyname(socket.gethostname())
    elements = []
    host_ips = {h["ip"] for h in hosts}

    # Nodes
    for h in hosts:
        node_type = "local" if h["ip"] == local_ip else "host"
        elements.append({
            "data": {"id": h["ip"], "label": h["ip"], "type": node_type},
        })

    # Edges from live flows (only between known hosts)
    seen_edges = set()
    for f in flows:
        src, dst = f["src_ip"], f["dst_ip"]
        if src in host_ips and dst in host_ips:
            key = (src, dst, f["protocol"])
            if key not in seen_edges:
                seen_edges.add(key)
                elements.append({
                    "data": {
                        "source": src,
                        "target": dst,
                        "proto": f["protocol"],
                        "packets": f["packet_count"],
                    }
                })

    return elements


# ── Callbacks ─────────────────────────────────────────────────────────────────

@callback(
    Output("hosts-store", "data"),
    Output("hosts-table", "children"),
    Output("port-host-select", "options"),
    Output("scan-status", "children"),
    Input("scan-btn", "n_clicks"),
    State("stealth-toggle", "value"),
    prevent_initial_call=True,
)
def run_scan(n_clicks, stealth_on):
    try:
        network = get_local_network()
        if stealth_on:
            with stealth_session():
                hosts = scan_hosts(network)
        else:
            hosts = scan_hosts(network)

        options = [{"label": h["ip"], "value": h["ip"]} for h in hosts]
        status = f"Scan complete — {len(hosts)} host(s) found on {network}"
        return hosts, _hosts_to_table(hosts), options, status
    except Exception as e:
        return [], html.P(f"Error: {e}", className="text-danger small"), [], f"Scan failed: {e}"


@callback(
    Output("ports-table", "children"),
    Input("port-host-select", "value"),
    prevent_initial_call=True,
)
def load_ports(ip):
    if not ip:
        return no_update
    try:
        ports = scan_ports(ip)
        return _ports_to_table(ports)
    except Exception as e:
        return html.P(f"Error: {e}", className="text-danger small")


@callback(
    Output("flow-interval", "disabled"),
    Input("sniffer-start", "n_clicks"),
    Input("sniffer-stop", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_sniffer(start, stop):
    from dash import ctx
    if ctx.triggered_id == "sniffer-start":
        sniffer.start()
        return False  # enable interval
    sniffer.stop()
    return True  # disable interval


@callback(
    Output("flows-table", "children"),
    Output("network-graph", "elements"),
    Input("flow-interval", "n_intervals"),
    State("hosts-store", "data"),
    prevent_initial_call=True,
)
def refresh_flows(n, hosts):
    flows = sniffer.get_flows()
    elements = _build_graph_elements(hosts or [], flows)
    return _flows_to_table(flows), elements
