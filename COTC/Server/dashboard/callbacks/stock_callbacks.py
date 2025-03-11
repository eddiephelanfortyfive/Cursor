import dash
from dashboard.app import app
from dashboard.utils.config import COLORS, TABLE_STYLE
from dash import dcc, html, Input, Output, dash_table, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from datetime import datetime
import logging
import json
import os
from database.models import (
    fetch_stock_symbols,
    fetch_latest_stock_data,
    get_stock_history
)
from api.endpoints import set_pending_stock_symbol_direct

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

# Get the absolute path to the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load configuration
config_path = os.path.join(PROJECT_ROOT, 'config', 'config.json')
with open(config_path) as config_file:
    config = json.load(config_file)

# Update database path to be absolute
if not os.path.isabs(config['database_path']):
    DATABASE_PATH = os.path.join(PROJECT_ROOT, config['database_path'])
else:
    DATABASE_PATH = config['database_path']

# Combined callback to set initial stock symbols, add new symbols, and periodically update dropdown
@app.callback(
    [Output('stock-symbol-status', 'children'),
     Output('stock-symbol-dropdown', 'options'),
     Output('stock-symbols-store', 'data'),
     Output('stock-symbol-input', 'value', allow_duplicate=True)],
    [Input('add-symbol-button', 'n_clicks'),
     Input('update-symbols-interval', 'n_intervals'),
     Input('stock-symbols-store', 'data')],
    [State('stock-symbol-input', 'value')]
)
def manage_stock_symbols(n_clicks, n_intervals, store_data, symbol):
    ctx = dash.callback_context
    # If this is the initial call (page load) or no specific trigger
    if not ctx.triggered or ctx.triggered[0]['prop_id'].split('.')[0] == '':
        # Fetch symbols on initial load directly from database
        try:
            symbols = fetch_stock_symbols(DATABASE_PATH)
            options = [{'label': sym, 'value': sym} for sym in symbols]
            return "", options, options, dash.no_update
        except Exception as e:
            logging.error(f"Error fetching stock symbols: {e}")
            return "Error fetching stock symbols.", [], [], dash.no_update

    triggered_input = ctx.triggered[0]['prop_id'].split('.')[0]
    status_message = ""

    if triggered_input == 'add-symbol-button' and n_clicks and symbol:
        # Clean and validate input - symbol is already uppercase from the other callback
        symbol = symbol.strip()
        
        if not symbol:
            status_message = "Symbol cannot be empty."
            status_div = html.Div(status_message, className="text-danger")
            return status_div, dash.no_update, dash.no_update, ""
        
        if not symbol.isalpha() and not all(c.isalnum() or c == '.' for c in symbol):
            status_message = "Invalid symbol format."
            status_div = html.Div(status_message, className="text-danger")
            return status_div, dash.no_update, dash.no_update, ""
        
        try:
            # Set the pending symbol directly using the function
            result = set_pending_stock_symbol_direct(symbol)
            
            if result["success"]:
                status_message = f"Symbol {symbol} set for polling"
                status_div = html.Div(status_message, className="text-success")
                logging.info(f"Set pending stock symbol: {symbol}")
                
                # Fetch updated symbols list directly from the database
                symbols = fetch_stock_symbols(DATABASE_PATH)
                options = [{'label': sym, 'value': sym} for sym in symbols]
                
                return status_div, options, options, ""
            else:
                status_message = result.get("error", "Failed to set symbol for polling")
                status_div = html.Div(status_message, className="text-danger")
                return status_div, dash.no_update, dash.no_update, ""
                
        except Exception as e:
            status_message = f"Error: {str(e)}"
            status_div = html.Div(status_message, className="text-danger")
            return status_div, dash.no_update, dash.no_update, ""
    
    elif triggered_input == 'update-symbols-interval':
        # Periodically update the symbols list from the database
        try:
            symbols = fetch_stock_symbols(DATABASE_PATH)
            options = [{'label': sym, 'value': sym} for sym in symbols]
            return dash.no_update, options, options, dash.no_update
        except Exception as e:
            logger.error(f"Error updating symbols: {e}")
            # Don't show error for background updates
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    # Default return for other cases
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update

# Callback to display latest stock data with a large number and update the table
@app.callback(
    [Output('current-price', 'children'),
     Output('stock-price-history', 'children')],
    [Input('stock-symbol-dropdown', 'value')]
)
def display_latest_stock_data_and_table(symbol):
    if not symbol:
        return html.Div("Select a stock symbol to view data", className="text-muted text-center p-4"), ""
    
    try:
        # Fetch latest stock data directly from the database
        latest_data = fetch_latest_stock_data(DATABASE_PATH, symbol)
        
        if latest_data:
            # Format the price display
            price = latest_data['price']
            timestamp = latest_data['timestamp']
            
            # Create a big number display
            price_display = html.Div([
                html.H2(f"${price:.2f}", className="mb-0 display-4 fw-bold"),
                html.P(f"Last updated: {timestamp}", className="text-muted small")
            ], className="text-center py-4")
            
            # Fetch historical data
            history = get_stock_history(DATABASE_PATH, symbol)
            
            if history:
                # Create a data table with the history
                table_data = []
                for item in history:
                    try:
                        # Try to parse the timestamp and format it nicely
                        if isinstance(item['timestamp'], str):
                            if 'T' in item['timestamp']:
                                # Parse ISO format timestamp
                                timestamp_parts = item['timestamp'].split('T')
                                date_part = timestamp_parts[0]
                                time_part = timestamp_parts[1].split('.')[0] if '.' in timestamp_parts[1] else timestamp_parts[1]
                                formatted_timestamp = f"{date_part} {time_part}"
                            else:
                                # Already a simple format
                                formatted_timestamp = item['timestamp']
                        else:
                            # Handle datetime object
                            formatted_timestamp = item['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                            
                        # Format the price with dollar sign and 2 decimal places
                        formatted_price = f"${float(item['price']):.2f}"
                        
                        table_data.append({
                            "timestamp": formatted_timestamp,
                            "price": formatted_price
                        })
                    except Exception as e:
                        logger.error(f"Error formatting history item: {e}")
                        # Skip this item if there's an error
                        continue
                
                # Sort the data by timestamp (newest first) but show all entries
                table_data = sorted(table_data, key=lambda x: x['timestamp'], reverse=True)
                
                # Count the total number of entries
                total_entries = len(table_data)
                
                table = html.Div([
                    html.H4(f"Price History ({total_entries} entries)", className="mb-3"),
                    dash_table.DataTable(
                        id='stock-history-table',
                        columns=[
                            {"name": "Timestamp", "id": "timestamp"},
                            {"name": "Price", "id": "price"}
                        ],
                        data=table_data,
                        style_table=TABLE_STYLE['table'],
                        style_cell=TABLE_STYLE['cell'],
                        style_header=TABLE_STYLE['header'],
                        style_data=TABLE_STYLE['data'],
                        style_data_conditional=TABLE_STYLE['conditional'],
                        # Add pagination to handle large datasets
                        page_size=25,
                        page_action="native",
                        sort_action="native",
                        sort_mode="multi",
                        filter_action="native",
                    )
                ], className="mt-4")
                
                return price_display, table
            
            return price_display, html.Div("No historical data available", className="text-muted text-center p-3")
        else:
            # No data available
            no_data = html.Div([
                html.H4("No data available", className="text-muted"),
                html.P("The requested stock symbol has no price data yet.")
            ], className="text-center p-4")
            
            return no_data, ""
            
    except Exception as e:
        logger.error(f"Error fetching stock data: {e}")
        error_msg = html.Div([
            html.H4("Error", className="text-danger"),
            html.P(f"Could not fetch data for {symbol}: {str(e)}")
        ], className="text-center p-4")
        
        return error_msg, ""

# Callback to update the stock price chart
@app.callback(
    Output('stock-price-chart', 'figure'),
    [Input('stock-symbol-dropdown', 'value')]
)
def update_stock_chart(symbol):
    if not symbol:
        # Return empty figure
        fig = go.Figure()
        fig.update_layout(
            title="Select a Stock Symbol",
            xaxis_title="Date",
            yaxis_title="Price",
            template="plotly_white",
            height=400,
            showlegend=False
        )
        return fig
    
    try:
        # Fetch stock history directly from the database
        history = get_stock_history(DATABASE_PATH, symbol)
        
        if history:
            # Extract data for plotting
            dates = []
            prices = []
            
            for item in history:
                try:
                    # Try to convert timestamp to datetime
                    if isinstance(item['timestamp'], str):
                        # Parse the timestamp
                        dates.append(item['timestamp'])
                    else:
                        # Already a datetime object
                        dates.append(item['timestamp'].isoformat())
                    
                    # Convert price to float
                    prices.append(float(item['price']))
                except Exception as e:
                    logger.error(f"Error processing history item for chart: {e}")
                    # Skip this item if there's an error
                    continue
            
            # Create the line chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates, 
                y=prices,
                mode='lines+markers',
                name=symbol,
                line=dict(color=COLORS['primary'], width=2),
                marker=dict(color=COLORS['primary'], size=5),
            ))
            
            # Update layout
            fig.update_layout(
                title=f"{symbol} Price History ({len(dates)} data points)",
                xaxis_title="Date",
                yaxis_title="Price ($)",
                template="plotly_white",
                height=500,  # Increase height for better visibility
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=12,
                    font_family="Arial"
                ),
                showlegend=False,
                # Add range slider for easy navigation of historical data
                xaxis=dict(
                    rangeslider=dict(visible=True),
                    type='date'
                )
            )
            
            # Add hover data formatting
            fig.update_traces(
                hovertemplate="<b>Date:</b> %{x}<br><b>Price:</b> $%{y:.2f}<extra></extra>"
            )
            
            return fig
        else:
            # No data available
            fig = go.Figure()
            fig.update_layout(
                title=f"No Data Available for {symbol}",
                xaxis_title="Date",
                yaxis_title="Price",
                template="plotly_white",
                height=400,
                showlegend=False
            )
            return fig
            
    except Exception as e:
        logger.error(f"Error creating stock chart: {e}")
        # Return error figure
        fig = go.Figure()
        fig.update_layout(
            title=f"Error Loading Data for {symbol}",
            xaxis_title="Date",
            yaxis_title="Price",
            template="plotly_white",
            height=400,
            showlegend=False
        )
        return fig

# Callback to handle polling for stock price updates
@app.callback(
    Output('polling-status', 'children'),
    [Input('polling-interval', 'n_intervals')]
)
def update_polling_status(n_intervals):
    """
    This callback doesn't need to be changed as it's just displaying UI elements.
    The actual polling happens on the client side.
    """
    if n_intervals:
        return [
            html.Span("✓", className="text-success me-2"),
            f"Polling active (every {n_intervals} intervals)"
        ]
    return [
        html.Span("○", className="text-muted me-2"),
        "Polling inactive"
    ]