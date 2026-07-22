#!/usr/bin/env python3
"""Inventory Claude CLI, Desktop, and browser residue without reading secrets."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
from pathlib import Path
from typing import Any


DOMAINS = ("claude.ai", "claude.com", "anthropic.com")


def display(path: Path) -> str:
    home = Path.home()
    try:
        return "~/" + str(path.relative_to(home))
    except ValueError:
        return str(path)


def add(records: list[dict[str, Any]], scope: str, kind: str, path: Path, impact: str) -> None:
    if not path.exists():
        return
    item: dict[str, Any] = {
        "scope": scope,
        "kind": kind,
        "path": display(path),
        "impact_if_removed": impact,
    }
    if path.is_file():
        try:
            item["bytes"] = path.stat().st_size
        except OSError:
            pass
    records.append(item)


def cookie_count(path: Path, table: str, host_column: str) -> int | None:
    if not path.is_file():
        return None
    condition = " OR ".join(f"lower({host_column}) LIKE ?" for _ in DOMAINS)
    params = tuple(f"%{domain}%" for domain in DOMAINS)
    try:
        uri = f"file:{path}?mode=ro"
        with sqlite3.connect(uri, uri=True, timeout=1) as connection:
            row = connection.execute(
                f"SELECT COUNT(*) FROM {table} WHERE {condition}", params
            ).fetchone()
        return int(row[0]) if row else 0
    except (OSError, sqlite3.Error):
        return None


def audit_cli(records: list[dict[str, Any]]) -> None:
    home = Path.home()
    root = Path(os.environ.get("CLAUDE_CONFIG_DIR", home / ".claude")).expanduser()
    categories = {
        "settings.json": ("config", "会丢失用户设置"),
        "settings.local.json": ("config", "会丢失本机设置"),
        "plugins": ("plugins", "会移除已安装插件"),
        "projects": ("sessions", "会丢失会话恢复、项目记忆和工具结果"),
        "history.jsonl": ("history", "会丢失提示词历史"),
        "file-history": ("checkpoints", "会丢失文件回退快照"),
        "stats-cache.json": ("cache", "会清空历史用量统计"),
        "plans": ("cache", "会删除本地计划文件"),
        "debug": ("cache", "会删除调试日志"),
        "paste-cache": ("cache", "会删除粘贴缓存"),
        "image-cache": ("cache", "会删除图片缓存"),
        "session-env": ("cache", "会删除会话环境元数据"),
        "tasks": ("cache", "会删除会话任务列表"),
        "todos": ("cache", "会删除旧版任务列表"),
        "shell-snapshots": ("cache", "会删除 Shell 环境快照"),
        "backups": ("backups", "会删除 Claude 自己创建的迁移备份"),
    }
    for name, (kind, impact) in categories.items():
        add(records, "claude_code", kind, root / name, impact)
    add(records, "claude_code", "account_state", home / ".claude.json", "会删除账号和项目状态")


def audit_desktop(records: list[dict[str, Any]]) -> None:
    library = Path.home() / "Library"
    bundle = "com.anthropic.claudefordesktop"
    candidates = (
        ("data", library / "Application Support" / "Claude", "会删除 Desktop 本地数据和登录状态"),
        ("data", library / "Application Support" / bundle, "会删除 Desktop 本地数据和登录状态"),
        ("cache", library / "Caches" / bundle, "会删除可重建缓存"),
        ("updater", library / "Caches" / f"{bundle}.ShipIt", "会删除更新器缓存"),
        ("preferences", library / "Preferences" / f"{bundle}.plist", "会重置 Desktop 偏好"),
        ("cookies", library / "Cookies" / f"{bundle}.binarycookies", "会退出 Desktop 登录"),
        ("http_storage", library / "HTTPStorages" / bundle, "会删除 HTTP 存储和会话状态"),
        ("webkit", library / "WebKit" / bundle, "会删除 WebKit 站点数据"),
        ("saved_state", library / "Saved Application State" / f"{bundle}.savedState", "会删除窗口恢复状态"),
        ("logs", library / "Logs" / "Claude", "会删除 Desktop 日志"),
        ("container", library / "Containers" / bundle, "会删除沙盒内全部 Desktop 数据"),
        ("group_container", library / "Group Containers" / bundle, "会删除共享容器数据"),
    )
    for kind, path, impact in candidates:
        add(records, "claude_desktop", kind, path, impact)

    for parent in (library / "Application Support", library / "Caches"):
        if not parent.is_dir():
            continue
        for pattern in ("*Claude*", "*claude*", "*Anthropic*", "*anthropic*"):
            for path in parent.glob(pattern):
                if not any(item["path"] == display(path) for item in records):
                    add(records, "claude_desktop", "discovered", path, "人工确认后再决定是否删除")


def chromium_profiles(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    profiles = []
    for path in root.iterdir():
        if path.is_dir() and (
            path.name == "Default"
            or path.name.startswith("Profile ")
            or path.name in {"Guest Profile", "System Profile"}
        ):
            profiles.append(path)
    return sorted(profiles)


def audit_chromium(records: list[dict[str, Any]], name: str, root: Path) -> None:
    for profile in chromium_profiles(root):
        for cookie_path in (profile / "Network" / "Cookies", profile / "Cookies"):
            if not cookie_path.exists():
                continue
            add(records, f"browser:{name}", "cookies", cookie_path, "按域名清理会退出 Claude 登录")
            records[-1]["claude_domain_rows"] = cookie_count(cookie_path, "cookies", "host_key")
        for relative, kind in (
            ("Local Storage", "local_storage"),
            ("IndexedDB", "indexed_db"),
            ("Service Worker", "service_worker"),
            ("Session Storage", "session_storage"),
            ("Cache", "cache"),
            ("Code Cache", "code_cache"),
            ("GPUCache", "gpu_cache"),
        ):
            add(
                records,
                f"browser:{name}",
                kind,
                profile / relative,
                "只能在浏览器站点数据界面按 Claude 域名清理",
            )


def audit_firefox(records: list[dict[str, Any]], root: Path) -> None:
    if not root.is_dir():
        return
    for profile in sorted(path for path in root.iterdir() if path.is_dir()):
        cookie_path = profile / "cookies.sqlite"
        if cookie_path.exists():
            add(records, "browser:Firefox", "cookies", cookie_path, "按域名清理会退出 Claude 登录")
            records[-1]["claude_domain_rows"] = cookie_count(cookie_path, "moz_cookies", "host")
        for relative, kind in (
            ("storage", "site_storage"),
            ("cache2", "cache"),
            ("sessionstore-backups", "session_storage"),
        ):
            add(
                records,
                "browser:Firefox",
                kind,
                profile / relative,
                "只能在浏览器站点数据界面按 Claude 域名清理",
            )


def audit_browsers(records: list[dict[str, Any]]) -> None:
    support = Path.home() / "Library" / "Application Support"
    chromium_roots = {
        "Chrome": support / "Google" / "Chrome",
        "Edge": support / "Microsoft Edge",
        "Brave": support / "BraveSoftware" / "Brave-Browser",
        "Chromium": support / "Chromium",
        "Arc": support / "Arc" / "User Data",
    }
    for name, root in chromium_roots.items():
        audit_chromium(records, name, root)
    audit_firefox(records, support / "Firefox" / "Profiles")
    audit_discovered_browser_data(records, support)

    library = Path.home() / "Library"
    for path in (
        library / "Safari",
        library / "Containers" / "com.apple.Safari" / "Data" / "Library",
        library / "HTTPStorages" / "com.apple.Safari",
    ):
        add(
            records,
            "browser:Safari",
            "site_data_root",
            path,
            "使用 Safari 管理网站数据按 Claude 域名清理",
        )


def normalized_domain_name(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def audit_discovered_browser_data(records: list[dict[str, Any]], support: Path) -> None:
    """Find unlisted Chromium/fingerprint-browser profiles without exposing values."""
    if not support.is_dir():
        return
    known_paths = {item["path"] for item in records}
    domain_needles = tuple(normalized_domain_name(domain) for domain in DOMAINS)
    skip_dirs = {
        "blob_storage",
        "Cache",
        "CacheStorage",
        "Code Cache",
        "GPUCache",
        "node_modules",
    }

    for current, dirs, files in os.walk(support, onerror=lambda _: None):
        current_path = Path(current)
        try:
            depth = len(current_path.relative_to(support).parts)
        except ValueError:
            continue
        if depth > 7:
            dirs[:] = []
            continue

        for dirname in list(dirs):
            candidate = current_path / dirname
            normalized = normalized_domain_name(dirname)
            if any(needle in normalized for needle in domain_needles):
                shown = display(candidate)
                if shown not in known_paths:
                    add(
                        records,
                        "browser:discovered",
                        "domain_named_storage",
                        candidate,
                        "按所属浏览器配置文件清除对应 Claude 站点数据",
                    )
                    known_paths.add(shown)
                dirs.remove(dirname)

        for filename, table, column in (
            ("Cookies", "cookies", "host_key"),
            ("cookies.sqlite", "moz_cookies", "host"),
        ):
            if filename not in files:
                continue
            candidate = current_path / filename
            shown = display(candidate)
            if shown in known_paths:
                continue
            count = cookie_count(candidate, table, column)
            if not count:
                continue
            add(
                records,
                "browser:discovered",
                "cookies",
                candidate,
                "按域名清理会退出 Claude 登录",
            )
            records[-1]["claude_domain_rows"] = count
            known_paths.add(shown)

        dirs[:] = [dirname for dirname in dirs if dirname not in skip_dirs]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="只读盘点 Claude Code、Desktop 和浏览器残留；不输出内容或秘密。"
    )
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    records: list[dict[str, Any]] = []
    audit_cli(records)
    audit_desktop(records)
    audit_browsers(records)

    if args.json:
        print(json.dumps({"domains": DOMAINS, "records": records}, ensure_ascii=False, indent=2))
    else:
        for item in records:
            count = item.get("claude_domain_rows")
            suffix = "" if count is None else f" domain_rows={count}"
            print(f"[{item['scope']}] {item['kind']}: {item['path']}{suffix}")
            print(f"  删除影响：{item['impact_if_removed']}")
        print(f"总计：{len(records)} 项；脚本只读，不会删除任何内容。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
