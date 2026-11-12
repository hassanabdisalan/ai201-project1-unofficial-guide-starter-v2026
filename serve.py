#!/usr/bin/env python3
"""
The Unofficial Guide — the same pipeline, over HTTP.

    python serve.py                          run it locally on port 5000
    gunicorn serve:app                       run it the way a host runs it

Nothing new happens in this file. It is a wrapper: a request comes in, it
hands the question to `app.py::ask_pipeline` — the exact function the command
line uses — and hands the answer back as JSON. Retrieval, the relevance gate
and the grounded prompt all still live where they lived. If you change how
your system answers, you change it in those files and this one follows.

Two routes:

    POST /ask       {"question": "..."} in, the answer and its sources out
    GET  /health    is the service up, and is there an index to search

Why this exists: `app.py` runs once and exits, which is fine on your laptop
and impossible to deploy. A hosted service has to stay up and wait for
requests. This is the smallest thing that does that.

Capstone instrumentation: every POST /ask appends one JSON line to
`logs/requests.jsonl` (override the path with AI201_LOG_PATH). Fields:
ts, request_id, question, answer, refused, best_distance, n_sources, status,
latency_ms, model_calls, prompt_tokens, output_tokens, error. Token and call
counts are per-request deltas of generate.py's session counters, so run one
worker process (gunicorn -w 1) or they will be wrong.
"""

import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request

import config

app = Flask(__name__)

LOG_PATH = Path(os.getenv("AI201_LOG_PATH", config.ROOT / "logs" / "requests.jsonl"))
_log_lock = threading.Lock()


def log_request(**fields) -> None:
    """Append one structured record. Logging never breaks a request."""
    record = {"ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds")}
    record.update(fields)
    try:
        with _log_lock:
            LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with LOG_PATH.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + chr(10))
    except Exception:  # noqa: BLE001
        pass


@app.get("/health")
def health():
    """Is the service up, and is there an index to search?

    Two different questions, and the second one is the one that bites. A
    freshly deployed service answers this route happily while every /ask
    returns "no index" — hosts give you no disk that survives a restart, so
    the index has to be built as part of getting the service up. Checking
    here means you find that out in one request instead of five.
    """
    from store import index_exists

    ready = index_exists(config.CORPUS)
    return jsonify(
        {
            "status": "ok",
            "corpus": config.CORPUS,
            "index_ready": ready,
            "detail": (
                "ready"
                if ready
                else "no index for this corpus — run `python app.py index`"
            ),
        }
    )


@app.post("/ask")
def ask():
    """One question in, one grounded answer out.

    A refused question is a 200, not an error. The gate refusing is your
    system working — it is an answer, and the JSON says so with
    `"refused": true` so whatever calls this can tell the two apart.
    """
    from app import ask_pipeline

    import generate

    request_id = uuid.uuid4().hex[:8]
    payload = request.get_json(silent=True) or {}
    question = (payload.get("question") or "").strip()

    if not question:
        log_request(request_id=request_id, question="", answer=None, status=400,
                    latency_ms=0, error="empty question")
        return (
            jsonify(
                {
                    "error": "Send JSON with a question in it, like "
                    '{"question": "is the housing lottery random?"}'
                }
            ),
            400,
        )

    calls0, tok0 = generate.call_count(), generate.token_counts()
    t0 = time.perf_counter()

    def usage_since():
        tok = generate.token_counts()
        return {
            "model_calls": generate.call_count() - calls0,
            "prompt_tokens": tok["prompt"] - tok0["prompt"],
            "output_tokens": tok["output"] - tok0["output"],
        }

    try:
        outcome = ask_pipeline(question, corpus=config.CORPUS)
    except Exception as exc:  # noqa: BLE001 — a reader gets this, not a traceback
        err = f"{type(exc).__name__}: {exc}"
        log_request(request_id=request_id, question=question, answer=None,
                    status=500, latency_ms=round((time.perf_counter() - t0) * 1000),
                    error=err, **usage_since())
        return jsonify({"error": err}), 500

    log_request(
        request_id=request_id,
        question=question,
        answer=outcome["answer"],
        refused=outcome["refused"],
        best_distance=round(outcome["best_distance"], 4),
        n_sources=len(outcome["sources"]),
        status=200,
        latency_ms=round((time.perf_counter() - t0) * 1000),
        error=None,
        **usage_since(),
    )

    return jsonify(
        {
            "question": question,
            "answer": outcome["answer"],
            "refused": outcome["refused"],
            "sources": outcome["sources"],
            "best_distance": round(outcome["best_distance"], 4),
            "threshold": outcome["threshold"],
            "corpus": config.CORPUS,
        }
    )


def main():
    # Hosts tell you which port to listen on through PORT, and they expect you
    # on 0.0.0.0. Binding 127.0.0.1 instead works perfectly on your laptop and
    # then answers nothing at all once deployed, because the host's router
    # can't reach a socket that only accepts connections from inside the
    # container. It is the single most common way a first deploy "succeeds"
    # and is unreachable.
    port = int(os.getenv("PORT", "5000"))

    # Debug mode reloads on save, which is handy, and prints a console that
    # runs arbitrary code, which is not something to leave switched on where
    # strangers can reach it. Off unless you ask for it.
    debug = os.getenv("AI201_DEBUG", "0") == "1"

    print(f"Serving The Unofficial Guide on http://localhost:{port}")
    print(f"Corpus: {config.CORPUS}    (Ctrl-C to stop)\n")
    print("Try it from another terminal:\n")
    print(f"  curl http://localhost:{port}/health")
    print(
        f"  curl -X POST http://localhost:{port}/ask \\\n"
        f"    -H 'Content-Type: application/json' \\\n"
        f"    -d '{{\"question\": \"is the housing lottery random?\"}}'\n"
    )

    app.run(host="0.0.0.0", port=port, debug=debug)


if __name__ == "__main__":
    main()
