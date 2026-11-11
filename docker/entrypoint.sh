#!/bin/bash
set -e
source /opt/ros/noetic/setup.bash
source /spider_ws/devel/setup.bash
case "${1:-run}" in
  run)
    python3 /opt/spider/spider_gen.py launch /config/robots.yaml > /tmp/robots.launch
    exec roslaunch /tmp/robots.launch ;;
  stop)   # 起動中のロボットを種別ごとに停止 (STOP_KING / STOP_SHIN)
    for n in $(python3 /opt/spider/spider_gen.py names /config/robots.yaml); do
      for node in $(rosnode list | grep "^/$n/"); do
        rosnode kill "$node"
      done
    done ;;
  bag-record)   # 起動中の全ロボットの joy を /bags に記録 (BAG_NAME 省略で日時)
    topics=$(rostopic list | grep '/joy$' || true)
    if [ -z "$topics" ]; then echo "記録できる /joy がありません (ロボットが起動していません)"; exit 1; fi
    f="/bags/${BAG_NAME:-$(date +%Y%m%d-%H%M%S)}.bag"
    echo "記録中: $f"; echo "$topics"; echo "(Ctrl+C で終了)"
    rosbag record -O "$f" $topics || true
    chown --reference=/bags "$f" 2>/dev/null || true ;;
  bag-play)     # /bags/$BAG を再生 (LOOP=1 で繰り返し)。再生中は実際のパッド入力を遮断する
    f="/bags/${BAG:?BAG を指定してください}"
    if [ ! -f "$f" ]; then echo "見つかりません: $f"; exit 1; fi
    topics=$(rosbag info "$f" | grep -oE '/[A-Za-z0-9_]+/joy' | sort -u)
    for t in $topics; do
      if ! rosnode list | grep -q "^${t%/joy}/joy_gate$"; then
        echo "${t%/joy} が起動していません (記録時と同じ KING / SHIN で make up してください)"; exit 1
      fi
    done
    restore() {   # ニュートラルを送ってから実入力へ戻す
      for t in $topics; do
        rostopic pub -1 "$t" sensor_msgs/Joy '{axes: [0,0,1,0,0,1,0,0], buttons: [0,0,0,0,0,0,0,0,0,0,0]}' >/dev/null 2>&1 || true
        rosparam set "${t%/joy}/joy_gate/replay" false
      done
    }
    trap restore EXIT
    for t in $topics; do rosparam set "${t%/joy}/joy_gate/replay" true; done
    args=""; if [ "${LOOP:-}" = 1 ]; then args="-l"; fi
    echo "再生中: $f $args (Ctrl+C で終了)"
    rosbag play $args "$f" ;;
  *) exec "$@" ;;
esac
