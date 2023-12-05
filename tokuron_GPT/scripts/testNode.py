#!/usr/bin/env python3
import rospy
from std_msgs.msg import String

rospy.init_node('testNode')
pub = rospy.Publisher('GPT_U', String, queue_size=1)
rate = rospy.Rate(10)
n = 0
while not rospy.is_shutdown():
    n = input("")
    pub.publish(n)
    rate.sleep()