# --- Imports --- #

from collections import deque

# --- Stack Class --- #

class Stack:
	def __init__(self):
		
		self.__stack = deque()
		
	def __len__(self):
		return len(self.__stack)
		
	def add(self, item):
		self.__stack.append(item)
		
	def pop(self):
		return self.__stack.pop()