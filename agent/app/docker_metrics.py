# app/docker_metrics.py
# Detects running Docker containers on this host (if Docker is present)
# and collects basic resource stats for each one. Returns an empty list
# if Docker isn't installed/running — this lets the agent work fine on
# machines with no Docker at all (like a plain VM).

import docker
from docker.errors import DockerException

def get_docker_containers() -> list[dict]:
    # Returns one dict per running container: name and basic stats.
    # Fails gracefully (returns []) if Docker isn't available.
    try:
        client = docker.from_env()
        client.ping()  # confirms the Docker daemon is actually reachable
    except DockerException:
        return []

    containers_data = []
    for container in client.containers.list():  # only running containers
        stats = container.stats(stream=False)  # one-shot stats snapshot

        # CPU percent calculation — Docker's raw stats give cumulative
        # CPU time, not a direct percentage, so we compute the delta
        # between the container and system CPU usage.
        cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
        system_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
        cpu_percent = (cpu_delta / system_delta) * 100 if system_delta > 0 else 0.0

        # Memory percent — usage vs. the limit Docker allocated to this container.
        mem_usage = stats["memory_stats"]["usage"]
        mem_limit = stats["memory_stats"]["limit"]
        memory_percent = (mem_usage / mem_limit) * 100 if mem_limit > 0 else 0.0

        containers_data.append({
            "name": container.name,
            "cpu_percent": round(cpu_percent, 2),
            "memory_percent": round(memory_percent, 2),
        })

    return containers_data