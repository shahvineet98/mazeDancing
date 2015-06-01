#!/usr/bin/env python2

import time
import math

# ROS
import rospy
from roslib import message

# movement
from geometry_msgs.msg import Twist
from std_msgs.msg import FLoat64
from consts import *

# NOTE MUST BE import by a ROS NODE
class Move_Manager(object):
	def __init__(self):
		self._tw_pub = rospy.Publisher(TWIST_PUB, Twist)
		self._rate = rospy.Rate(RATE)
		self._checks = {\
			"FULL": None,\
			"MIDDLE": False,\
			"LEFT": False,\
			"RIGHT": False\
		}
		self._sense_subs = [\
			rospy.Subscriber(PCL_FULL_IO, Float64, self._pcl(info="FULL")\
			rospy.Subscriber(PCL_LEFT_IO, Float64, self._pcl(info="LEFT"))\
			rospy.Subscriber(PCL_RIGHT_IO, Float64, self._pcl(info="RIGHT"))\
			rospy.Subscriber(PCL_MIDDLE_IO, Float64, self._pcl(info="MIDDLE"))\
		]
	
	# generic callback, use info
	def _pcl(self, data, info=None):
		if info is None:
			rospy.loginfo("pcl callback has None as info")
			return

		pcl = data.data
		if info == "FULL":
			self._checks[info] = pcl
		elif info == "LEFT" or info == "RIGHT":
			self._checks[info] = pcl > MIN_TURN_DIST
		elif info == "MIDDLE":
			self._checks[info] = pcl > MIN_FORWARD_DIST
		else:
			rospy.loginfo("invalid info argument: " + info)
	
	def check(self, direction):
		if direction == Direction.RIGHT:
			return self._checks["RIGHT"]
		elif direction == Direction.LEFT:
			return self._checks["LEFT"]
		elif direction == Direction.FORWARD:
			return self._checks["MIDDLE"]
		else:
			rospy.log("you asked to check backwards?")
		return result
	
	# we always turn orthogonally so we won't ask for z input
	def move(self, direction, hardcode=True):
		# NOTE this should be the only place where we delay after movement
		if direction == Direction.FORWARD:
			self._send_twist(TWIST_X, 0)
		elif direction == Direction.BACKWARD:
			self._send_twist(-TWIST_X, 0)
		elif direction == Direction.RIGHT or direction == Direction.LEFT:
			self._turn(direction, hardcode)
		else:
			rospy.loginfo("invalid direction to move() " + str(direction))

	# halt movement of the turtlebot immediately
	def stop(self):
		twist = Twist()
		self.tw_pub.publish(twist)

	def _turn(self, direction, hardcode):
		# HACK we just hardcode a fixed number of identical twist messages to do
		# an orthogonal turn on a flat surface
		val = TWIST_Z if direction == Direction.RIGHT else -TWIST_Z
		self._send_twist(0, val)

	# actually send message
	def _send_twist(self, x, z):
		for _ in range(TWIST_NUM):
			twist = Twist()
			twist.linear.x = x
			twist.angular.z = z
			rospy.loginfo("new twist message: " + str(twist))
			self._tw_pub.publish(twist)
			self._rate.sleep()
		self.stop()
		rospy.sleep(DELAY)
