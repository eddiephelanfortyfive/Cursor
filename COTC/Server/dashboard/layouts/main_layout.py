import dash_bootstrap_components as dbc
from dash import dcc, html
from dashboard.app import LAST_UPDATE_TIME
from dashboard.components.header import create_header
from dashboard.utils.config import CARD_STYLE

def create_layout():
    """Create the main dashboard layout"""
    return html.Div([
        # Data stores
        html.Div([
            dcc.Store(id='device-store', storage_type='memory'),
            dcc.Store(id='stock-symbols-store', storage_type='memory'),
            dcc.Store(id='last-update-time-store', storage_type='memory'),
            dcc.Store(id='refresh-animation-store', data={'animating': False}, storage_type='memory'),
            dcc.Store(id='cpu-history-data-store', storage_type='memory'),
            dcc.Store(id='ram-history-data-store', storage_type='memory'),
        ], style={'display': 'none'}),
        
        # Intervals for auto-refresh
        dcc.Interval(id='interval-component', interval=30*1000, n_intervals=0),  # Auto-refresh every 30 seconds
        dcc.Interval(id='update-symbols-interval', interval=60*1000, n_intervals=0),  # Update symbols every 60 seconds
        dcc.Interval(id='clock-interval', interval=1000, n_intervals=0),  # Clock update every second
        dcc.Interval(id='device-update-interval', interval=60*1000, n_intervals=0),  # Update devices list every minute
        dcc.Interval(id='history-update-interval', interval=30*1000, n_intervals=0),  # Update history data every 30 seconds
        
        # Add a store for page reload
        dcc.Store(id='reload-trigger', data=0),
        
        # Header
        create_header(),
        
        # Main content
        dbc.Container([
            # System Metrics Section
            dbc.Row([
                # CPU Usage Card
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5("CPU Usage", className="card-title mb-0"),
                            dbc.Button(
                                "History",
                                id="toggle-cpu-history",
                                color="link",
                                size="sm",
                                className="ms-2 float-end"
                            ),
                        ]),
                        dbc.CardBody([
                            dcc.Graph(
                                id='cpu-gauge',
                                config={'displayModeBar': False}
                            ),
                        ]),
                        # CPU History section (initially hidden)
                        html.Div(
                            id='cpu-history-container',
                            style={"display": "none"},
                            className="mt-3 border-top pt-3"
                        ),
                    ], style=CARD_STYLE)
                ], md=6),
                
                # RAM Usage Card
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5("RAM Usage", className="card-title mb-0"),
                            dbc.Button(
                                "History",
                                id="toggle-ram-history",
                                color="link",
                                size="sm",
                                className="ms-2 float-end"
                            ),
                        ]),
                        dbc.CardBody([
                            dcc.Graph(
                                id='ram-gauge',
                                config={'displayModeBar': False}
                            ),
                        ]),
                        # RAM History section (initially hidden)
                        html.Div(
                            id='ram-history-container',
                            style={"display": "none"},
                            className="mt-3 border-top pt-3"
                        ),
                    ], style=CARD_STYLE)
                ], md=6),
            ]),
            
            # Stock Data Section
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5("Stock Data Tracker", className="card-title mb-0"),
                        ]),
                        dbc.CardBody([
                            # Add Symbol Form
                            dbc.Row([
                                dbc.Col([
                                    dbc.InputGroup([
                                        dbc.Input(
                                            id='stock-symbol-input',
                                            type='text',
                                            placeholder='Enter stock symbol',
                                            style={'textTransform': 'uppercase'}
                                        ),
                                        dbc.Button(
                                            "Add Symbol", 
                                            id='add-symbol-button',
                                            color="primary"
                                        ),
                                    ], size="md"),
                                    html.Div(
                                        id='stock-symbol-status',
                                        className="mt-2 small"
                                    ),
                                ], md=6),
                                dbc.Col([
                                    dbc.FormText("Select an existing symbol:"),
                                    dcc.Dropdown(
                                        id='stock-symbol-dropdown',
                                        placeholder='Select a stock symbol',
                                        persistence=True,
                                        persistence_type='local',
                                        className="mb-3",
                                        loading_state={'is_loading': True, 'component_name': 'stock-symbol-dropdown'},
                                    ),
                                ], md=6)
                            ]),
                            
                            html.Hr(),
                            
                            # Stock Data Display
                            html.Div(
                                id='current-price', 
                                className="stock-price-display text-center my-4"
                            ),
                            
                            # Stock Price History
                            html.Div([
                                html.H6("Price History", className="mb-3"),
                                html.Div(
                                    id='stock-price-history',
                                    className="stock-history-container"
                                ),
                            ]),
                        ]),
                    ], style=CARD_STYLE),
                ], md=12),
            ]),
            
            # Footer
            dbc.Row([
                dbc.Col([
                    html.Footer([
                        html.P(
                            "System Monitoring Dashboard © 2023",
                            className="text-center text-muted small mt-4 mb-2"
                        ),
                    ])
                ])
            ]),
        ]),
    ], className="dash-template") 