"""Windows 用: ゲームパッド (Logicool F310 XInput モード) を UDP でコンテナへ送る。

パッド i (0 始まり) -> UDP ポート 5001+i -> /robot{i+1}/joy
出力の並びは Linux の joy_node で F310(XInput) を読んだ場合と同じ。
  axes   : LX, LY, LT, RX, RY, RT, 十字X, 十字Y (スティックは 左/上 が +、トリガは 離す +1 / 押す -1)
  buttons: A, B, X, Y, LB, RB, Back, Start, Guide(常に0), L3, R3
"""
import argparse, os, socket, struct, time

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", "1")
import pygame

BASE_PORT = 5001
SDL_BTN = [0, 1, 2, 3, 4, 5, 6, 7, None, 8, 9]  # Linux index -> SDL index (Guide は無し)


def convert(j):
    a = lambda i: j.get_axis(i) if i < j.get_numaxes() else 0.0
    hx, hy = j.get_hat(0) if j.get_numhats() else (0, 0)
    axes = [-a(0), -a(1), -a(4), -a(2), -a(3), -a(5), float(-hx), float(hy)]
    btn = [1 if (s is not None and s < j.get_numbuttons() and j.get_button(s)) else 0 for s in SDL_BTN]
    return axes, btn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="127.0.0.1")
    ap.add_argument("--pads", type=int, default=1, help="使うパッド数 (1〜3)")
    ap.add_argument("--rate", type=float, default=20.0)
    args = ap.parse_args()

    pygame.init()
    pygame.joystick.init()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    pads = {}
    print(f"bridge start: pads={args.pads} target={args.target}  (Ctrl+C で終了)")
    try:
        while True:
            pygame.event.pump()
            n = pygame.joystick.get_count()
            for i in range(min(args.pads, n)):
                if i not in pads:
                    pads[i] = pygame.joystick.Joystick(i)
                    print(f"pad{i}: {pads[i].get_name()} -> UDP {BASE_PORT + i}")
                axes, btn = convert(pads[i])
                sock.sendto(struct.pack("<8f11B", *axes, *btn), (args.target, BASE_PORT + i))
            time.sleep(1.0 / args.rate)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
