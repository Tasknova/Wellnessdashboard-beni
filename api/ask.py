"""
Vercel Serverless Function — Pusher trigger for WF chatbot questions.
POST /api/ask with {session_id, question, mode}
Triggers 'question' event on 'wf-queries' Pusher channel.
"""
import json
import os
from http.server import BaseHTTPRequestHandler
import pusher


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(content_length).decode('utf-8')

        try:
            body = json.loads(raw)
        except Exception:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Invalid JSON'}).encode())
            return

        session_id = body.get('session_id', '')
        question = body.get('question', '').strip()
        mode = body.get('mode', 'INSIGHTS')

        if not question:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Missing question'}).encode())
            return

        pusher_client = pusher.Pusher(
            app_id=os.environ['PUSHER_APP_ID'],
            key=os.environ['PUSHER_KEY'],
            secret=os.environ['PUSHER_SECRET'],
            cluster=os.environ.get('PUSHER_CLUSTER', 'ap2'),
            ssl=True,
        )

        pusher_client.trigger('wf-queries', 'question', {
            'session_id': session_id,
            'question': question,
            'mode': mode,
        })

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'sent', 'session_id': session_id}).encode())
