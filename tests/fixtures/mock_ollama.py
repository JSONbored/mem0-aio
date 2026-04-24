from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

EMBEDDING_DIMENSIONS = 768


class Handler(BaseHTTPRequestHandler):
    def _write_json(self, payload: dict[str, object], status: int = 200) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        if self.path == "/api/tags":
            self._write_json(
                {
                    "models": [
                        {"name": "tinyllama:latest", "model": "tinyllama:latest"},
                        {
                            "name": "nomic-embed-text:latest",
                            "model": "nomic-embed-text:latest",
                        },
                    ]
                }
            )
            return

        self._write_json({"status": "ok"})

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw_body = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw_body.decode() or "{}")
        except json.JSONDecodeError:
            body = {}

        if self.path == "/api/embed":
            inputs = body.get("input", "")
            count = len(inputs) if isinstance(inputs, list) else 1
            self._write_json(
                {
                    "model": body.get("model", "nomic-embed-text:latest"),
                    "embeddings": [
                        [0.01 for _ in range(EMBEDDING_DIMENSIONS)]
                        for _ in range(count)
                    ],
                }
            )
            return

        if self.path in {"/api/embeddings", "/v1/embeddings"}:
            self._write_json(
                {
                    "embedding": [0.01 for _ in range(EMBEDDING_DIMENSIONS)],
                    "data": [
                        {
                            "embedding": [0.01 for _ in range(EMBEDDING_DIMENSIONS)],
                            "index": 0,
                            "object": "embedding",
                        }
                    ],
                    "object": "list",
                }
            )
            return

        if self.path in {"/api/chat", "/v1/chat/completions"}:
            self._write_json(
                {
                    "message": {"role": "assistant", "content": "ok"},
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": "ok"},
                            "finish_reason": "stop",
                        }
                    ],
                    "done": True,
                }
            )
            return

        self._write_json({"status": "ok"})

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> None:
    ThreadingHTTPServer(
        ("0.0.0.0", 11434), Handler  # nosec B104 - test container listener only
    ).serve_forever()


if __name__ == "__main__":
    main()
