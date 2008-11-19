#!/usr/bin/env python

class Storage:
	location = ""		# exported location
	access_mode = ""	# permissions rw
	
	def __init__(self):
		print "[storage] initiated"
	
	def __del__(self):
		print "[connection] destroyed"
	
	def list(self):
		pass
	
	# resource names are actual resources names
	# (without modelling actions)
	# available in the system
	
	# atomic complete read
	def read(self, resource_name):
		pass
	
	# atomic complete write
	def write(self, resource_name):
		pass
	

