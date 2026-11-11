#!/usr/bin/env python3
"""UDP パケット (Windows ブリッジ) を sensor_msgs/Joy にして発行する。

パケット: struct "<8f11B" = axes[8] (float32) + buttons[11] (uint8)
並びは Logicool F310 (XInput モード) を Linux joy_node で読んだ場合と同じ。
"""
import socket, struct, threading
import rospy
from sensor_msgs.msg import Joy

FMT = "<8f11B"
SIZE = struct.calcsize(FMT)


def main():
    rospy.init_node("udp_joy")
    port = rospy.get_param("~port")
    rate = rospy.get_param("~rate", 20.0)  # joy_node の autorepeat_rate 相当
    pub = rospy.Publisher("joy_raw", Joy, queue_size=10)  # joy_gate 経由で joy へ
    state = {"axes": [0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0], "buttons": [0] * 11}

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
    sock.settimeout(0.5)

    def rx():
        while not rospy.is_shutdown():
            try:
                data, _ = sock.recvfrom(256)
            except socket.timeout:
                continue
            if len(data) != SIZE:
                continue
            v = struct.unpack(FMT, data)
            state["axes"], state["buttons"] = list(v[:8]), list(v[8:])

    threading.Thread(target=rx, daemon=True).start()
    r = rospy.Rate(rate)
    while not rospy.is_shutdown():
        m = Joy()
        m.header.stamp = rospy.Time.now()
        m.axes, m.buttons = state["axes"], state["buttons"]
        pub.publish(m)
        r.sleep()


if __name__ == "__main__":
    main()
