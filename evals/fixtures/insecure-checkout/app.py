#!/usr/bin/env python3
"""Deliberately flawed local fixture for RateMyCode execution evals."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


ORDERS = [
    {"id": "order-a", "user_id": "alice", "sku": "starter", "status": "paid"},
    {"id": "order-b", "user_id": "bob", "sku": "pro", "status": "paid"},
]


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/api/orders"):
            self.send_json(200, {"orders": ORDERS})
            return
        self.send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/checkout":
            self.send_json(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length) or b"{}")
        order = {
            "id": f"order-{len(ORDERS) + 1}",
            "user_id": payload.get("user_id"),
            "sku": payload.get("sku"),
            "status": "paid",
        }
        ORDERS.append(order)
        self.send_json(200, {"ok": True, "order": order})

    def log_message(self, _format, *_args):
        return


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("fixture listening on http://127.0.0.1:8765", flush=True)
    server.serve_forever()
