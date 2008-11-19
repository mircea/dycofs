#!/usr/bin/env python

class DataMapper:
	def __init__(self):
		print "[mapper] initiated"
	
	def __del__(self):
		print "[mapper] destroyed"

	def list(self):
		pass

	# resource names might include actions to be executed
	# example: /all/average/temperature
	#   where "average" is the action name
	#         "all" is the group where the action is performed
	
	# atomic complete read
	def read(self, resource_name):
		pass
	
	# atomic complete write
	def write(self, resource_name):
		pass
	
	
