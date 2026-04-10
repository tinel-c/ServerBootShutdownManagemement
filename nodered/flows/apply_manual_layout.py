"""
Apply x,y from a Node-RED export onto 420-irrigation-zones-controls.json
by stable fingerprints (IDs may differ).

  python apply_manual_layout.py
  python apply_manual_layout.py -   # JSON array on stdin
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_FLOW = Path(__file__).with_name("420-irrigation-zones-controls.json")
USER_JSON = Path(__file__).with_name("420-manual-layout.json")
MAIN_TAB = "dd53b5c74524e7c3"
COMMENT_ID = "a87d8c82a860eb8b"


def fingerprint(n: dict) -> tuple:
    t = n.get("type")
    if t == "comment":
        return ("comment", (n.get("name") or "")[:80])
    if t == "mqtt in":
        return ("mqtt in", n.get("topic"))
    if t == "mqtt out":
        return ("mqtt out", n.get("topic"))
    if t == "change":
        return ("change", n.get("name"), json.dumps(n.get("rules", []), sort_keys=True))
    if t == "switch":
        return ("switch", n.get("property"), json.dumps(n.get("rules", []), sort_keys=True))
    if t == "link in":
        return ("link in", n.get("name"), tuple(sorted(n.get("links") or [])))
    if t == "link out":
        return ("link out", n.get("name"), tuple(sorted(n.get("links") or [])))
    if t == "inject":
        return ("inject", n.get("payloadType"), n.get("topic"), n.get("once"))
    if t == "delay":
        return ("delay", n.get("timeout"), n.get("timeoutUnits"), n.get("pauseType"))
    if t == "ui-button":
        return ("ui-button", n.get("label"), n.get("group"))
    if t == "ui-switch":
        return ("ui-switch", n.get("label"), n.get("group"))
    if t == "ui-text":
        return ("ui-text", n.get("label"), n.get("group"))
    if t == "function":
        return ("function", n.get("name"), (n.get("func") or "")[:200])
    if t == "simpletime":
        return ("simpletime", n.get("name"))
    if t == "zone in":
        return ("zone in", n.get("zonename"), n.get("program"))
    if t == "zone-timer":
        return ("zone-timer", n.get("zonename"), n.get("program"))
    if t == "timerctl out":
        return ("timerctl out", n.get("program"))
    if t == "run-gate":
        return ("run-gate", n.get("program"))
    if t == "program":
        return ("program", n.get("name"))
    if t == "mqtt-broker":
        return ("mqtt-broker", n.get("broker"), n.get("port"))
    if t == "global-config":
        return ("global-config", json.dumps(n.get("modules", {}), sort_keys=True))
    if t == "ui_group":
        return ("ui_group", n.get("name"), n.get("tab"))
    if t == "ui_tab":
        return ("ui_tab", n.get("name"))
    return (t, n.get("id"))


def bucket_xy(nodes: list[dict]) -> dict[tuple, list[tuple[int, int]]]:
    out: dict[tuple, list[tuple[int, int]]] = defaultdict(list)
    for n in nodes:
        if "x" not in n or "y" not in n:
            continue
        out[fingerprint(n)].append((int(n["x"]), int(n["y"])))
    for fp in out:
        out[fp].sort(key=lambda xy: (xy[1], xy[0]))
    return out


def load_user() -> list:
    if len(sys.argv) > 1 and sys.argv[1] in ("-", "--stdin"):
        return json.load(sys.stdin)
    if not USER_JSON.is_file():
        raise SystemExit(
            f"Missing {USER_JSON.name}. Save your Node-RED export as this file, "
            f"or pipe JSON: python apply_manual_layout.py - < {USER_JSON.name}"
        )
    return json.loads(USER_JSON.read_text(encoding="utf-8"))


def main() -> None:
    user = load_user()
    repo = json.loads(REPO_FLOW.read_text(encoding="utf-8"))

    user_buckets = bucket_xy(user)

    repo_by_fp: dict[tuple, list[dict]] = defaultdict(list)
    for n in repo:
        z = str(n.get("z", ""))
        if n.get("id") == COMMENT_ID and n.get("type") == "comment":
            repo_by_fp[fingerprint(n)].append(n)
            continue
        if z != MAIN_TAB:
            continue
        if "x" not in n or "y" not in n:
            continue
        repo_by_fp[fingerprint(n)].append(n)

    for nodes in repo_by_fp.values():
        nodes.sort(key=lambda n: (int(n["y"]), int(n["x"])))

    updated = 0
    missing: list[str] = []
    mismatched_len: list[str] = []

    for fp, repo_nodes in repo_by_fp.items():
        u = user_buckets.get(fp)
        if not u:
            if repo_nodes:
                missing.append(f"{fp!r} ({len(repo_nodes)} repo nodes)")
            continue
        if len(u) != len(repo_nodes):
            mismatched_len.append(f"{fp!r} user={len(u)} repo={len(repo_nodes)}")
        for n, (nx, ny) in zip(repo_nodes, u):
            if int(n["x"]) != nx or int(n["y"]) != ny:
                n["x"], n["y"] = nx, ny
                updated += 1
        if len(repo_nodes) > len(u):
            for n in repo_nodes[len(u) :]:
                missing.append(f"extra repo {n.get('type')} {fp!r}")
        elif len(u) > len(repo_nodes):
            pass  # extra user coords ignored

    REPO_FLOW.write_text(json.dumps(repo, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Updated {updated} node positions.")
    if mismatched_len:
        print("Count mismatches (check fingerprints):", len(mismatched_len))
        for m in mismatched_len[:25]:
            print(" ", m)
    if missing:
        print("Issues:", len(missing))
        for m in missing[:25]:
            print(" ", m)


if __name__ == "__main__":
    main()
