#!/usr/bin/env python3
"""robots.yaml から launch (コンテナ内) / compose の devices (ホスト側) を生成する。"""
import os, sys, yaml

BASE_PORT = 5000
PKG = {"kingspider": ("kingspider", "kingspider_joy_node"),
       "shin_spider": ("shin_spider", "shin_spider_node")}


def load(path):
    robots = (yaml.safe_load(open(path)) or {}).get("robots", [])
    names = [r["name"] for r in robots]
    if len(set(names)) != len(names):
        sys.exit("robots.yaml: name が重複")
    for r in robots:
        if r.get("type") not in PKG:
            sys.exit("robots.yaml: type は kingspider | shin_spider")
    # KING / SHIN = 起動する台数 (未指定なら robots.yaml の全台)。yaml の並び順で先頭から選ぶ
    want = {"kingspider": os.environ.get("KING", ""), "shin_spider": os.environ.get("SHIN", "")}
    if any(want.values()):
        want = {t: int(n or 0) for t, n in want.items()}
        sel = []
        for t in PKG:
            pool = [r for r in robots if r["type"] == t]
            if want[t] > len(pool):
                sys.exit(f"robots.yaml に {t} は {len(pool)} 台しかありません")
            sel += pool[:want[t]]
        robots = [r for r in robots if r in sel]
    if not 1 <= len(robots) <= 3:
        sys.exit(f"起動するロボットは 1〜3 台 (現在 {len(robots)} 台)")
    return robots


def launch(path, dry, joy):
    out = ['<launch>']
    for i, r in enumerate(load(path)):
        pkg, node = PKG[r["type"]]
        out.append(f'  <group ns="{r["name"]}">')
        if joy == "js":
            out.append(f'    <node pkg="joy" type="joy_node" name="joy_node">'
                       f'<param name="dev" value="/dev/input/js{i}"/><param name="deadzone" value="0.05"/>'
                       f'<param name="autorepeat_rate" value="20"/><remap from="joy" to="joy_raw"/></node>')
        elif joy == "udp":
            out.append(f'    <node pkg="spider_docker" type="udp_joy.py" name="udp_joy">'
                       f'<param name="port" value="{BASE_PORT + i + 1}"/></node>')
        # 実入力 (joy_raw) -> joy。rosbag 再生中は遮断される
        out.append('    <node pkg="spider_docker" type="joy_gate.py" name="joy_gate"/>')
        out.append(f'    <node pkg="{pkg}" type="{node}" name="{node}" output="screen">')
        if r["type"] == "shin_spider":
            out.append('      <rosparam file="$(find shin_spider)/config/shin_spider.yaml" command="load"/>')
            out.append(f'      <param name="dry_run" value="{str(dry).lower()}"/>')
        out.append(f'      <param name="joy_topic" value="joy"/>')
        out.append(f'      <param name="device_name" value="{r["serial"]}"/>')
        out.append('    </node>')
        out.append('  </group>')
    out.append('</launch>')
    return "\n".join(l for l in out if l) + "\n"


def names(path, dry, joy):
    """停止対象の name。STOP_KING / STOP_SHIN が空でなければ、その種別の起動中ロボット全部"""
    flags = (("kingspider", "STOP_KING"), ("shin_spider", "STOP_SHIN"))
    types = [t for t, v in flags if os.environ.get(v)]
    if not types:
        sys.exit("KING=1 または SHIN=1 (または両方) を指定してください")
    sel = [r["name"] for r in load(path) if r["type"] in types]
    if not sel:
        sys.exit("該当するロボットは起動していません")
    return "\n".join(sel)


def compose(path, dry, joy):
    devs = []
    if not dry:
        for i, r in enumerate(load(path)):
            devs.append(r["serial"])
            if joy == "js":
                devs.append(f"/dev/input/js{i}")
    s = "services:\n  spider:\n"
    if devs:
        s += "    devices:\n" + "".join(f'      - "{d}:{d}"\n' for d in devs)
    else:
        s += "    {}\n"
    return s


if __name__ == "__main__":
    cmd, path = sys.argv[1], sys.argv[2]
    dry = os.environ.get("DRY_RUN", "1") == "1"
    joy = os.environ.get("JOY_SOURCE", "udp")
    print({"launch": launch, "compose": compose, "names": names}[cmd](path, dry, joy), end="")
