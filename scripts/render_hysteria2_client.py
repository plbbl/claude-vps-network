#!/usr/bin/env python3
"""Generate a protected Hysteria 2 share URI and Mihomo YAML fragment."""

from __future__ import annotations

import argparse
import getpass
import os
from pathlib import Path
from urllib.parse import quote, urlencode


def secret_from_env_or_prompt(name: str, prompt: str, required: bool = True) -> str:
    value = os.environ.get(name, "")
    if not value:
        value = getpass.getpass(prompt)
    if required and not value:
        raise SystemExit(f"{name} is required")
    return value


def yaml_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", required=True, help="Server hostname or IP")
    parser.add_argument("--port", type=int, default=443)
    parser.add_argument("--sni", required=True, help="TLS server name")
    parser.add_argument("--name", default="Private Hysteria 2")
    parser.add_argument("--obfs", choices=("none", "salamander"), default="salamander")
    parser.add_argument("--insecure", action="store_true", help="Disable normal TLS certificate verification")
    parser.add_argument("--output", type=Path, required=True, help="Protected output file")
    parser.add_argument("--force", action="store_true", help="Explicitly overwrite an existing output file")
    args = parser.parse_args()

    if not (1 <= args.port <= 65535):
        parser.error("--port must be between 1 and 65535")
    if any(char.isspace() for char in args.server) or any(char.isspace() for char in args.sni):
        parser.error("--server and --sni cannot contain whitespace")
    if "://" in args.server:
        parser.error("--server must be a hostname or IP, not a URL")
    if args.output.exists() and not args.force:
        parser.error("--output already exists; choose a new path or pass --force")

    auth = secret_from_env_or_prompt("HY2_AUTH", "Hysteria authentication secret: ")
    obfs_password = ""
    if args.obfs == "salamander":
        obfs_password = secret_from_env_or_prompt("HY2_OBFS_PASSWORD", "Salamander password: ")

    query: list[tuple[str, str]] = [("sni", args.sni), ("insecure", "1" if args.insecure else "0")]
    if args.obfs == "salamander":
        query.extend((("obfs", "salamander"), ("obfs-password", obfs_password)))
    uri_host = args.server if ":" not in args.server or args.server.startswith("[") else f"[{args.server}]"
    uri = (
        f"hysteria2://{quote(auth, safe='')}@{uri_host}:{args.port}/?"
        f"{urlencode(query)}#{quote(args.name, safe='')}"
    )

    lines = [
        "# Hysteria 2 single-node share URI",
        uri,
        "",
        "# Mihomo/Clash YAML fragment",
        "proxies:",
        f"  - name: {yaml_quote(args.name)}",
        "    type: hysteria2",
        f"    server: {yaml_quote(args.server)}",
        f"    port: {args.port}",
        f"    password: {yaml_quote(auth)}",
        f"    sni: {yaml_quote(args.sni)}",
        f"    skip-cert-verify: {'true' if args.insecure else 'false'}",
    ]
    if args.obfs == "salamander":
        lines.extend(("    obfs: salamander", f"    obfs-password: {yaml_quote(obfs_password)}"))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | (os.O_TRUNC if args.force else os.O_EXCL)
    fd = os.open(args.output, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    os.chmod(args.output, 0o600)
    print(f"Wrote protected client bundle: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
