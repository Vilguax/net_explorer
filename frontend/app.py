import dash
import dash_bootstrap_components as dbc

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    title="Net Explorer",
    suppress_callback_exceptions=True,
)

from frontend.layouts.main_layout import layout
from frontend.callbacks import network_callbacks  # noqa: F401 — registers callbacks

app.layout = layout
