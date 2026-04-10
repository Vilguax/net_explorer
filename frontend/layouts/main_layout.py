import dash_cytoscape as cyto
import dash_bootstrap_components as dbc
from dash import dcc, html

cyto.load_extra_layouts()

layout = dbc.Container(
    fluid=True,
    style={"padding": "20px"},
    children=[

        # ── Header ────────────────────────────────────────────────────
        dbc.Row([
            dbc.Col([
                html.H2("Net Explorer", className="text-info mb-0"),
                html.Small("Local network scanner & flow visualizer", className="text-muted"),
            ], width=8),
            dbc.Col([
                dbc.Switch(id="stealth-toggle", label="Stealth mode", value=False,
                           className="mt-2"),
            ], width=2, className="text-end"),
            dbc.Col([
                dbc.Button("Scan network", id="scan-btn", color="info", className="mt-1 w-100"),
            ], width=2),
        ], className="mb-4 align-items-center"),

        # ── Status bar ────────────────────────────────────────────────
        dbc.Row([
            dbc.Col(
                html.Div(id="scan-status", className="text-muted small"),
            )
        ], className="mb-3"),

        # ── Graph + Host table ────────────────────────────────────────
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Network graph"),
                    dbc.CardBody(
                        cyto.Cytoscape(
                            id="network-graph",
                            layout={"name": "cose"},
                            style={"width": "100%", "height": "420px"},
                            stylesheet=[
                                {
                                    "selector": "node",
                                    "style": {
                                        "label": "data(label)",
                                        "background-color": "#17a2b8",
                                        "color": "#fff",
                                        "font-size": "11px",
                                        "text-valign": "bottom",
                                        "text-halign": "center",
                                    },
                                },
                                {
                                    "selector": "node[type='gateway']",
                                    "style": {"background-color": "#ffc107", "width": 40, "height": 40},
                                },
                                {
                                    "selector": "node[type='local']",
                                    "style": {"background-color": "#28a745"},
                                },
                                {
                                    "selector": "edge",
                                    "style": {
                                        "line-color": "#555",
                                        "target-arrow-color": "#555",
                                        "target-arrow-shape": "triangle",
                                        "curve-style": "bezier",
                                        "width": 1.5,
                                    },
                                },
                                {
                                    "selector": "edge[proto='TCP']",
                                    "style": {"line-color": "#17a2b8"},
                                },
                                {
                                    "selector": "edge[proto='UDP']",
                                    "style": {"line-color": "#6f42c1"},
                                },
                                {
                                    "selector": "edge[proto='ARP']",
                                    "style": {"line-color": "#fd7e14"},
                                },
                            ],
                            elements=[],
                        )
                    ),
                ], color="dark", outline=True),
            ], width=8),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Discovered hosts"),
                    dbc.CardBody(
                        html.Div(id="hosts-table", style={"overflowY": "auto", "maxHeight": "380px"}),
                    ),
                ], color="dark", outline=True),
            ], width=4),
        ], className="mb-4"),

        # ── Ports + Flows ─────────────────────────────────────────────
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        dbc.Row([
                            dbc.Col("Open ports", width=8),
                            dbc.Col(
                                dbc.Select(
                                    id="port-host-select",
                                    placeholder="Select a host...",
                                    options=[],
                                    size="sm",
                                ),
                                width=4,
                            ),
                        ])
                    ),
                    dbc.CardBody(
                        html.Div(id="ports-table", style={"overflowY": "auto", "maxHeight": "260px"}),
                    ),
                ], color="dark", outline=True),
            ], width=6),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        dbc.Row([
                            dbc.Col("Live flows", width=8),
                            dbc.Col(
                                dbc.ButtonGroup([
                                    dbc.Button("Start", id="sniffer-start", color="success", size="sm"),
                                    dbc.Button("Stop", id="sniffer-stop", color="danger", size="sm"),
                                ]),
                                width=4, className="text-end",
                            ),
                        ])
                    ),
                    dbc.CardBody(
                        html.Div(id="flows-table", style={"overflowY": "auto", "maxHeight": "260px"}),
                    ),
                ], color="dark", outline=True),
            ], width=6),
        ]),

        # ── Intervals ─────────────────────────────────────────────────
        dcc.Interval(id="flow-interval", interval=2000, n_intervals=0, disabled=True),

        # ── Stores ────────────────────────────────────────────────────
        dcc.Store(id="hosts-store", data=[]),
    ],
)
