# app/main.py
# Entry point for the agent. Registers this host with the API
# (if needed), then repeatedly collects metrics and sends them.

# app/main.py

import time
import requests
import threading

from app.config import settings
from app.metrics import collect_host_metrics
from app.docker_metrics import get_docker_containers
from app.diagnostic_listener import listen_for_diagnostics

HEADERS = {"X-Agent-Token": settings.agent_shared_token}

def main():
    host_id = get_or_create_host(settings.host_name, resource_type="bare_metal")

    # Start the diagnostic listener in the background so it can respond
    # to requests at any time, without blocking the metrics loop below.
    listener_thread = threading.Thread(
        target=listen_for_diagnostics,
        args=(host_id,),
        daemon=True,  # dies automatically when the main program exits
    )
    listener_thread.start()

    while True:
        send_host_metrics(host_id)
        send_docker_metrics(parent_host_id=host_id)
        time.sleep(settings.report_interval_seconds)

def get_or_create_host(name: str, resource_type: str, parent_host_id: int | None = None) -> int:
    # Generalized version of the old register_host(): checks if a host
    # (machine OR container) already exists by name, and reuses its id
    # if so. Otherwise registers it fresh. Used for both the top-level
    # machine and any Docker containers found on it.
    existing = requests.get(
        f"{settings.api_url}/hosts/{name}",
        headers=HEADERS,
    )
    if existing.status_code == 200:
        return existing.json()["id"]

    response = requests.post(
        f"{settings.api_url}/hosts",
        json={
            "name": name,
            "resource_type": resource_type,
            "parent_host_id": parent_host_id,
        },
        headers=HEADERS,
    )
    if response.status_code == 200:
        host = response.json()
        print(f"Registered host '{host['name']}' ({resource_type}) with id {host['id']}")
        return host["id"]
    else:
        raise RuntimeError(f"Failed to register host '{name}': {response.status_code} {response.text}")

def send_metric(host_id: int, metric_type: str, value: float):
    # Sends a single metric reading to the API.
    response = requests.post(
        f"{settings.api_url}/metrics",
        json={"host_id": host_id, "metric_type": metric_type, "value": value},
        headers=HEADERS,
    )
    if response.status_code == 200:
        print(f"Sent {metric_type} for host {host_id}: {value}")
    else:
        print(f"Failed to send {metric_type} for host {host_id}: {response.status_code} {response.text}")

def send_host_metrics(host_id: int):
    # Sends CPU/memory/disk readings for the main machine.
    for reading in collect_host_metrics():
        send_metric(host_id, reading["metric_type"], reading["value"])

def send_docker_metrics(parent_host_id: int):
    # Registers (or looks up) each running container as its own host,
    # nested under the machine it's running on, then sends its metrics.
    for container in get_docker_containers():
        container_host_id = get_or_create_host(
            name=container["name"],
            resource_type="docker",
            parent_host_id=parent_host_id,
        )
        send_metric(container_host_id, "cpu_percent", container["cpu_percent"])
        send_metric(container_host_id, "memory_percent", container["memory_percent"])



if __name__ == "__main__":
    main()