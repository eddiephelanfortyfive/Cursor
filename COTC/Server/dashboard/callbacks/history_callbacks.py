import dash
from dash.dependencies import Input, Output, State
from dash import html, dash_table
import logging
import requests
from dashboard.app import app
from dashboard.utils.config import API_BASE_URL, TABLE_STYLE
from datetime import datetime

# Callback to update CPU history data
@app.callback(
    [Output('cpu-history-data-store', 'data')],
    [Input('history-update-interval', 'n_intervals'),
     Input('device-store', 'data')],
    prevent_initial_call=False
)
def update_cpu_history_data(n_intervals, device_data):
    """Update the CPU history data store"""
    if not device_data or not device_data.get('device_id'):
        return [[]]  # Return empty data if no device selected
    
    device_id = device_data.get('device_id')
    
    try:
        # Fetch CPU history data - use the general history endpoint
        api_url = f'{API_BASE_URL}/metrics/system/history/cpu_usage?device_id={device_id}'
        response = requests.get(api_url)
        
        if response.status_code == 200:
            history_data = response.json()
            
            # Ensure we have a list
            if not isinstance(history_data, list):
                history_data = [history_data] if history_data else []
                
            # Filter to only include CPU usage metrics
            filtered_data = [item for item in history_data if item.get('metric_name') == 'cpu_usage']
            
            # Return the filtered data wrapped in a list
            return [[filtered_data]]
            
    except Exception as e:
        logging.error(f"Error fetching CPU history data: {e}")
    
    return [[]]

# Callback to update RAM history data
@app.callback(
    [Output('ram-history-data-store', 'data')],
    [Input('history-update-interval', 'n_intervals'),
     Input('device-store', 'data')],
    prevent_initial_call=False
)
def update_ram_history_data(n_intervals, device_data):
    """Update the RAM history data store"""
    if not device_data or not device_data.get('device_id'):
        return [[]]  # Return empty data if no device selected
    
    device_id = device_data.get('device_id')
    
    try:
        # Fetch RAM history data - use the general history endpoint
        api_url = f'{API_BASE_URL}/metrics/system/history/ram_usage?device_id={device_id}'
        response = requests.get(api_url)
        
        if response.status_code == 200:
            history_data = response.json()
            
            # Ensure we have a list
            if not isinstance(history_data, list):
                history_data = [history_data] if history_data else []
                
            # Filter to only include RAM usage metrics
            filtered_data = [item for item in history_data if item.get('metric_name') == 'ram_usage']
            
            # Return the filtered data wrapped in a list
            return [[filtered_data]]
            
    except Exception as e:
        logging.error(f"Error fetching RAM history data: {e}")
    
    return [[]]

# Callback to toggle CPU history table visibility
@app.callback(
    [Output('cpu-history-container', 'style'),
     Output('cpu-history-container', 'children'),
     Output('toggle-cpu-history', 'children')],
    [Input('toggle-cpu-history', 'n_clicks'),
     Input('cpu-history-data-store', 'data')],
    [State('cpu-history-container', 'style'),
     State('device-store', 'data')]
)
def toggle_cpu_history(n_clicks, history_data, current_style, device_data):
    """Toggle visibility of CPU history data and update the table"""
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    
    # Get device information
    device_id = device_data.get('device_id') if device_data else None
    device_hostname = device_data.get('hostname', 'No Device Selected') if device_data else 'No Device Selected'
    
    # If toggle button wasn't clicked and we're just updating data, maintain current visibility
    if trigger_id != 'toggle-cpu-history' and current_style:
        is_visible = current_style.get("display") != "none"
        if not is_visible:
            return current_style, [], "Show History"
    else:
        # Check if the container is currently visible
        is_visible = current_style and current_style.get("display") != "none"
        if is_visible and trigger_id == 'toggle-cpu-history':
            return {"display": "none"}, [], "Show History"
    
    # If no device is selected, show a message
    if not device_id:
        no_device_message = html.Div([
            html.H5("No device selected"),
            html.P("Please select a device to view CPU usage history.")
        ], className="text-center p-3")
        return {"display": "block"}, no_device_message, "Hide History"
    
    # Ensure history_data is a list and unwrap it
    if history_data and isinstance(history_data, list):
        history_data = history_data[0]  # Unwrap the list
    
    # Ensure data is a list
    if not isinstance(history_data, list):
        history_data = [history_data] if history_data else []
    
    # Create a DataTable with the history data
    if history_data:
        # Format the data for the table - create a new list to avoid modifying the original
        formatted_data = []
        for entry in history_data:
            if isinstance(entry, dict):
                formatted_data.append({
                    'timestamp': entry.get('timestamp', ''),
                    'metric_value': entry.get('metric_value', 0)
                })
        
        # Create the table
        table = dash_table.DataTable(
            id='cpu-history-table',
            columns=[
                {'name': 'Time', 'id': 'timestamp'},
                {
                    'name': 'CPU Usage (%)', 
                    'id': 'metric_value',
                    'type': 'numeric',
                    'format': {'specifier': '.2f'}
                }
            ],
            data=formatted_data,
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
        
        # Create the container with the table
        container = html.Div([
            html.H5(f"CPU Usage History - {device_hostname} ({len(formatted_data)} entries)"),
            table
        ], className="mt-4")
        
        return {"display": "block"}, container, "Hide History"
    else:
        # No history data available
        no_data_message = html.Div([
            html.H5(f"No CPU Usage History"),
            html.P(f"No CPU usage history data available for {device_hostname}.")
        ], className="text-center p-3")
        
        return {"display": "block"}, no_data_message, "Hide History"

# Callback to toggle RAM history table visibility
@app.callback(
    [Output('ram-history-container', 'style'),
     Output('ram-history-container', 'children'),
     Output('toggle-ram-history', 'children')],
    [Input('toggle-ram-history', 'n_clicks'),
     Input('ram-history-data-store', 'data')],
    [State('ram-history-container', 'style'),
     State('device-store', 'data')]
)
def toggle_ram_history(n_clicks, history_data, current_style, device_data):
    """Toggle visibility of RAM history data and update the table"""
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    
    # Get device information
    device_id = device_data.get('device_id') if device_data else None
    device_hostname = device_data.get('hostname', 'No Device Selected') if device_data else 'No Device Selected'
    
    # If toggle button wasn't clicked and we're just updating data, maintain current visibility
    if trigger_id != 'toggle-ram-history' and current_style:
        is_visible = current_style.get("display") != "none"
        if not is_visible:
            return current_style, [], "Show History"
    else:
        # Check if the container is currently visible
        is_visible = current_style and current_style.get("display") != "none"
        if is_visible and trigger_id == 'toggle-ram-history':
            return {"display": "none"}, [], "Show History"
    
    # If no device is selected, show a message
    if not device_id:
        no_device_message = html.Div([
            html.H5("No device selected"),
            html.P("Please select a device to view RAM usage history.")
        ], className="text-center p-3")
        return {"display": "block"}, no_device_message, "Hide History"
    
    # Ensure history_data is a list and unwrap it
    if history_data and isinstance(history_data, list):
        history_data = history_data[0]  # Unwrap the list
    
    # Ensure data is a list
    if not isinstance(history_data, list):
        history_data = [history_data] if history_data else []
    
    # Create a DataTable with the history data
    if history_data:
        # Format the data for the table - create a new list to avoid modifying the original
        formatted_data = []
        for entry in history_data:
            if isinstance(entry, dict):
                formatted_data.append({
                    'timestamp': entry.get('timestamp', ''),
                    'metric_value': entry.get('metric_value', 0)
                })
        
        # Create the table
        table = dash_table.DataTable(
            id='ram-history-table',
            columns=[
                {'name': 'Time', 'id': 'timestamp'},
                {
                    'name': 'RAM Usage (%)', 
                    'id': 'metric_value',
                    'type': 'numeric',
                    'format': {'specifier': '.2f'}
                }
            ],
            data=formatted_data,
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
        
        # Create the container with the table
        container = html.Div([
            html.H5(f"RAM Usage History - {device_hostname} ({len(formatted_data)} entries)"),
            table
        ], className="mt-4")
        
        return {"display": "block"}, container, "Hide History"
    else:
        # No history data available
        no_data_message = html.Div([
            html.H5(f"No RAM Usage History"),
            html.P(f"No RAM usage history data available for {device_hostname}.")
        ], className="text-center p-3")
        
        return {"display": "block"}, no_data_message, "Hide History"