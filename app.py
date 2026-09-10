import json
import importlib
import logging
import sys
import time
import uuid
from flask import Flask, g, jsonify, request
try:
    prometheus_client = importlib.import_module("prometheus_client")
    CONTENT_TYPE_LATEST = prometheus_client.CONTENT_TYPE_LATEST
    Counter = prometheus_client.Counter
    generate_latest = prometheus_client.generate_latest
except ModuleNotFoundError:
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"

    class Counter:
        def __init__(self, name, description, label_names):
            self.name = name
            self.description = description
            self.label_names = label_names
            self.values = {}

        def labels(self, *label_values):
            key = tuple(label_values)
            counter = self

            class LabelCounter:
                def inc(self):
                    counter.values[key] = counter.values.get(key, 0) + 1

            return LabelCounter()

    def generate_latest():
        lines = [
            f"# HELP {REQUESTS.name} {REQUESTS.description}",
            f"# TYPE {REQUESTS.name} counter",
        ]
        for label_values, value in REQUESTS.values.items():
            labels = ",".join(
                f'{name}="{label}"'
                for name, label in zip(REQUESTS.label_names, label_values)
            )
            lines.append(f"{REQUESTS.name}{{{labels}}} {value}")
        return ("\n".join(lines) + "\n").encode()

app = Flask(__name__)

tasks = {}
next_id = 1

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(message)s")
log = logging.getLogger("taskflow")

REQUESTS = Counter("taskflow_requests_total", "HTTP requests", ["method", "path", "status"])


@app.before_request
def start_timer():
    g.start = time.time()
    g.trace_id = request.headers.get("X-Trace-Id", uuid.uuid4().hex[:8])


@app.after_request
def log_request(response):
    log.info(json.dumps({
        "level": "info", "event": "http.request",
        "method": request.method, "path": request.path,
        "status": response.status_code,
        "duration_ms": round((time.time() - g.start) * 1000, 1),
        "trace_id": g.trace_id,
    }))
    return response


@app.after_request
def count_request(response):
    REQUESTS.labels(request.method, request.path, response.status_code).inc()
    return response


@app.get("/health")
def health():
    return jsonify(status="ok"), 200


@app.post("/tasks")
def create_task():
    global next_id
    data = request.get_json(silent=True) or {}
    title = data.get("title")
    if not title:
        return jsonify(error="title is required"), 400
    task = {"id": next_id, "title": title, "done": False}
    tasks[next_id] = task
    next_id += 1
    return jsonify(task), 201


@app.get("/tasks")
def list_tasks():
    return jsonify(list(tasks.values())), 200


@app.put("/tasks/<int:task_id>/complete")
def complete_task(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify(error="not found"), 404
    task["done"] = True
    return jsonify(task), 200


@app.get("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
