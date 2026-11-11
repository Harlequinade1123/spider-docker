FROM ros:noetic-ros-base-focal
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential git python3-catkin-tools python3-vcstool python3-yaml python3-rospy \
      ros-noetic-joy \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /spider_ws
COPY spider.repos /spider_ws/spider.repos
COPY ros/spider_docker /spider_ws/spider_docker_pkg
RUN mkdir src && vcs import src < spider.repos && cp -r spider_docker_pkg src/spider_docker \
 && find src/spider_docker -type f \( -name '*.py' -o -name '*.xml' -o -name 'CMakeLists.txt' \) -exec sed -i 's/\r$//' {} + \
 && rosdep update --rosdistro noetic \
 && apt-get update && rosdep install --from-paths src --ignore-src -r -y \
 && rm -rf /var/lib/apt/lists/* \
 && . /opt/ros/noetic/setup.sh && catkin init && catkin build

COPY docker/spider_gen.py docker/entrypoint.sh /opt/spider/
# 念のため CRLF を除去 (Windows で clone して改行が変わっていても動くように)
RUN sed -i 's/\r$//' /opt/spider/entrypoint.sh /opt/spider/spider_gen.py \
 && chmod +x /opt/spider/entrypoint.sh /opt/spider/spider_gen.py
ENTRYPOINT ["/opt/spider/entrypoint.sh"]
CMD ["run"]
