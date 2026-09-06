#!/usr/bin/env python3
"""Tiny CORS+PNA file server so the Gmail tab can fetch local files."""
import http.server, functools

class H(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        super().end_headers()
    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

http.server.HTTPServer(("127.0.0.1", 8811), H).serve_forever()
