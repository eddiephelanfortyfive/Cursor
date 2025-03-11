import dash_bootstrap_components as dbc
from dash import dcc, html

def create_header():
    """Create the header component with navigation and controls"""
    return dbc.Navbar(
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.Img(src="https://img.icons8.com/color/48/000000/dashboard.png", height="30px"),
                    dbc.NavbarBrand("System Monitoring Dashboard", className="ms-2 fw-bold"),
                ], width="auto"),
                dbc.Col([
                    html.Div([
                        html.Label("Device:", className="me-2"),
                        dcc.Dropdown(
                            id='device-selector',
                            placeholder="Select a device to view metrics",
                            style={'width': '300px', 'display': 'inline-block'},
                            persistence=True,
                            persistence_type='local',
                            clearable=True,
                            optionHeight=60,  # Increase option height for better visibility
                            maxHeight=400,    # Increase max height of dropdown menu
                            className="dropdown-menu-right"  # Align dropdown to the right
                        ),
                    ], className="d-flex align-items-center"),
                ], width="auto", className="ms-auto"),
                dbc.Col([
                    html.Span("Data last updated: ", className="me-2"),
                    html.Span(id="last-update-time", className="text-muted"),
                ], width="auto", className="me-3 d-none d-md-flex"),
                dbc.Col([
                    dbc.Button([
                        html.I(id="refresh-icon", className="fas fa-sync-alt me-2"),
                        "Refresh Data"
                    ], 
                    id="refresh-button", 
                    color="primary", 
                    size="sm", 
                    className="me-2"),
                ], width="auto"),
            ], align="center"),
        ]),
        color="light",
        className="mb-4 shadow-sm",
        sticky="top",
    ) 