#!/usr/bin/env python
from dycofs.common.multicast import MulticastDiscoveryService
from time import sleep

def new_node(name, host, address, port):
	"""a new node was discovered"""
	print "new: %s[%s] (%s:%d)" %(name, host, address, port)

def del_node(name):
	"""a node was removed"""
	print "del: %s" %(name)

ds = MulticastDiscoveryService(new_node, del_node)
ds.start()

try:
	while True:
		sleep(10)
except KeyboardInterrupt:
	print "Stopped monitoring for nodes"
	ds.stop()
