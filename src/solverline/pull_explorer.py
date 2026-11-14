"""Resumable Explorer pull over predeclared windows (sampling.json).

Usage: python -m solverline.pull_explorer [--config sampling.json]
- >=5 s between request starts (API limit 1 req/5 s); honors Retry-After on 429.
- Window [start,end) is half-open: start is exclusive in the API, so we ask 1 ms earlier and filter locally.
- Complete windows are cached atomically in data/raw/explorer/<start>.json and skipped on resume.
- Dedup by (depositAddress, depositMemo); conflicting duplicates raise. Token never logged/cached.
"""
import argparse, datetime as dt, hashlib, json, os, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "raw" / "explorer"
_last = [0.0]


def _env():
    env = {}
    for line in (ROOT / ".env").read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def _iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%S.") + f"{t.microsecond // 1000:03d}Z"


def _get(base, jwt, params, tries=5):
    url = base + "/transactions?" + urllib.parse.urlencode(params)
    for attempt in range(tries):
        wait = 5.2 - (time.monotonic() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.monotonic()
        req = urllib.request.Request(url, headers={"Authorization": "Bearer " + jwt, "User-Agent": "solverline"})
        try:
            with urllib.request.urlopen(req, timeout=60) as f:
                return json.load(f)
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                sys.exit(f"Explorer rejected authentication (HTTP {e.code}).")
            if e.code == 429:
                time.sleep(float(e.headers.get("Retry-After", 10)))
            elif attempt == tries - 1:
                raise
            else:
                time.sleep(2 ** attempt)
        except (urllib.error.URLError, TimeoutError):
            if attempt == tries - 1:
                raise
            time.sleep(2 ** attempt)


def key(tx):
    return (tx["depositAddress"], tx.get("depositMemo") or None)


def pull_window(base, jwt, start, end, statuses, size):
    rows, seen_cursors, cursor = {}, set(), None
    while True:
        p = {"numberOfTransactions": size, "statuses": statuses,
             "startTimestamp": _iso(start - dt.timedelta(milliseconds=1)), "endTimestamp": _iso(end)}
        if cursor:
            p["lastDepositAddress"], p["lastDepositMemo"] = cursor[0], cursor[1] or ""
            p = {k: v for k, v in p.items() if not (k == "lastDepositMemo" and v == "")}
        page = _get(base, jwt, p)
        if not isinstance(page, list):
            raise RuntimeError("unexpected response shape")
        for tx in page:
            k = key(tx)
            if k in rows and rows[k] != tx:
                raise RuntimeError(f"conflicting duplicate {k}")
            rows[k] = tx
        if len(page) < size:
            return list(rows.values()), True
        cursor = key(page[-1])
        if cursor in seen_cursors:
            return list(rows.values()), False  # non-advancing: mark incomplete
        seen_cursors.add(cursor)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(ROOT / "sampling.json"))
    a = ap.parse_args()
    cfg_text = Path(a.config).read_text()
    cfg = json.loads(cfg_text)
    env = _env()
    base = env.get("EXPLORER_BASE_URL", "https://explorer.near-intents.org/api/v0")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "_config.sha256").write_text(hashlib.sha256(cfg_text.encode()).hexdigest())
    for d in cfg["dates"]:
        for slot in cfg["slots_utc"]:
            start = dt.datetime.fromisoformat(f"{d}T{slot}:00+00:00")
            end = start + dt.timedelta(minutes=cfg["window_minutes"])
            f = OUT / f"{start:%Y%m%dT%H%M}.json"
            if f.exists() and json.loads(f.read_text()).get("complete"):
                print("cached", f.name)
                continue
            rows, complete = pull_window(base, env["EXPLORER_JWT"], start, end, cfg["statuses"], cfg["page_size"])
            rows = [r for r in rows if start <= dt.datetime.fromisoformat(r["createdAt"].replace("Z", "+00:00")) < end]
            body = {"start": _iso(start), "end": _iso(end), "complete": complete,
                    "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(), "count": len(rows), "swaps": rows}
            tmp = f.with_suffix(".tmp")
            tmp.write_text(json.dumps(body))
            os.replace(tmp, f)
            print(f"{f.name}: {len(rows)} swaps complete={complete}", flush=True)


if __name__ == "__main__":
    main()
