#!/usr/bin/env python2

import time
import math

# ROS
import rospy
from roslib import message

# movement
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64, UInt32MultiArray
from consts import *

# maze solving
from Maze import Maze

# NOTE MUST BE import by a ROS NODE
class Move_Manager(object):
	def __init__(self):
		self._tw_pub = rospy.Publisher(TWIST_PUB, Twist)
		self._rate = rospy.Rate(RATE)
		self._checks = {\
			"FULL": None,\
			Direction.FORWARD: None,\
			Direction.LEFT: None,\
			Direction.RIGHT: None\
		}
		# TODO
		# should consider packaging variance and num and depth all together
		self._sense_subs = [\
			rospy.Subscriber(PCL_FULL_IO, UInt32MultiArray, self._pcl_full),\
			rospy.Subscriber(PCL_LEFT_IO, Float64, self._pcl_left),\
			rospy.Subscriber(PCL_RIGHT_IO, Float64, self._pcl_right),\
			rospy.Subscriber(PCL_MIDDLE_IO, Float64, self._pcl_middle)\
		]
		self.maze = Maze()
	
	def _pcl_left(self, data):
		if data is None:
			rospy.loginfo("data is none")
			return
		pcl = data.data
		self._checks[Direction.LEFT] = pcl

	def _pcl_right(self, data):
		if data is None:
			rospy.loginfo("data is none")
			return
		pcl = data.data
		self._checks[Direction.RIGHT] = pcl

	def _pcl_middle(self, data):
		if data is None:
			rospy.loginfo("data is none")
			return
		pcl = data.data
		self._checks[Direction.FORWARD] = pcl

	# NOTE
	# misleading since this is an array, not float64
	def _pcl_full(self, data):
		if data is None:
			rospy.loginfo("data is none")
			return
		pcl = data.data
		self._checks["FULL"] = pcl
	
	# adjust a little bit towards the goal by MIN/MAX_FORWARD_DIST
	def nudge(self):
		goal = (MAX_FORWARD_DIST + MIN_FORWARD_DIST)/2
		# NOTE most reliable measurement at the moment
		pos = self._checks["FULL"]
		diff = (goal - pos[0]) / TIME
		# _send_twist takes 1 second to perform the entire movement
		# so we should not have to scale diff at all

		# boundary conditions
		diff = min(MAX_NUDGE, diff) if diff > 0 else max(-MAX_NUDGE, diff)
		rospy.loginfo("nudge: " + str(diff))
		self._send_twist(diff, 0)

	# turning is left to the callee!
	# if True, then the robot has enough room to perform the directional movement
	def check(self, direction):
		# NOTE the most reliable measurement at the moment
		measure = self._checks["FULL"]
		direction = Direction.FORWARD

		rospy.loginfo("last variance was {}".format(self._last_variance))
		rospy.loginfo("{} > {}".format(measure, MIN_FORWARD_DIST))
		return measure[0] > MIN_FORWARD_DIST if direction == Direction.FORWARD else measure[0] > MIN_TURN_DIST
	
	# we always turn orthogonally so we won't ask for z input
	def move(self, direction, hardcode=True):
		# NOTE this should be the only place where we delay after movement
		if direction == Direction.FORWARD:
			self._send_twist(TWIST_X, 0)
			self.maze.step()
		elif direction == Direction.BACKWARD:
			self._send_twist(-TWIST_X, 0)
			self.maze.step()
		elif direction == Direction.RIGHT or direction == Direction.LEFT:
			self._turn(direction, hardcode)
			self.maze.turn(direction)
		else:
			rospy.loginfo("invalid direction to move() " + str(direction))

	# halt movement of the turtlebot immediately
	def stop(self):
		twist = Twist()
		self._tw_pub.publish(twist)

	def _turn(self, direction, hardcode):
		# HACK we just hardcode a fixed number of identical twist messages to do
		# an orthogonal turn on a flat surface
		val = -TWIST_Z if direction == Direction.RIGHT else TWIST_Z
		self._send_twist(0, val)

	# actually send message
	def _send_twist(self, x, z):
		for _ in range(TWIST_NUM):
			twist = Twist()
			twist.linear.x = x
			twist.angular.z = z
			self._tw_pub.publish(twist)
			self._rate.sleep()
		self.stop()
		rospy.sleep(DELAY)
