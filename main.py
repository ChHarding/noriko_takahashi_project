"""Version 1: receive and save writing events from the browser.

JavaScript decides when a sentence or revision is finished.
Python only receives the events and saves them as JSON.
"""

import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
SESSIONS = ROOT / "sessions"
SESSIONS.mkdir(exist_ok=True)

sessions = {}


def now():
    return datetime.now(timezone.utc).isoformat()


def save_session(session):
    file_path = SESSIONS / f'{session["session_id"]}.json'
    file_path.write_text(json.dumps(session, indent=2, ensure_ascii=False), encoding="utf-8")
    return file_path


def add_event(session, event_type, data=None):
    event = {"time_utc": now(), "type": event_type}

    if data is not None:
        event.update(data)

    session["events"].append(event)
    save_session(session)


class Handler(BaseHTTPRequestHandler):
    def send_json(self, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        if not body:
            return {}

        return json.loads(body)

    def do_GET(self):
        if self.path == "/":
            body = (STATIC / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_error(404)

    def do_POST(self):
        data = self.read_json()

        if self.path == "/start":
            session_id = uuid4().hex
            session = {
                "session_id": session_id,
                "started_at": now(),
                "ended_at": None,
                "events": [],
                "sentences": []
            }
            sessions[session_id] = session
            add_event(session, "session_started")
            self.send_json({"session_id": session_id})
            return

        session = sessions.get(data.get("session_id"))

        if session is None:
            self.send_error(404, "Unknown session")
            return

        if self.path == "/edit":
            add_event(session, "edit", {
                "before": data.get("before", ""),
                "after": data.get("after", ""),
                "change_position": data.get("change_position"),
                "cursor": data.get("cursor")
            })
            self.send_json({"ok": True})
            return

        if self.path == "/sentence":
            item = {
                "time_utc": now(),
                "type": data.get("type"),
                "sentence_number": data.get("sentence_number"),
                "sentence": data.get("sentence", ""),
                "current_draft": data.get("current_draft", "")
            }
            session["sentences"].append(item)
            add_event(session, "sentence_sent", item)
            self.send_json({"ok": True})
            return

        if self.path == "/end":
            session["ended_at"] = now()
            session["final_draft"] = data.get("current_draft", "")
            add_event(session, "session_ended")
            file_path = save_session(session)

            self.send_json({
                "sentences_sent": len(session["sentences"]),
                "file": str(file_path)
            })
            return

        self.send_error(404)

    def log_message(self, format, *args):
        pass


def main():
    print("Version 1 real-time input test")
    print("Open http://localhost:8000 in your browser.")

    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")


if __name__ == "__main__":
    main()
