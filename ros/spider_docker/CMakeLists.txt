cmake_minimum_required(VERSION 3.0.2)
project(spider_docker)
find_package(catkin REQUIRED)
catkin_package()
catkin_install_python(PROGRAMS scripts/udp_joy.py scripts/joy_gate.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})
