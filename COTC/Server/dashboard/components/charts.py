import plotly.graph_objects as go
from dashboard.utils.config import COLORS

def create_gauge_figure(title, value, color):
    """Create a gauge chart for system metrics"""
    value = round(value, 1) if value is not None else 0
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={'font': {'size': 28, 'color': color}},
        title={'text': title, 'font': {'size': 16}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "gray"},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
        }
    ))
    
    fig.update_layout(
        margin=dict(l=20, r=20, t=70, b=20),
        height=280,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def create_error_gauge(title):
    """Create an error state gauge chart"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=0,
        number={'font': {'size': 24, 'color': COLORS['danger']}, 'suffix': ' Error'},
        title={'text': title, 'font': {'size': 16}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "gray"},
            'bar': {'color': COLORS['danger']},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
        }
    ))
    
    fig.update_layout(
        margin=dict(l=20, r=20, t=70, b=20),
        height=280,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def get_color_based_on_value(value):
    """Return an appropriate color based on the metric value"""
    if value is None:
        return COLORS['secondary']
    
    value = float(value) if value is not None else 0
    
    if value > 80:
        return COLORS['danger']
    elif value > 50:
        return COLORS['warning']
    else:
        return COLORS['success'] 