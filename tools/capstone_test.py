"""Capstone acceptance test: runs the five criteria in criteria.md once (one trial).

    python tools/capstone_test.py <trial_number>

Starts its own servers (good key on one port, deliberately invalid key on
another), writes everything to results/capstone/trial<N>.jsonl and a summary to
results/capstone/trial<N>.json, then stops the servers it started.
"""
import json, os, subprocess, sys, threading, time, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import questions as Q

TRIAL = int(sys.argv[1])
OUT = ROOT / "results" / "capstone"
OUT.mkdir(parents=True, exist_ok=True)
LOG = OUT / f"trial{TRIAL}.jsonl"
if LOG.exists():
    LOG.unlink()
GOOD, BAD = 5071, 5072
IN = [q["question"] for q in Q.QUESTIONS]
OOS = list(Q.OUT_OF_SCOPE)
REQUIRED = ["ts", "request_id", "question", "answer", "status", "latency_ms", "error"]


def start(port, key=None):
    env = dict(os.environ, AI201_CACHE="0", PORT=str(port), AI201_LOG_PATH=str(LOG))
    if key:
        env["GEMINI_API_KEY"] = key
    p = subprocess.Popen([sys.executable, str(ROOT / "serve.py")], cwd=ROOT, env=env,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        try:
            urllib.request.urlopen(f"http://localhost:{port}/health", timeout=2).read()
            return p
        except Exception:
            time.sleep(1)
    raise RuntimeError("server did not start")


def ask(port, body, timeout=120):
    data = json.dumps(body).encode()
    req = urllib.request.Request(f"http://localhost:{port}/ask", data, {"Content-Type": "application/json"})
    t0 = time.perf_counter()
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        status, text = r.status, r.read()
    except urllib.error.HTTPError as e:
        status, text = e.code, e.read()
    except Exception as e:  # timeout / connection
        return {"status": None, "body": None, "ms": (time.perf_counter() - t0) * 1000, "exc": repr(e)}
    ms = (time.perf_counter() - t0) * 1000
    try:
        body = json.loads(text)
    except Exception:
        body = None
    return {"status": status, "body": body, "ms": ms, "raw": text[:200]}


def lines():
    if not LOG.exists():
        return []
    out = []
    for l in LOG.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(l))
        except Exception:
            out.append({"_invalid": l})
    return out


res = {"trial": TRIAL}
good = start(GOOD)
bad = start(BAD, key="invalid-key-for-test")
try:
    ask(GOOD, {"question": IN[0]})  # warm-up, discarded
    base = len(lines())

    # ── Criterion 3: 10 timed sequential answered requests
    timed = [ask(GOOD, {"question": q}) for q in IN + IN]
    new = lines()[base:]
    ok = 0
    detail3 = []
    for r, ln in zip(timed, new):
        fast = r["status"] == 200 and r["ms"] < 10000
        consistent = ln.get("latency_ms") is not None and ln["latency_ms"] >= r["ms"] - 250
        detail3.append({"client_ms": round(r["ms"]), "logged_ms": ln.get("latency_ms"), "status": r["status"]})
        ok += bool(fast and consistent)
    res["c3"] = {"pass": ok, "of": 10, "detail": detail3}

    # ── Criterion 1: 20 requests, mixed; count lines appended
    base = len(lines())
    for q in IN + IN:
        ask(GOOD, {"question": q})
    for q in OOS:
        ask(GOOD, {"question": q})
    for _ in range(3):
        ask(GOOD, {"question": "  "})
    for q in IN[:2]:
        ask(BAD, {"question": q})
    new = lines()[base:]
    good_lines = [l for l in new if "_invalid" not in l and all(k in l for k in REQUIRED)]
    res["c1"] = {"lines_added": len(new), "complete_lines": len(good_lines), "of": 20,
                 "pass": len(good_lines) if len(new) == 20 else 0}

    # ── Criterion 4: 20 requests, 3 concurrent clients
    base = len(lines())
    work = (IN * 3) + OOS
    idx = {"i": 0}
    lock = threading.Lock()

    def worker():
        while True:
            with lock:
                if idx["i"] >= len(work):
                    return
                q = work[idx["i"]]
                idx["i"] += 1
            ask(GOOD, {"question": q})

    ts = [threading.Thread(target=worker) for _ in range(3)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    new = lines()[base:]
    right, bad4 = 0, []
    for l in new:
        if l.get("refused"):
            c = l.get("model_calls") == 0 and l.get("prompt_tokens") == 0 and l.get("output_tokens") == 0
        elif l.get("status") == 200:
            c = l.get("model_calls") == 1 and (l.get("prompt_tokens") or 0) > 0 and (l.get("output_tokens") or 0) > 0
        else:
            c = False
        right += c
        if not c:
            bad4.append({k: l.get(k) for k in ("question", "status", "refused", "model_calls", "prompt_tokens", "output_tokens")})
    res["c4"] = {"lines_added": len(new), "correct": right, "of": 20,
                 "pass": right if len(new) == 20 else min(right, len(new)), "wrong": bad4}

    # ── Criterion 5: out-of-scope set refused, 0 model calls
    base = len(lines())
    r5 = [ask(GOOD, {"question": q}) for q in OOS]
    new = lines()[base:]
    ok5 = sum(1 for r, l in zip(r5, new)
              if r["body"] and r["body"].get("refused") is True and l.get("model_calls") == 0)
    res["c5"] = {"pass": ok5, "of": 5}

    # ── Criterion 2: invalid key, 5 in-corpus questions
    base = len(lines())
    r2 = [ask(BAD, {"question": q}) for q in IN]
    new = lines()[base:]
    ok2, d2 = 0, []
    for r, l in zip(r2, new):
        good2 = (r["status"] == 500 and r["body"] and r["body"].get("error") and r["ms"] < 30000
                 and l.get("status") == 500 and l.get("error"))
        ok2 += bool(good2)
        d2.append({"status": r["status"], "ms": round(r["ms"]), "exc": r.get("exc"), "logged_status": l.get("status")})
    res["c2"] = {"pass": ok2, "of": 5, "detail": d2, "lines_added": len(new)}
finally:
    for p in (good, bad):
        p.terminate()

(OUT / f"trial{TRIAL}.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
print(json.dumps({k: (v if not isinstance(v, dict) else {a: b for a, b in v.items() if a not in ("detail", "wrong")}) for k, v in res.items()}))
