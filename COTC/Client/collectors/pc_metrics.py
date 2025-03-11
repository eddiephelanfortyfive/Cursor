"""
PC Metrics Collector

This module is responsible for collecting various system metrics from the local machine.
"""
import psutil
import logging

class PCMetricsCollector:
    def __init__(self, metrics_to_collect=None):
        """
        Initialize the PC metrics collector.
        
        Args:
            metrics_to_collect: List of metrics to collect. Defaults to CPU and RAM usage.
        """
        self.metrics_to_collect = metrics_to_collect or ["cpu_usage", "ram_usage"]
        
    def collect_metrics(self):
        """
        Collect all configured system metrics.
        
        Returns:
            Dict containing all collected metrics with their values.
        """
        metrics = {}
        
        # Collect each requested metric
        for metric in self.metrics_to_collect:
            try:
                if metric == "cpu_usage":
                    metrics[metric] = self.get_cpu_usage()
                elif metric == "ram_usage":
                    metrics[metric] = self.get_ram_usage()
            except Exception as e:
                logging.error(f"Error collecting {metric}: {e}")
                metrics[metric] = None
        
        return metrics
    
    def get_cpu_usage(self):
        """Get CPU usage percentage."""
        return psutil.cpu_percent(interval=1)
    
    def get_ram_usage(self):
        """Get RAM usage percentage."""
        return psutil.virtual_memory().percent