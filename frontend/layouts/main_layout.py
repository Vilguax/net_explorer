import dash_cytoscape as cyto
import dash_bootstrap_components as dbc
from dash import dcc, html

cyto.load_extra_layouts()

# ── Palette ───────────────────────────────────────────────────────────────────
BG       = "#0d1117"
SURFACE  = "#161b22"
BORDER   = "#30363d"
ACCENT   = "#58a6ff"
SUCCESS  = "#3fb950"
DANGER   = "#f85149"
WARNING  = "#d29922"
MUTED    = "#8b949e"
TEXT     = "#e6edf3"

card_style = {
    "background": SURFACE,
    "border": f"1px solid {BORDER}",
    "borderRadius": "8px",
    "padding": "0",
}

header_style = {
    "background": "#1c2128",
    "borderBottom": f"1px solid {BORDER}",
    "borderRadius": "8px 8px 0 0",
    "padding": "10px 16px",
    "color": MUTED,
    "fontSize": "12px",
    "fontWeight": "600",
    "letterSpacing": "0.05em",
    "textTransform": "uppercase",
}

# ── Layout ────────────────────────────────────────────────────────────────────
layout = html.Div(
    style={"background": BG, "minHeight": "100vh", "padding": "24px", "fontFamily": "monospace"},
    children=[

        # ── Header ────────────────────────────────────────────────────
        html.Div(
            style={"display": "flex", "alignItems": "center", "justifyContent": "space-between", "marginBottom": "24px"},
            children=[
                html.Div([
                    html.Span("net_explorer", style={"color": ACCENT, "fontSize": "22px", "fontWeight": "700"}),
                    html.Span("  //  local network scanner", style={"color": MUTED, "fontSize": "13px"}),
                ]),
                html.Div(
                    style={"display": "flex", "gap": "12px", "alignItems": "center"},
                    children=[
                        html.Div(
                            style={"display": "flex", "alignItems": "center", "gap": "8px"},
                            children=[
                                dbc.Switch(id="stealth-toggle", value=False, style={"marginBottom": "0"}),
                                html.Span("stealth", style={"color": MUTED, "fontSize": "12px"}),
                            ]
                        ),
                        dbc.Button(
                            "[ scan network ]",
                            id="scan-btn",
                            style={
                                "background": "transparent",
                                "border": f"1px solid {ACCENT}",
                                "color": ACCENT,
                                "fontFamily": "monospace",
                                "fontSize": "13px",
                                "padding": "6px 16px",
                                "borderRadius": "4px",
                            }
                        ),
                    ]
                ),
            ]
        ),

        # ── Status bar ────────────────────────────────────────────────
        html.Div(
            id="scan-status",
            style={"color": MUTED, "fontSize": "12px", "marginBottom": "16px", "minHeight": "18px"},
        ),

        # ── Graph + Hosts ─────────────────────────────────────────────
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "2fr 1fr", "gap": "16px", "marginBottom": "16px"},
            children=[
                # Graph
                html.Div(style=card_style, children=[
                    html.Div("network graph", style=header_style),
                    cyto.Cytoscape(
                        id="network-graph",
                        layout={"name": "cose"},
                        style={"width": "100%", "height": "400px", "background": SURFACE, "borderRadius": "0 0 8px 8px"},
                        stylesheet=[
                            {
                                "selector": "node",
                                "style": {
                                    "label": "data(label)",
                                    "background-color": "#1f6feb",
                                    "color": TEXT,
                                    "font-size": "10px",
                                    "font-family": "monospace",
                                    "text-valign": "bottom",
                                    "text-margin-y": "4px",
                                    "width": 28, "height": 28,
                                    "border-width": 2,
                                    "border-color": ACCENT,
                                },
                            },
                            {
                                "selector": "node[type='local']",
                                "style": {
                                    "background-color": "#238636",
                                    "border-color": SUCCESS,
                                    "width": 36, "height": 36,
                                },
                            },
                            {
                                "selector": "edge",
                                "style": {
                                    "line-color": BORDER,
                                    "target-arrow-color": BORDER,
                                    "target-arrow-shape": "triangle",
                                    "curve-style": "bezier",
                                    "width": 1.5,
                                },
                            },
                            {"selector": "edge[proto='TCP']", "style": {"line-color": ACCENT}},
                            {"selector": "edge[proto='UDP']", "style": {"line-color": "#a371f7"}},
                            {"selector": "edge[proto='ARP']", "style": {"line-color": WARNING}},
                        ],
                        elements=[],
                    ),
                ]),

                # Hosts
                html.Div(style=card_style, children=[
                    html.Div("discovered hosts", style=header_style),
                    html.Div(
                        id="hosts-table",
                        style={"overflowY": "auto", "maxHeight": "370px", "padding": "8px"},
                        children=[html.Span("—", style={"color": MUTED, "fontSize": "12px"})],
                    ),
                ]),
            ]
        ),

        # ── Ports + Flows ─────────────────────────────────────────────
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "16px"},
            children=[
                # Ports
                html.Div(style=card_style, children=[
                    html.Div(
                        style={**header_style, "display": "flex", "justifyContent": "space-between", "alignItems": "center"},
                        children=[
                            html.Span("open ports"),
                            dbc.Select(
                                id="port-host-select",
                                placeholder="select host...",
                                options=[],
                                style={
                                    "background": BG,
                                    "border": f"1px solid {BORDER}",
                                    "color": TEXT,
                                    "fontFamily": "monospace",
                                    "fontSize": "11px",
                                    "padding": "2px 8px",
                                    "width": "160px",
                                    "height": "28px",
                                }
                            ),
                        ]
                    ),
                    html.Div(
                        id="ports-table",
                        style={"overflowY": "auto", "maxHeight": "250px", "padding": "8px"},
                        children=[html.Span("—", style={"color": MUTED, "fontSize": "12px"})],
                    ),
                ]),

                # Flows
                html.Div(style=card_style, children=[
                    html.Div(
                        style={**header_style, "display": "flex", "justifyContent": "space-between", "alignItems": "center"},
                        children=[
                            html.Span("live flows"),
                            html.Div([
                                dbc.Button("start", id="sniffer-start", style={
                                    "background": "transparent", "border": f"1px solid {SUCCESS}",
                                    "color": SUCCESS, "fontFamily": "monospace", "fontSize": "11px",
                                    "padding": "2px 10px", "marginRight": "6px",
                                }),
                                dbc.Button("stop", id="sniffer-stop", style={
                                    "background": "transparent", "border": f"1px solid {DANGER}",
                                    "color": DANGER, "fontFamily": "monospace", "fontSize": "11px",
                                    "padding": "2px 10px",
                                }),
                            ]),
                        ]
                    ),
                    html.Div(
                        id="flows-table",
                        style={"overflowY": "auto", "maxHeight": "250px", "padding": "8px"},
                        children=[html.Span("—", style={"color": MUTED, "fontSize": "12px"})],
                    ),
                ]),
            ]
        ),

        # ── Intervals + Store ─────────────────────────────────────────
        dcc.Interval(id="flow-interval", interval=2000, n_intervals=0, disabled=True),
        dcc.Store(id="hosts-store", data=[]),
    ]
)
