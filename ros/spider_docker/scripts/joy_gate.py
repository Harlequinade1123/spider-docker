#!/usr/bin/env python3
"""joy_raw (実入力: joy_node / udp_joy) を joy へ中継する。

~replay が true の間は中継を止める。rosbag 再生が joy へ直接発行するときに、
実入力と混ざらないようにするため。
  rosparam set /<robot>/joy_gate/replay true|false
"""
import rospy
from sensor_msgs.msg import Joy


def main():
    rospy.init_node("joy_gate")
    pub = rospy.Publisher("joy", Joy, queue_size=10)
    rospy.set_param("~replay", False)

    def cb(msg):
        if not rospy.get_param_cached("~replay", False):
            pub.publish(msg)

    rospy.Subscriber("joy_raw", Joy, cb, queue_size=10)
    rospy.spin()


if __name__ == "__main__":
    main()
