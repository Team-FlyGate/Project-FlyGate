"""One cache rule for every upstream call: ToolUniverse SDK tools and the Open Targets GraphQL endpoint.

A request is a canonical JSON key. Its sha1 names the cache file `$OMICS_DIR/<source>/<sha1>.json`, which holds
the key, the retrieval date, and the response. Only successful responses are cached. A cached request is never
sent again. A dry run counts uncached requests as `not_cached` and returns None. A failed call returns None and
appends an error record; nothing is replaced by 0.
"""
import datetime
import hashlib
import json
import os
import pathlib
import time
import urllib.error
import urllib.request

OT_GRAPHQL = "https://api.platform.opentargets.org/api/v4/graphql"
DEFAULT_DIR = "/data/hps/assoc/private/rsc/user/ybae/tmp/omics-cache"
TOOLUNIVERSE = "1.5.7"
GAP = 0.2
ATTEMPTS = 3
TIMEOUT = 60

PREFIX_SOURCE = {"OpenTargets_": "opentargets", "GTEx_": "gtex", "DGIdb_": "dgidb", "ols_": "ols", "HPO_": "hpo",
                 "Mondo_": "mondo"}
HOSTS = {"opentargets": "api.platform.opentargets.org", "gtex": "gtexportal.org", "dgidb": "dgidb.org",
         "ols": "www.ebi.ac.uk", "hpo": "ontology.jax.org", "mondo": "api.monarchinitiative.org"}


def cache_dir() -> pathlib.Path:
    return pathlib.Path(os.environ.get("OMICS_DIR") or DEFAULT_DIR)


def canonical(key: dict) -> str:
    return json.dumps(key, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def cache_path(root: pathlib.Path, source: str, key: dict) -> pathlib.Path:
    return root / source / f"{hashlib.sha1(canonical(key).encode('utf-8')).hexdigest()}.json"


def write_entry(path: pathlib.Path, key: dict, day: str, response) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps({"request": key, "retrieved": day, "response": response}, ensure_ascii=False),
                   encoding="utf-8")
    tmp.replace(path)


def source_of(tool: str) -> str:
    return next(s for p, s in PREFIX_SOURCE.items() if tool.startswith(p))


def _send(url: str, body: bytes | None = None):
    req = urllib.request.Request(url, data=body, method="GET" if body is None else "POST",
                                 headers={"Content-Type": "application/json", "Accept": "application/json",
                                          "User-Agent": "FlyGate-omics-build/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')[:300]}") from exc


_TU = None


def _toolu(name: str, arguments: dict):
    global _TU
    if _TU is None:
        from tooluniverse import ToolUniverse
        _TU = ToolUniverse()
        _TU.load_tools()
    return _TU.run_one_function({"name": name, "arguments": arguments})


class Fetcher:
    def __init__(self, root: pathlib.Path | None = None, dry_run: bool = False, gap: float = GAP):
        self.root, self.dry_run, self.gap = root or cache_dir(), dry_run, gap
        self.stats: dict[str, dict[str, int]] = {}
        self.errors: list[dict] = []
        self.dates: set[str] = set()
        self._last: dict[str, float] = {}
        self._memo: dict[pathlib.Path, object] = {}

    def _count(self, source: str, what: str) -> None:
        s = self.stats.setdefault(source, {"cached": 0, "sent": 0, "not_cached": 0, "failed": 0})
        s[what] += 1

    def _space(self, source: str) -> None:
        host = HOSTS.get(source, source)
        wait = self.gap - (time.monotonic() - self._last.get(host, 0.0))
        if wait > 0:
            time.sleep(wait)
        self._last[host] = time.monotonic()

    def _get(self, source: str, key: dict, call):
        path = cache_path(self.root, source, key)
        if path not in self._memo:
            self._memo[path] = self._load(source, key, path, call)
        return self._memo[path]

    def _load(self, source: str, key: dict, path: pathlib.Path, call):
        if path.exists():
            entry = json.loads(path.read_text(encoding="utf-8"))
            self._count(source, "cached")
            self.dates.add(entry["retrieved"])
            return entry["response"]
        if self.dry_run:
            self._count(source, "not_cached")
            return None
        for attempt in range(ATTEMPTS):
            self._space(source)
            self._count(source, "sent")
            try:
                response, error = call()
                break
            except Exception as exc:  # noqa: BLE001  transport failures are retried, then recorded, never a value
                response, error = None, f"{type(exc).__name__}: {exc}"
                time.sleep(2 * attempt)
        if error is not None:
            self._count(source, "failed")
            self.errors.append({"source": source, "request": key, "error": error[:300]})
            return None
        day = datetime.date.today().isoformat()
        write_entry(path, key, day, response)
        self.dates.add(day)
        return response

    def tool(self, name: str, arguments: dict, absent: str | None = None):
        """Returns the tool's payload, or None when the call failed or was not cached in a dry run.

        `run_one_function` wraps some tools in `{"status", "data"}` and returns others bare, so both are unwrapped
        here and the cache holds the payload only. A tool error whose text contains `absent` is the upstream
        saying the record does not exist; that is an answer, so the error envelope is cached and returned.
        """
        def call():
            r = _toolu(name, arguments)
            if absent and isinstance(r, dict) and r.get("status") == "error" and absent in str(r.get("error")):
                return r, None
            if isinstance(r, dict) and "status" in r and "data" in r:
                ok = r["status"] == "success"
                return (r["data"], None) if ok else (None, "tool_error: " + json.dumps(r, default=str)[:300])
            if r is None or (isinstance(r, dict) and ("error" in r or r.get("status") == "error")):
                return None, "tool_error: " + json.dumps(r, ensure_ascii=False, default=str)[:300]
            return r, None
        return self._get(source_of(name), {"tool": name, "arguments": arguments}, call)

    def get(self, source: str, url: str):
        """A plain JSON GET under the same cache rule, for endpoints no ToolUniverse tool reads correctly."""
        return self._get(source, {"get": url}, lambda: (_send(url), None))

    def graphql(self, operation: str, query: str, variables: dict | None):
        """Returns the GraphQL `data`, or None. A response carrying `errors` counts as a failure."""
        key = {"graphql": operation, "query": query, "variables": variables}

        def call():
            body = json.dumps({"operationName": operation, "query": query, "variables": variables}).encode("utf-8")
            r = _send(OT_GRAPHQL, body)
            if not isinstance(r, dict) or r.get("errors") or r.get("data") is None:
                return None, "graphql_error: " + json.dumps(r, ensure_ascii=False)[:300]
            return r["data"], None
        return self._get("opentargets", key, call)

    def note(self, source: str, request: dict, error: str) -> None:
        """A derived failure. In a dry run a missing value means not cached, so nothing is recorded."""
        if not self.dry_run:
            self.errors.append({"source": source, "request": request, "error": error})
