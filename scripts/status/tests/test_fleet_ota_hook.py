"""Unit tests for the post-build fleet OTA interpreter selection."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

STATUS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STATUS))

spec = importlib.util.spec_from_file_location("fleet_ota_hook", STATUS / "fleet_ota_hook.py")
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

PENV = r"C:\Users\tinel\.platformio\penv\Scripts\python.exe"
SYSTEM = r"C:\Python311\python.exe"


def test_candidate_prefixes_prefer_system_over_platformio():
    def which(name):
        return {
            "py": r"C:\Windows\py.exe",
            "python": PENV,
            "python3": None,
        }.get(name)

    prefixes = mod._candidate_prefixes(which, PENV)
    assert prefixes[0] == [r"C:\Windows\py.exe", "-3"]
    assert prefixes[-1] == [PENV]
    assert all("/.platformio/" not in item[0].replace("\\", "/").lower() for item in prefixes[:-1])


def test_candidate_prefixes_dedupes_platformio_python():
    prefixes = mod._candidate_prefixes(lambda name: PENV if name == "python" else None, PENV)
    assert prefixes == [[PENV]]


def test_python_cmd_uses_interpreter_that_already_has_deps(monkeypatch):
    monkeypatch.setattr(mod, "_candidate_prefixes", lambda which, exe: [["py", "-3"], [SYSTEM]])

    def probe(prefix):
        return "ready" if prefix[0] == "py" else "missing"

    monkeypatch.setattr(mod, "_probe", probe)
    monkeypatch.setattr(mod, "_pip_install", lambda prefix: False)
    assert mod._python_cmd() == ["py", "-3"]


def test_python_cmd_installs_into_first_interpreter_missing_deps(monkeypatch):
    monkeypatch.setattr(mod, "_candidate_prefixes", lambda which, exe: [[SYSTEM], [PENV]])
    seen = {"n": 0}

    def probe(prefix):
        seen["n"] += 1
        if prefix[0] == SYSTEM and seen["n"] > 1:
            return "ready"
        return "missing"

    installed = []
    monkeypatch.setattr(mod, "_probe", probe)
    monkeypatch.setattr(mod, "_pip_install", lambda prefix: installed.append(prefix) or True)
    assert mod._python_cmd() == [SYSTEM]
    assert installed == [[SYSTEM]]


def test_python_cmd_falls_through_to_platformio_when_system_pip_fails(monkeypatch):
    monkeypatch.setattr(mod, "_candidate_prefixes", lambda which, exe: [[SYSTEM], [PENV]])

    def probe(prefix):
        return "ready" if prefix[0] == PENV and probe.installed else "missing"

    probe.installed = False

    def pip_install(prefix):
        if prefix[0] == PENV:
            probe.installed = True
            return True
        return False

    monkeypatch.setattr(mod, "_probe", probe)
    monkeypatch.setattr(mod, "_pip_install", pip_install)
    assert mod._python_cmd() == [PENV]


def test_python_cmd_skips_dead_interpreters(monkeypatch):
    monkeypatch.setattr(mod, "_candidate_prefixes", lambda which, exe: [["py", "-3"], [SYSTEM]])

    def probe(prefix):
        return "dead" if prefix[0] == "py" else "ready"

    monkeypatch.setattr(mod, "_probe", probe)
    assert mod._python_cmd() == [SYSTEM]


def test_python_cmd_empty_when_install_cannot_run(monkeypatch):
    monkeypatch.setattr(mod, "_candidate_prefixes", lambda which, exe: [[SYSTEM]])
    monkeypatch.setattr(mod, "_probe", lambda prefix: "missing")
    monkeypatch.setattr(mod, "_pip_install", lambda prefix: False)
    assert mod._python_cmd() == []
