import dash
from dashboard.app import app
from dashboard.utils.config import COLORS, TABLE_STYLE
from dash import dcc, html, Input, Output, dash_table, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import requests
from datetime import datetime
import logging


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
        # Fetch symbols on initial load
        try:
            symbols_response = requests.get('http://127.0.0.1:5000/metrics/stock/symbols')
            symbols_response.raise_for_status()
            symbols = symbols_response.json()
            options = [{'label': sym, 'value': sym} for sym in symbols]
            return "", options, options, dash.no_update
        except requests.exceptions.RequestException as e:
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
            # Set the symbol as pending for clients to poll
            pending_response = requests.post(
                'http://127.0.0.1:5000/metrics/stock/set_pending',
                json={'symbol': symbol}
            )
            
            if pending_response.status_code == 200:
                status_message = f"Symbol {symbol} set for polling"
                status_div = html.Div(status_message, className="text-success")
                logging.info(f"Set pending stock symbol: {symbol}")
                
                # Fetch updated symbols list
                symbols_response = requests.get('http://127.0.0.1:5000/metrics/stock/symbols')
                symbols = symbols_response.json()
                options = [{'label': sym, 'value': sym} for sym in symbols]
                
                return status_div, options, options, ""
            else:
                error_data = pending_response.json()
                status_message = error_data.get('error', 'Failed to set symbol for polling')
                status_div = html.Div(status_message, className="text-danger")
                return status_div, dash.no_update, dash.no_update, ""
                
        except requests.exceptions.RequestException as e:
            status_message = f"Error: {str(e)}"
            status_div = html.Div(status_message, className="text-danger")
            return status_div, dash.no_update, dash.no_update, ""
    
    elif triggered_input == 'update-symbols-interval':
        # Periodically update the symbols list
        try:
            symbols_response = requests.get('http://127.0.0.1:5000/metrics/stock/symbols')
            symbols = symbols_response.json()
            options = [{'label': sym, 'value': sym} for sym in symbols]
            return dash.no_update, options, options, dash.no_update
        except:
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
        # Fetch latest stock data
        response = requests.get(f'http://127.0.0.1:5000/metrics/stock/{symbol}')
        if response.status_code == 200:
            stock_data = response.json()
            if not stock_data:
                return html.Div(f"No data found for {symbol}", className="text-muted text-center p-4"), ""
                
            # Parse and round the timestamp to the nearest second
            timestamp = datetime.fromisoformat(stock_data['timestamp']).replace(microsecond=0)
            
            # Determine price color based on value (could be based on daily change instead)
            price_color = COLORS['success']  # Default to green for now
            
            latest_data_display = html.Div([
                html.Div(symbol, className="h2 fw-bold"),
                html.Div(f"${stock_data['price']:.2f}", className="display-3 fw-bold", style={'color': price_color}),
                html.Div(f"Last Updated: {timestamp}", className="text-muted small")
            ], className="text-center")

            # Fetch historical stock data
            history_response = requests.get(f'http://127.0.0.1:5000/metrics/stock/history/{symbol}')
            if history_response.status_code == 200:
                history_data = history_response.json()
                if not history_data:
                    return latest_data_display, html.Div("No historical data available", className="text-muted text-center")
                    
                # Create a DataTable of historical data with enhanced styling
                table = dash_table.DataTable(
                    columns=[
                        {'name': 'Date', 'id': 'timestamp'},
                        {
                            'name': 'Price ($)', 
                            'id': 'price',
                            'type': 'numeric',
                            'format': {'specifier': '$.2f'}
                        }
                    ],
                    data=history_data,
                    page_size=10,
                    style_table=TABLE_STYLE,
                    style_cell={
                        'textAlign': 'left',
                        'padding': '8px',
                        'fontFamily': 'Arial, sans-serif'
                    },
                    style_header={
                        'fontWeight': 'bold',
                        'backgroundColor': '#f8f9fa',
                        'borderBottom': '1px solid #dee2e6'
                    },
                    style_data_conditional=[
                        {'if': {'row_index': 'odd'}, 'backgroundColor': '#f9f9f9'}
                    ],
                    sort_action='native',
                    filter_action='native',
                    sort_by=[{'column_id': 'timestamp', 'direction': 'desc'}]
                )
                return latest_data_display, table
            else:
                error_msg = html.Div("Error fetching historical data", className="text-danger text-center")
                return latest_data_display, error_msg
        else:
            error_msg = html.Div(f"Error fetching stock data for {symbol}", className="text-danger text-center p-4")
            return error_msg, ""
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching stock data: {e}")
        error_msg = html.Div(f"Error: {str(e)}", className="text-danger text-center p-4")
        return error_msg, ""