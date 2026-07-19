# app/metrics.py
# Uses psutil (a cross-platform library for reading system stats)
# to collect basic host health metrics: CPU, memory, and disk usage.

import psutil

def collect_host_metrics() -> list[dict]:
    # Returns a list of individual metric readings, matching the shape
    # the API's /metrics endpoint expects (one dict per reading).

    readings = []

    # CPU usage, sampled over a short interval for an accurate reading
    # (interval=1 makes psutil measure over 1 second instead of an instant snapshot)
    cpu_percent = psutil.cpu_percent(interval=1)
    readings.append({"metric_type": "cpu_percent", "value": cpu_percent})

    # Memory usage as a percentage of total RAM in use
    memory = psutil.virtual_memory()
    readings.append({"metric_type": "memory_percent", "value": memory.percent})

    # Disk usage for the root filesystem
    disk = psutil.disk_usage("/")
    readings.append({"metric_type": "disk_percent", "value": disk.percent})

    return readings