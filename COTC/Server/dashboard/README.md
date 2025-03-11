# Dashboard Module

This directory contains a modular Dash application for monitoring system metrics and device information.

## Directory Structure

```
dashboard/
├── app.py                  # Main application initialization
├── index.py                # Entry point for starting the dashboard
├── assets/                 # Static assets (CSS, JS, images)
│   ├── clientside.js       # Client-side JavaScript functions
│   └── custom.css          # Custom CSS styles
├── components/             # UI components
│   ├── __init__.py
│   ├── header.py           # Header/navbar component
│   └── charts.py           # Chart components (gauges, etc.)
├── layouts/                # Layout modules
│   ├── __init__.py
│   └── main_layout.py      # Main dashboard layout
├── callbacks/              # Callback modules
│   ├── __init__.py
│   ├── device_callbacks.py       # Device selection callbacks
│   ├── system_metrics_callbacks.py  # System metrics callbacks
│   ├── history_callbacks.py      # History data callbacks
│   └── page_callbacks.py         # Page-level callbacks (refresh, etc.)
└── utils/                  # Utility modules
    ├── __init__.py
    └── config.py           # Configuration handling
```

## Running the Dashboard

To start the dashboard, run:

```bash
python -m dashboard.index
```

## Configuration

The dashboard is configured using `config.json` in the `config` directory. See `utils/config.py` for configuration handling details.

## Features

- Device selection with automatic metrics updating
- Real-time CPU and RAM usage monitoring
- Historical data viewing for system metrics
- Page refresh functionality
- Responsive design for various screen sizes
- Light/dark mode support

## Dependencies

- dash
- dash-bootstrap-components
- plotly
- requests

## API Integration

The dashboard integrates with a REST API for fetching device and metrics data. API endpoints are configured in `utils/config.py`. 