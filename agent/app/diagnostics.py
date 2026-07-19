# app/diagnostics.py
# On-demand network diagnostic tools: ping, traceroute, DNS lookup,
# port check, and HTTP check. Each function takes a target and returns
# a plain dict — this shape gets stored directly in the diagnostic_runs
# table's JSONB "result" column, so no fixed schema is needed here.

import subprocess
import socket
import time
import requests
import dns.resolver


def run_ping(target: str) -> dict:
    # Uses the system's built-in `ping` command rather than a Python
    # ping library, since raw ICMP sockets need root/admin privileges
    # on most systems — shelling out to `ping` avoids that entirely.
    try:
        result = subprocess.run(
            ["ping", "-c", "4", target],  # -c 4 = send 4 packets, then stop
            capture_output=True,
            text=True,
            timeout=10,
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "ping timed out"}


def run_traceroute(target: str) -> dict:
    # Same approach as ping — shells out to the system's traceroute,
    # since implementing raw traceroute in Python also needs elevated
    # permissions.
    try:
        result = subprocess.run(
            ["traceroute", "-m", "15", target],  # -m 15 = max 15 hops
            capture_output=True,
            text=True,
            timeout=60,
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "traceroute timed out"}


def run_dns_lookup(target: str) -> dict:
    # Resolves A records (IPv4 addresses) for a given hostname.
    try:
        answers = dns.resolver.resolve(target, "A")
        return {
            "success": True,
            "addresses": [str(rdata) for rdata in answers],
        }
    except dns.resolver.NXDOMAIN:
        return {"success": False, "error": "domain does not exist"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def run_port_check(target: str, port: int) -> dict:
    # Attempts a raw TCP connection to a specific host:port to check
    # if something is listening there. No extra libraries needed —
    # this is what socket.connect_ex is built for.
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((target, port))  # 0 = success, nonzero = failed/closed
        sock.close()
        return {
            "success": result == 0,
            "port": port,
            "open": result == 0,
        }
    except socket.gaierror:
        return {"success": False, "error": "could not resolve hostname"}


def run_http_check(target: str) -> dict:
    # Makes an HTTP GET request and reports status code + response time.
    # target should be a full URL, e.g. "https://example.com".
    try:
        start = time.time()
        response = requests.get(target, timeout=10)
        elapsed_ms = round((time.time() - start) * 1000, 2)
        return {
            "success": response.ok,
            "status_code": response.status_code,
            "response_time_ms": elapsed_ms,
        }
    except requests.RequestException as e:
        return {"success": False, "error": str(e)}