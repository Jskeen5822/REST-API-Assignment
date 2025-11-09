"""Run a short end-to-end demo against the FastAPI app.

This script starts the local server, exercises all ten endpoints with real HTTP
requests using httpx, prints the responses, and then shuts the server down.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Iterable

import httpx

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_IMPORT_PATH = "app.main:app"
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000
BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"


def _print_response(label: str, response: httpx.Response) -> None:
    body: Any
    try:
        body = response.json()
    except ValueError:
        body = response.text

    print("==>", label)
    print("status:", response.status_code)
    print("body:")
    if isinstance(body, (dict, list)):
        print(json.dumps(body, indent=2))
    else:
        print(body)
    print()


def _wait_for_server(timeout: float = 15.0) -> None:
    start = time.perf_counter()
    with httpx.Client() as client:
        while time.perf_counter() - start < timeout:
            try:
                client.get(BASE_URL + "/inventory", timeout=0.5)
            except httpx.HTTPError:
                time.sleep(0.2)
                continue
            return
    raise RuntimeError("Server did not become ready in time")


def _exercise_endpoints() -> None:
    with httpx.Client(base_url=BASE_URL) as client:
        _print_response("GET /inventory", client.get("/inventory"))

        widget = client.post(
            "/inventory",
            json={"name": "Widget", "quantity": 10, "price": 12.5},
        )
        _print_response("POST /inventory", widget)
        widget_id = widget.json()["id"]

        gadget = client.post(
            "/inventory",
            json={"name": "Gadget", "quantity": 5, "price": 32.0},
        )
        _print_response("POST /inventory (second)", gadget)

        inventory_full = client.get("/inventory")
        _print_response("GET /inventory (after inserts)", inventory_full)

        replace_widget = client.put(
            f"/inventory/{widget_id}",
            json={"name": "Widget", "quantity": 25, "price": 11.0},
        )
        _print_response("PUT /inventory/{id}", replace_widget)

        patch_widget = client.patch(
            f"/inventory/{widget_id}",
            json={"price": 9.99},
        )
        _print_response("PATCH /inventory/{id}", patch_widget)

        order = client.post(
            "/orders",
            json={
                "customer": "Ada Lovelace",
                "items": [widget_id, gadget.json()["id"]],
                "status": "pending",
            },
        )
        _print_response("POST /orders", order)
        order_id = order.json()["id"]

        order_detail = client.get(f"/orders/{order_id}")
        _print_response("GET /orders/{id}", order_detail)

        replace_order = client.put(
            f"/orders/{order_id}",
            json={
                "customer": "Ada Lovelace",
                "items": [gadget.json()["id"]],
                "status": "confirmed",
            },
        )
        _print_response("PUT /orders/{id}", replace_order)

        patch_order = client.patch(
            f"/orders/{order_id}",
            json={"status": "shipped"},
        )
        _print_response("PATCH /orders/{id}", patch_order)

        delete_order = client.delete(f"/orders/{order_id}")
        _print_response("DELETE /orders/{id}", delete_order)

        delete_widget = client.delete(f"/inventory/{widget_id}")
        _print_response("DELETE /inventory/{id}", delete_widget)


def _start_server() -> subprocess.Popen[Any]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    command: Iterable[str] = (
        sys.executable,
        "-m",
        "uvicorn",
        APP_IMPORT_PATH,
    )
    creationflags = 0
    if sys.platform == "win32":  # isolate console signals from parent process
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

    process = subprocess.Popen(
        command,
        cwd=REPO_ROOT,
        env=env,
        creationflags=creationflags,
    )
    return process


def main() -> None:
    server = _start_server()
    try:
        _wait_for_server()
        _exercise_endpoints()
    finally:
        if server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
        try:
            server.wait(timeout=1)
        except subprocess.TimeoutExpired:
            pass


if __name__ == "__main__":
    main()
