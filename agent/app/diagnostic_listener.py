# app/diagnostic_listener.py
# Subscribes to this host's Redis channel and runs whatever diagnostic
# is requested, then posts the result back to the API. Runs in its
# own background thread so it doesn't block the regular metrics loop.

import json
import redis
import requests

from app.config import settings
from app.diagnostics import (
    run_ping,
    run_traceroute,
    run_dns_lookup,
    run_port_check,
    run_http_check,
)

HEADERS = {"X-Agent-Token": settings.agent_shared_token}

# Maps the diagnostic_type string (from the message) to the actual
# function that runs it. Keeps the listener logic simple — just look
# up the function and call it, no long if/elif chain.
DIAGNOSTIC_FUNCTIONS = {
    "ping": lambda target: run_ping(target),
    "traceroute": lambda target: run_traceroute(target),
    "dns_lookup": lambda target: run_dns_lookup(target),
    "http_check": lambda target: run_http_check(target),
    # port_check needs a port number too — target format: "host:port".
    # Explicitly convert the port piece to int, since split() always
    # returns strings.
    "port_check": lambda target: run_port_check(
        target.split(":")[0], int(target.split(":")[1])
    ),
}


def report_result(diagnostic_run_id: int, result: dict):
    # Posts the completed diagnostic result back to the API, which
    # updates the matching diagnostic_runs row.
    response = requests.post(
        f"{settings.api_url}/diagnostics/{diagnostic_run_id}/result",
        json={"result": result},
        headers=HEADERS,
    )
    if response.status_code == 200:
        print(f"Reported result for diagnostic_run {diagnostic_run_id}")
    else:
        print(f"Failed to report result: {response.status_code} {response.text}")


def listen_for_diagnostics(host_id: int):
    # Blocks forever, listening on this host's specific channel.
    # Meant to be run in a background thread.
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    pubsub = redis_client.pubsub()
    channel = f"diagnostics:host:{host_id}"
    pubsub.subscribe(channel)
    print(f"Listening for diagnostics on '{channel}'")

    for message in pubsub.listen():
        if message["type"] != "message":
            continue  # skip the initial "subscribe" confirmation message

        payload = json.loads(message["data"])
        diagnostic_run_id = payload["diagnostic_run_id"]
        diagnostic_type = payload["diagnostic_type"]
        target = payload["target"]

        print(f"Received diagnostic request: {diagnostic_type} -> {target}")

        func = DIAGNOSTIC_FUNCTIONS.get(diagnostic_type)
        if not func:
            report_result(diagnostic_run_id, {"success": False, "error": f"unknown diagnostic_type: {diagnostic_type}"})
            continue

        try:
            result = func(target)
        except Exception as e:
            result = {"success": False, "error": f"diagnostic failed: {str(e)}"}

        report_result(diagnostic_run_id, result)