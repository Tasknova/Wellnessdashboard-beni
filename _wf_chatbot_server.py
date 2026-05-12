"""
Tasknova — WF Chatbot HTTP Bridge
===================================
Local HTTP server that bridges the dashboard chatbot UI
to the chatbot agent via file polling.

Run: python _wf_chatbot_server.py
Serves: http://localhost:8765
"""

import http.server
import json
from pathlib import Path

ROOT = Path(__file__).parent
DASHBOARD = ROOT / 'wf-revenue-intelligence-dashboard.html'
QUERY_FILE = ROOT / 'chatbot_query.txt'
RESPONSE_FILE = ROOT / 'chatbot_response.txt'
PORT = 8765


class ChatbotHandler(http.server.BaseHTTPRequestHandler):

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self._serve_dashboard()
        elif self.path == '/response':
            self._serve_response()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/query':
            self._handle_query()
        elif self.path == '/clear':
            self._handle_clear()
        else:
            self.send_response(404)
            self.end_headers()

    def _serve_dashboard(self):
        if not DASHBOARD.exists():
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'Dashboard not found. Run _build_wf_dashboard.py first.')
            return
        data = DASHBOARD.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(data))
        self.end_headers()
        self.wfile.write(data)

    def _handle_query(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8').strip()
        # Clear previous response
        if RESPONSE_FILE.exists():
            RESPONSE_FILE.unlink()
        # Write query for agent to pick up
        QUERY_FILE.write_text(body, encoding='utf-8')

        self.send_response(200)
        self._cors()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'queued'}).encode())

    def _handle_clear(self):
        """Reset conversation — write a clear signal for the agent."""
        QUERY_FILE.write_text('[CLEAR]', encoding='utf-8')
        if RESPONSE_FILE.exists():
            RESPONSE_FILE.unlink()
        self.send_response(200)
        self._cors()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'cleared'}).encode())

    def _serve_response(self):
        self.send_response(200)
        self._cors()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        if RESPONSE_FILE.exists():
            answer = RESPONSE_FILE.read_text(encoding='utf-8').strip()
            if answer:
                self.wfile.write(json.dumps({
                    'status': 'ready',
                    'response': answer
                }).encode())
                return

        self.wfile.write(json.dumps({'status': 'waiting'}).encode())

    def log_message(self, format, *args):
        print(f"[server] {args[0]}")


if __name__ == '__main__':
    server = http.server.HTTPServer(('localhost', PORT), ChatbotHandler)
    print(f"Tasknova Chatbot Server running at http://localhost:{PORT}")
    print(f"Dashboard: {DASHBOARD}")
    print(f"Query file: {QUERY_FILE}")
    print(f"Response file: {RESPONSE_FILE}")
    print("Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()
