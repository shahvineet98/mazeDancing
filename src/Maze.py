#!/usr/bin/env python2

import numpy
from consts import *

from a_star import *

class Maze(object):
	def __init__(self, n=8):
		self.orientation = Direction.FORWARD
		self.maze = [[Maze_Cell.UNKNOWN for i in range(n)] for j in range(n)]
		self.pos = (n//2, n//2)
		self.start = self.pos
		self.maze[self.start[0]][self.start[1]] = Maze_Cell.OPEN

		self.path = []

	# get new step
	def step(self):
		new_pos = None
		if self.orientation == Direction.FORWARD:
			new_pos = (self.pos[0] - 1, self.pos[1])
		elif self.orientation == Direction.RIGHT:
			new_pos = (self.pos[0], self.pos[1] + 1)
		elif self.orientation == Direction.BACKWARD:
			new_pos = (self.pos[0] + 1, self.pos[1])
		elif self.orientation == Direction.LEFT:
			new_pos = (self.pos[0], self.pos[1] - 1)

		# update based on new point
		self._update_maze(new_pos)
	
	# we don't step, we just see that it is open
	# HACK, we are just going to step and go back
	def mark_ahead(self):
		_old = self.pos
		self.step()
		self.pos = _old
	
	def next_pos(self, t=Follower.RIGHT):
		if t == Follower.RIGHT:
			if maze[self.pos[0] + 1][self.pos[1]] == Maze_Cell.OPEN:
				return Direction.RIGHT
			elif maze[self.pos[0]][self.pos[1] + 1] == Maze_Cell.OPEN:
				return Direction.FORWARD
			elif maze[self.pos[0] - 1][self.pos[1]] == Maze_Cell.OPEN:
				return Direction.LEFT
			else:
				return Direction.BACKWARD

	# update orientation
	def turn(self, direction):
		self.orientation = Direction.TURN[self.orientation][direction]
	
	# check bounds on our new point
	def _new_pos_is_valid(self, x, y):
		maze = len(self.maze)
		if x < 0 or y < 0 or x >= maze or y >= maze:
			return False
		return True
	
	def _update_maze(self, new_pos):
		# check bounds
		if not self._new_pos_is_valid(*new_pos):
			self._expand_maze()
			n = len(self.maze)//2
			new_pos = (new_pos[0] + n//2, new_pos[1] + n//2)
			self.start = (self.start[0] + n//2, self.start[1] + n//2)

		# move
		self.pos = new_pos
		# mark internally
		self.maze[self.pos[0]][self.pos[1]] = Maze_Cell.OPEN
	
	# return best path from self.start to self.pos
	# based on self.maze
	def best_path(self):
		# A* algo
		a_star = AStar()
		a_star.init_maze(self.maze, self.start, self.pos)
		a_star.process()
		return _best_scout_path(a_star, self.maze), _best_worker_path(a_star, self.maze)

	# take nxn maze and pad to 2nx2n
	def _expand_maze(self):
		n = len(self.maze)
		padding = [Maze_Cell.UNKNOWN for i in range(n//2)]
		new_maze = []
		# add first n/2 rows
		for i in range(n//2):
			new_maze.append([Maze_Cell.UNKNOWN for j in range(2*n)])
		for row in self.maze:
			new_maze.append(padding + row + padding)
		for i in range(n//2):
			new_maze.append([Maze_Cell.UNKNOWN for j in range(2*n)])
		self.maze = new_maze

	def print_maze(self):
		for row in self.maze:
			string = ""
			for ele in row:
				if ele == Maze_Cell.OPEN:
					string += " "
				else:
					string += "X"
			print(string)

	
def _best_scout_path(a_star, maze):
	cells = []
	cell = a_star.end
	while cell is not a_star.start:
		cells.append(cell)
		cell = cell.parent
	cells.append(cell)
	return _extract_path(cells, maze)
	
def _best_worker_path(a_star, maze):
	# HACK
	scout = _best_scout_path(a_star, maze)
	_rev = scout[::-1]
	ret = []
	for d in _rev:
		if d == Direction.RIGHT:
			ret.append(Direction.LEFT)
		elif d == Direction.LEFT:
			ret.append(Direction.RIGHT)
		elif d == Direction.FORWARD:
			ret.append(Direction.BACKWARD)
		else:
			ret.append(Direction.FORWARD)
	return ret
	# get path from algo
	cells = []
	cell = a_star.end
	while cell is not a_star.start:
		cells.insert(0, cell)
		cell = cell.parent
	cells.insert(0, cell)
	return _extract_path(cells, maze)

def _extract_path(cells, maze):
	# of these cells, which are actual nodes
	nodes = []
	for cell in cells:
		out = 0
		if Maze_Cell.OPEN == maze[cell.x-1][cell.y]:
			out += 1
		if Maze_Cell.OPEN == maze[cell.x+1][cell.y]:
			out += 1
		if Maze_Cell.OPEN == maze[cell.x][cell.y-1]:
			out += 1
		if Maze_Cell.OPEN == maze[cell.x][cell.y+1]:
			out += 1
		if out > 2:
			nodes.append(cell)
	ret = []
	last = (False, None, None)
	for cell in cells:
		# cell is how I left
		# last[1] is the node's position
		# last[2] is how I entered
		if last[0]:
			# NOTE
			# coordinates are mixed up
			leave_x = cell.y - last[1].y
			leave_y = cell.x - last[1].x
			enter_x = last[1].y - last[2].y
			enter_y = last[1].x - last[2].x

			leave_dir = Maze_Cell.CELL_TO_DIR[leave_x][leave_y]
			enter_dir = Maze_Cell.CELL_TO_DIR[enter_x][enter_y]
			direction = Maze_Cell.DIR_TO_TURN[enter_dir][leave_dir]
			ret.append(direction)
		last = (cell in nodes, cell, last[1])

	return ret
