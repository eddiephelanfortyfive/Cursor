# System Monitoring Client Agent

This client agent collects system metrics (CPU and RAM usage) from your local machine and sends them to a central monitoring server.

## Setup

1. Make sure you have Python 3.6+ installed on your system
2. Install the required dependencies:
   ```
   pip install requests psutil getmac
   ```

## Configuration

Edit the `client_config.json` file to configure the client:

```json
{
    "server_url": "http://your-server-url:5000",
    "collection_interval": 60,
    "debug": true
}
```

- `server_url`: The URL of your monitoring server
- `collection_interval`: How often to collect and send metrics (in seconds)
- `debug`: Set to true for verbose logging

## Running the Client

Run the client using:

```
python run_client.py
```

The client will:
1. Register your device with the server
2. Collect system metrics at the specified interval
3. Send the metrics to the server

## Running as a Background Service

### On Linux/macOS

Create a systemd service or use cron to run the client in the background.

Example systemd service file (`/etc/systemd/system/system-monitor-client.service`):

```
[Unit]
Description=System Monitoring Client
After=network.target

[Service]
ExecStart=/usr/bin/python3 /path/to/run_client.py
WorkingDirectory=/path/to/client/directory
Restart=always
User=yourusername

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```
sudo systemctl enable system-monitor-client
sudo systemctl start system-monitor-client
```

### On Windows

You can use Task Scheduler to run the client at startup.

1. Open Task Scheduler
2. Create a new task
3. Set it to run at startup
4. Action: Start a program
5. Program/script: `python`
6. Arguments: `run_client.py`
7. Start in: `C:\path\to\client\directory` 