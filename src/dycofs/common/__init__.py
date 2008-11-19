#!/usr/bin/env python

class Connection:
	peer_id = ""		# peer id
	peer_host = ""		# peer host/address
	peer_port = ""		# peer port
	peer_gw = ""		# gateway port

	def __init__(self):
		print "[connection] initiated", self.peer_id
	
	def __del__(self):
		print "[connection] destroyed", self.peer_id

	def send(self, data):
		pass
	
	def receive(self, data):
		pass
	

