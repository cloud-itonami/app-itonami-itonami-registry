#!/usr/bin/env python3
"""home-sweep — ~ / ~/github / ~/.hermes の直下に迷い込んだ作業ファイルを ~/_attic/<date>/ へ退避する。

seiri の no-agent cron job から毎日呼ばれる。黙って捨てない: 削除は一切せず、移動のみ。
移動元→移動先は ~/_attic/<date>/MANIFEST.tsv に追記する（戻すときは逆向きに mv）。

  - 退避する: 既知の置き場所以外にある scratch 拡張子のファイル、scratch 名のディレクトリ（git を含まないもの）
  - 報告のみ: ad-hoc 位置の git worktree / clone、正体不明の新規ディレクトリ、symlink
  - 触らない: MIN_AGE 以内に更新されたもの（使用中の可能性）、ALLOW に載っているもの

stdout が空なら hermes cron は何も配信しない。--dry-run で移動せず計画だけ出す。
"""
import datetime
import os
import re
import shutil
import sys
import time

HOME = os.path.expanduser("~")
TODAY = datetime.date.today().isoformat()
ATTIC = os.path.join(HOME, "_attic", TODAY)
MIN_AGE = 6 * 3600
DRY = "--dry-run" in sys.argv

SCRATCH_FILE = re.compile(
    r"\.(txt|out|err|log|py|sh|diff|patch|json|jsonl|csv|tsv|md|html|edn|status|tmp)$"
    r"|\.bak[-.\w]*$|\.tmp\d+$|^(probe|tmp|scratch)",
    re.I,
)
SCRATCH_DIR = re.compile(
    r"^(tmp|temp|scratch|ws|workspace|work|plans|out|probe)([-_.].*)?$|[-_](work|wip|tmp|scratch)$|^fal_|^\.gp-analysis",
    re.I,
)
# ~ 直下の dotfile はツールの設定が多いので、明白な作業ダンプ（txt/diff/out/py/sh）だけを対象にする。
DOT_SCRATCH = re.compile(r"^\.[^.]+.*\.(txt|diff|patch|out|py|sh)$", re.I)
SEEN = os.path.join(HOME, ".hermes", "profiles", "seiri", "workspace", "home-sweep-reported.txt")
ADHOC_WT = re.compile(r"^(_?k?wt\d*|worktrees?|.*-worktree)([-_].*)?$", re.I)

# 既存の正規エントリ。ここに無い新規ディレクトリは報告だけする（移動はしない）。
ALLOW = {
    HOME: {
        "_attic", "90-docs", "Applications", "Applications (Parallels)", "bin", "Claude", "Desktop",
        "Documents", "Downloads", "github", "Library", "Movies", "Music", "OrbStack", "Parallels",
        "Pictures", "Public", "ShareMouse", "models", "kotoba-lang", "network-awai", "repo-archive",
        "club-shinshi-app", "web3m-build", "mangaka-arc0-1-tailscale", "dsv41-shard11",
        "ternary-uncensored.NCsszJ", "hermes-workspace", "sec-audit-work", "aiueos-work",
    },
    os.path.join(HOME, "github"): {
        "cloud-itonami", "com-junkawasaki", "edu-mit-cybernetics-ja", "kotoba-lang", "network-awai", "wt", "workspaces",
    },
    os.path.join(HOME, ".hermes"): {
        "config.yaml", ".env", "auth.json", "auth.lock", "SOUL.md", "channel_directory.json", "install_id",
        "models_dev_cache.etag", "models_dev_cache.json", "ollama_cloud_models_cache.json",
        "provider_models_cache.json", "processes.json", "profile.yaml", "spawn-ledger.json",
        "webhook_subscriptions.json", "desktop-build-stamp.json", "web-ui-build-stamp.json",
        "interrupt_debug.log", "mail_poll_run.status", "mail_poll_run.out",
    },
}
# ~/.hermes 直下のディレクトリと DB/lock 類は hermes 本体の管理物なので対象外。
HERMES_KEEP = re.compile(r"\.(db|db-wal|db-shm|pid|lock)$|^(state|gateway)")


def newest_mtime(path):
    st = os.lstat(path).st_mtime
    if os.path.isdir(path) and not os.path.islink(path):
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in (".git", "node_modules")]
            for f in files:
                if f != ".DS_Store":
                    try:
                        st = max(st, os.lstat(os.path.join(root, f)).st_mtime)
                    except OSError:
                        pass
    return st


def has_git(path, depth=3):
    for root, dirs, files in os.walk(path):
        if ".git" in dirs or ".git" in files:
            return True
        if root[len(path):].count(os.sep) >= depth:
            dirs[:] = []
        dirs[:] = [d for d in dirs if d != "node_modules"]
    return False


def classify(root, name):
    """-> ("move"|"report"|None, reason)"""
    p = os.path.join(root, name)
    if name in ALLOW.get(root, ()) or name == ".DS_Store":
        return None, ""
    if os.path.islink(p):
        return None, ""
    is_hermes = root == os.path.join(HOME, ".hermes")
    if is_hermes and (name.startswith(".") or os.path.isdir(p) or HERMES_KEEP.search(name)):
        return None, ""
    if root == HOME and name.startswith(".") and os.path.isdir(p):
        return None, ""  # ツールの設定ディレクトリ（~/.foo）は正規
    if os.path.isfile(p):
        if name.startswith("."):
            return ("move", "scratch dotfile") if DOT_SCRATCH.match(name) else (None, "")
        if SCRATCH_FILE.search(name) or is_hermes:
            return "move", "scratch file"
        return "report", "unknown file"
    if os.path.isdir(p):
        if has_git(p):
            if ADHOC_WT.match(name) or root != HOME:
                return "report", "git worktree/clone at ad-hoc location"
            return "report", "git repo at home root"
        if SCRATCH_DIR.match(name) or ADHOC_WT.match(name):
            return "move", "scratch dir (no git)"
        if not os.listdir(p):
            return "move", "empty dir"
        return "report", "unknown dir"
    return None, ""


def main():
    now = time.time()
    moved, reported, manifest = [], [], []
    for root in ALLOW:
        if not os.path.isdir(root):
            continue
        for name in sorted(os.listdir(root)):
            action, why = classify(root, name)
            if not action:
                continue
            p = os.path.join(root, name)
            try:
                if now - newest_mtime(p) < MIN_AGE:
                    continue
            except OSError:
                continue
            rel = p[len(HOME):].lstrip("/")
            if action == "report":
                reported.append(f"  ~/{rel}  ({why})")
                continue
            dst = os.path.join(ATTIC, "home", rel)
            if os.path.lexists(dst):
                dst += f".{int(now)}"
            if not DRY:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.move(p, dst)
                manifest.append(f"{p}\t{dst}\n")
            moved.append(f"  ~/{rel}  ({why})")
    if manifest:
        with open(os.path.join(ATTIC, "MANIFEST.tsv"), "a") as f:
            f.writelines(manifest)

    # 30 日を過ぎた attic は削除せず、手動確認を促すだけ。
    stale = []
    attic_root = os.path.join(HOME, "_attic")
    if os.path.isdir(attic_root):
        cutoff = datetime.date.today() - datetime.timedelta(days=30)
        for d in sorted(os.listdir(attic_root)):
            try:
                if datetime.date.fromisoformat(d) < cutoff:
                    stale.append(f"  ~/_attic/{d}")
            except ValueError:
                pass

    # 報告は新顔だけ（同じ worktree を毎日並べない）。解消したものは seen から消える。
    try:
        seen = set(open(SEEN).read().splitlines())
    except OSError:
        seen = set()
    new_reported = [r for r in reported if r not in seen]
    if not DRY:
        os.makedirs(os.path.dirname(SEEN), exist_ok=True)
        with open(SEEN, "w") as f:
            f.write("\n".join(reported) + ("\n" if reported else ""))
    persistent = len(reported) - len(new_reported)
    reported = new_reported
    if not (moved or reported or stale):
        return
    print(f"home-sweep {TODAY}{' (dry-run)' if DRY else ''}")
    if moved:
        print(f"退避 {len(moved)} 件 → ~/_attic/{TODAY}/ (MANIFEST.tsv に記録):")
        print("\n".join(moved))
    if reported:
        print(f"要確認 {len(reported)} 件（移動していない）:")
        print("\n".join(reported))
    if persistent:
        print(f"（既報で未解消の要確認 {persistent} 件は省略。一覧: {SEEN}）")
    if stale:
        print("30 日超の attic（中身を確認して手動で削除）:")
        print("\n".join(stale))


if __name__ == "__main__":
    main()
