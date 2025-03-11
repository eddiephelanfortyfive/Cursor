"""
Callback modules for the dashboard.
"""

# Import all callback modules to register their callbacks
from dashboard.callbacks import device_callbacks
from dashboard.callbacks import system_metrics_callbacks
from dashboard.callbacks import history_callbacks
from dashboard.callbacks import page_callbacks
from dashboard.callbacks import stock_callbacks


# This allows importing like: from dashboard.callbacks import device_callbacks 