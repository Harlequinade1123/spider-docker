#!/usr/bin/env python3
"""接続中のシリアルデバイスを一覧し、robots.yaml の serial を書き換える (標準ライブラリのみ)。

  python3 tools/serial_tool.py list
  python3 tools/serial_tool.py set [--robot king1]

robots.yaml は次の形式 (name / type / serial を 1 行ずつ) を想定する。コメントは保持される。
  - name: king1
    type: kingspider
    serial: /dev/ttyUSB0
"""
import argparse, glob, os, re, sys

YAML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "robots.yaml")


def devices():
    """[(パス, 実体)]。/dev/serial/by-id を優先 (番号が変わらないため)。無ければ ttyUSB*/ttyACM*"""
    out = [(p, os.path.realpath(p)) for p in sorted(glob.glob("/dev/serial/by-id/*"))]
    if not out:
        out = [(p, p) for p in sorted(glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*"))]
    return out


def robots(text):
    """[(name, type, serial)] を robots.yaml (ブロック形式) から読む"""
    pat = re.compile(r"^\s*-\s*name:\s*(\S+)\s*\n\s*type:\s*(\S+)\s*\n\s*serial:\s*(\S+)", re.M)
    return pat.findall(text)


def show(devs, used):
    if not devs:
        print("シリアルデバイスが見つかりません (接続と、Windows は attach を確認してください)")
        return
    for i, (p, real) in enumerate(devs, 1):
        tag = f"  <- {used[p]}" if p in used else ""
        print(f"  [{i}] {p}" + (f" -> {real}" if real != p else "") + tag)


def set_serial(text, name, dev):
    pat = re.compile(r"(^\s*-\s*name:\s*" + re.escape(name) + r"\s*\n\s*type:\s*\S+\s*\n\s*serial:\s*)\S+", re.M)
    return pat.subn(lambda m: m.group(1) + dev, text, count=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["list", "set"])
    ap.add_argument("--robot", default="", help="set: このロボットだけ設定 (例 king1)")
    a = ap.parse_args()

    text = open(YAML, encoding="utf-8").read()
    rb = robots(text)
    if not rb:
        sys.exit("robots.yaml から name / type / serial を読めません (ブロック形式で書いてください)")
    devs = devices()
    used = {s: n for n, _, s in rb}
    print("接続中のシリアル:")
    show(devs, used)
    if a.cmd == "list" or not devs:
        return

    targets = [r for r in rb if not a.robot or r[0] == a.robot]
    if not targets:
        sys.exit(f"robots.yaml に {a.robot} がありません: " + ", ".join(n for n, _, _ in rb))
    print("\nロボットごとに番号を入力 (Enter = 変更なし / 0 = 空にしない・スキップ)")
    for name, typ, cur in targets:
        ans = input(f"{name} ({typ}) 現在 {cur} > ").strip()
        if ans in ("", "0"):
            continue
        if not (ans.isdigit() and 1 <= int(ans) <= len(devs)):
            print("  番号が不正なのでスキップ")
            continue
        text, n = set_serial(text, name, devs[int(ans) - 1][0])
        print(f"  {name}: {devs[int(ans) - 1][0]}" if n else f"  {name}: 書き換えに失敗")
    open(YAML, "w", encoding="utf-8").write(text)
    print("\nrobots.yaml を更新しました")


if __name__ == "__main__":
    main()
