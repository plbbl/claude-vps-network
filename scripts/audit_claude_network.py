#!/usr/bin/env python3
"""Read-only, redacted audit of Claude Code-related network configuration."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


SENSITIVE_NAME = re.compile(r"(proxy|base_url|anthropic|claude)", re.I)
ASSIGNMENT = re.compile(
    r"(?P<prefix>\b(?:export\s+)?[A-Za-z_][A-Za-z0-9_]*(?:proxy|base_url|anthropic)[A-Za-z0-9_]*\s*[=:]\s*)(?P<value>[^\s#]+)",
    re.I,
)


def run(argv: list[str]) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            argv,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=8,
            check=False,
        )
        return {
            "available": True,
            "exit_code": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
        }
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {"available": False, "error": type(exc).__name__}


def redact_value(value: str) -> str:
    value = value.strip().strip("'\"")
    try:
        parsed = urlsplit(value)
        if parsed.scheme and parsed.hostname:
            port = f":{parsed.port}" if parsed.port else ""
            return f"{parsed.scheme}://{parsed.hostname}{port}/…"
    except ValueError:
        pass
    return "<set:redacted>"


def redact_line(line: str) -> str:
    return ASSIGNMENT.sub(lambda m: m.group("prefix") + redact_value(m.group("value")), line.rstrip())


def redact_scutil(output: str) -> str:
    redacted: list[str] = []
    for line in output.splitlines():
        key, separator, value = line.partition(":")
        normalized = key.strip().lower()
        if not separator:
            redacted.append(line)
        elif "url" in normalized:
            redacted.append(f"{key}: {redact_value(value)}")
        elif "password" in normalized or "username" in normalized:
            redacted.append(f"{key}: <set:redacted>")
        else:
            redacted.append(line)
    return "\n".join(redacted)


def candidate_files(cwd: Path) -> list[Path]:
    home = Path.home()
    return [
        home / ".zshrc",
        home / ".zprofile",
        home / ".zshenv",
        home / ".bashrc",
        home / ".bash_profile",
        home / ".profile",
        home / ".npmrc",
        home / ".claude" / "settings.json",
        home / ".claude" / "settings.local.json",
        home / ".claude.json",
        cwd / ".claude" / "settings.json",
        cwd / ".claude" / "settings.local.json",
    ]


def scan_file(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    findings: list[dict[str, Any]] = []
    try:
        for number, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
            if SENSITIVE_NAME.search(line):
                indicators = sorted({match.group(0).lower() for match in SENSITIVE_NAME.finditer(line)})
                findings.append({"line": number, "indicators": indicators, "text": "<redacted sensitive setting>"})
    except OSError as exc:
        return {"path": str(path), "error": str(exc)}
    return {"path": str(path), "findings": findings}


def timezone_info() -> dict[str, str]:
    info = {"tz_env": os.environ.get("TZ", "<unset>"), "runtime": ",".join(map(str, __import__("time").tzname))}
    localtime = Path("/etc/localtime")
    try:
        if localtime.is_symlink():
            info["localtime"] = os.readlink(localtime)
    except OSError:
        pass
    return info


def online_ip() -> dict[str, Any]:
    request = urllib.request.Request(
        "https://ipinfo.io/json",
        headers={"User-Agent": "claude-vps-network-audit/1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            data = json.load(response)
        return {key: data.get(key) for key in ("ip", "country", "region", "city", "org", "timezone")}
    except Exception as exc:  # Network and JSON failures are report data, not fatal.
        return {"error": type(exc).__name__}


def package_proxy(tool: str) -> dict[str, Any]:
    if not shutil.which(tool):
        return {"available": False}
    return {
        "proxy": run([tool, "config", "get", "proxy"]),
        "https_proxy": run([tool, "config", "get", "https-proxy"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--online", action="store_true", help="Contact ipinfo.io for public egress metadata")
    parser.add_argument("--output", type=Path, help="Write JSON to this file instead of stdout")
    args = parser.parse_args()

    cwd = Path.cwd()
    environment = {
        key: redact_value(value)
        for key, value in sorted(os.environ.items())
        if SENSITIVE_NAME.search(key)
    }
    files = [result for path in candidate_files(cwd) if (result := scan_file(path)) is not None]

    report: dict[str, Any] = {
        "read_only": True,
        "system": {"os": platform.platform(), "machine": platform.machine(), "timezone": timezone_info()},
        "claude": run(["claude", "--version"]) if shutil.which("claude") else {"available": False},
        "node_timezone": run(["node", "-e", "console.log(Intl.DateTimeFormat().resolvedOptions().timeZone)"])
        if shutil.which("node")
        else {"available": False},
        "environment": environment,
        "files": files,
        "git_global_proxy": run(["git", "config", "--global", "--get-regexp", r"^(http|https)\.proxy$"])
        if shutil.which("git")
        else {"available": False},
        "npm_proxy": package_proxy("npm"),
        "yarn_proxy": package_proxy("yarn"),
        "pnpm_proxy": package_proxy("pnpm"),
        "homebrew_proxy": run(["brew", "config"]) if shutil.which("brew") else {"available": False},
    }

    if platform.system() == "Darwin":
        report["macos_system_proxy"] = run(["scutil", "--proxy"])
    if args.online:
        report["public_egress"] = online_ip()

    # Redact command outputs that may include credentials.
    for section in ("git_global_proxy",):
        item = report.get(section)
        if isinstance(item, dict) and isinstance(item.get("stdout"), str):
            redacted_lines = []
            for line in item["stdout"].splitlines():
                key, _, value = line.partition(" ")
                redacted_lines.append(f"{key} {redact_value(value)}" if value else f"{key} <set:redacted>")
            item["stdout"] = "\n".join(redacted_lines)
    for section in ("npm_proxy", "yarn_proxy", "pnpm_proxy"):
        package = report.get(section)
        if isinstance(package, dict):
            for item in package.values():
                if isinstance(item, dict) and isinstance(item.get("stdout"), str) and item["stdout"] not in {"null", "undefined", ""}:
                    item["stdout"] = redact_value(item["stdout"])
    homebrew = report.get("homebrew_proxy")
    if isinstance(homebrew, dict) and isinstance(homebrew.get("stdout"), str):
        homebrew["stdout"] = "\n".join(
            redact_line(line) for line in homebrew["stdout"].splitlines() if "proxy" in line.lower()
        )
    macos_proxy = report.get("macos_system_proxy")
    if isinstance(macos_proxy, dict) and isinstance(macos_proxy.get("stdout"), str):
        macos_proxy["stdout"] = redact_scutil(macos_proxy["stdout"])

    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload)
        os.chmod(args.output, 0o600)
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
