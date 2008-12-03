#!/usr/bin/env python
from threading import Thread
import pybonjour
import sys
import select
import socket

class DiscoveryService(Thread):
	def __init__(self, add_callback, remove_callback):
		Thread.__init__(self)
		pass

	def run(self):
		pass


# Looking for DyCoFS published services
TYPE = '_dycofs._tcp'
		

class AvahiDiscoveryService(DiscoveryService):
	"""docstring for AvahiMulticastDiscovery"""
	def __init__(self, add_callback, remove_callback):
		import dbus, avahi
		from dbus import DBusException
		from dbus.mainloop.glib import DBusGMainLoop
		import gobject
		
		super(AvahiDiscoveryService, self).__init__(add_callback, remove_callback)
		self.add_callback = add_callback
		self.remove_callback = remove_callback
		
		dbus_loop = DBusGMainLoop(set_as_default=True)
		self.message_bus = dbus.SystemBus(mainloop=dbus_loop)
		self.avahi_server = dbus.Interface( self.message_bus.get_object(avahi.DBUS_NAME, '/'),
				'org.freedesktop.Avahi.Server')
		sbrowser = dbus.Interface(self.message_bus.get_object(avahi.DBUS_NAME,
				self.avahi_server.ServiceBrowserNew(avahi.IF_UNSPEC,
					avahi.PROTO_UNSPEC, TYPE, 'local', dbus.UInt32(0))),
				avahi.DBUS_INTERFACE_SERVICE_BROWSER)

		sbrowser.connect_to_signal("ItemNew", self.myhandler_add)
		sbrowser.connect_to_signal("ItemRemove", self.myhandler_del)
		self.mainloop = gobject.MainLoop()
		gobject.threads_init()
		self.context = self.mainloop.get_context()
		self.running = True
		
	def service_resolved_add(self, *args):
		self.add_callback(args[2]+"."+args[3]+"."+args[4], args[5], args[7], args[8])
	
	def print_error(self, *args):
		print 'error_handler'
		print args[0]
	
	def myhandler_del(self, interface, protocol, name, stype, domain, flags):
		#import dbus, avahi
		#print "Deleted service '%s' type '%s' domain '%s' " % (name, stype, domain)
		#if flags & avahi.LOOKUP_RESULT_LOCAL: # local service, skip
		#	pass
		#print interface, protocol, name, stype, domain, flags
		self.remove_callback(name+"."+stype+"."+domain);
	
	def myhandler_add(self, interface, protocol, name, stype, domain, flags):
		import dbus, avahi
		#print "Found service '%s' type '%s' domain '%s' " % (name, stype, domain)
		if flags & avahi.LOOKUP_RESULT_LOCAL: # local service, skip
			pass
		self.avahi_server.ResolveService(interface, protocol, name, stype, 
			domain, avahi.PROTO_UNSPEC, dbus.UInt32(0), 
			reply_handler=self.service_resolved_add, error_handler=self.print_error)
	
	def run(self):
		"""docstring for run"""
		while self.running:
			self.context.iteration(True)
	
	def stop(self):
		self.running = False
		self.mainloop.quit()

class BonjourDiscoveryService(DiscoveryService):
	"""docstring for BonjourDiscoveryService"""
	def __init__(self, add_callback, remove_callback):	
		super(BonjourDiscoveryService, self).__init__(add_callback, remove_callback)
		self.add_callback = add_callback
		self.remove_callback = remove_callback
		self.TIMEOUT  = 5
		self.queried  = []
		self.resolved = []
		self.browse_sdRef = pybonjour.DNSServiceBrowse(regtype = TYPE,
			callBack = self.browse_callback)
	
	def query_record_callback(self,sdRef, flags, interfaceIndex, errorCode, fullname,
							  rrtype, rrclass, rdata, ttl):
		if errorCode == pybonjour.kDNSServiceErr_NoError:
			#print '  IP		 =', socket.inet_ntoa(rdata)
			self.queried.append(socket.inet_ntoa(rdata))
	
	def resolve_callback(self,sdRef, flags, interfaceIndex, errorCode, fullname,
						 hosttarget, port, txtRecord):
		if errorCode != pybonjour.kDNSServiceErr_NoError:
			return
		#print 'Resolved service:'
		#print '  fullname	 =', fullname
		#print '  hosttarget =', hosttarget
		#print '  port		 =', port
		query_sdRef = \
			pybonjour.DNSServiceQueryRecord(interfaceIndex = interfaceIndex,
											fullname = hosttarget,
											rrtype = pybonjour.kDNSServiceType_A,
											callBack = self.query_record_callback)
		try:
			while not self.queried:
				ready = select.select([query_sdRef], [], [], self.TIMEOUT)
				if query_sdRef not in ready[0]:
					print 'Query record timed out'
					break
				pybonjour.DNSServiceProcessResult(query_sdRef)
			else:
				#print self.queried.pop()
				self.add_callback(fullname[:-1].decode('string_escape'), hosttarget[:-1], self.queried.pop(), port)
		finally:
			query_sdRef.close()
		self.resolved.append(True)
	
	def resolve_callback_remove(self,sdRef, flags, interfaceIndex, errorCode, fullname,
						 hosttarget, port, txtRecord):
		if errorCode != pybonjour.kDNSServiceErr_NoError:
			return
		#print 'Resolved service:'
		#print '  fullname	 =', fullname
		#print '  hosttarget =', hosttarget
		#print '  port		 =', port
		query_sdRef = \
			pybonjour.DNSServiceQueryRecord(interfaceIndex = interfaceIndex,
											fullname = hosttarget,
											rrtype = pybonjour.kDNSServiceType_A,
											callBack = self.query_record_callback)
		try:
			while not self.queried:
				ready = select.select([query_sdRef], [], [], self.TIMEOUT)
				if query_sdRef not in ready[0]:
					print 'Query record timed out'
					break
				pybonjour.DNSServiceProcessResult(query_sdRef)
			else:
				#print self.queried.pop()
				self.remove_callback(fullname[:-1].decode('string_escape'), hosttarget[:-1], self.queried.pop(), port)
		finally:
			query_sdRef.close()
		self.resolved.append(True)
	
	def browse_callback(self, sdRef, flags, interfaceIndex, errorCode, serviceName,
			regtype, replyDomain):
		if errorCode != pybonjour.kDNSServiceErr_NoError:
			return
		r_callback = self.resolve_callback
		if not (flags & pybonjour.kDNSServiceFlagsAdd):
			#print 'Service removed'
			#print interfaceIndex, serviceName, regtype, replyDomain
			self.remove_callback(serviceName+"."+regtype+replyDomain[:-1])
			return
		#print 'Service added; resolving'
		resolve_sdRef = pybonjour.DNSServiceResolve(0,
													interfaceIndex,
													serviceName,
													regtype,
													replyDomain,
													self.resolve_callback)
		#print interfaceIndex, serviceName, regtype, replyDomain
		try:
			while not self.resolved:
				ready = select.select([resolve_sdRef], [], [], self.TIMEOUT)
				if resolve_sdRef not in ready[0]:
					print 'Resolve timed out (new node)'
					break
				pybonjour.DNSServiceProcessResult(resolve_sdRef)
			else:
				self.resolved.pop()
		finally:
			resolve_sdRef.close()
	
	def run(self):
		try:
			try:
				while True:
					ready = select.select([self.browse_sdRef], [], [])
					if self.browse_sdRef in ready[0]:
						pybonjour.DNSServiceProcessResult(self.browse_sdRef)
			except Exception:
				pass
		finally:
			try:
				self.browse_sdRef.close()
			except:
				pass
	
	def stop(self):
		"""docstring for stop"""
		try:
			self.browse_sdRef.close()
		except Exception:
			pass

class MulticastDiscoveryService(object):
	"""docstring for MulticastDiscoveryService"""
	def __init__(self, new_callback, del_callback):
		super(MulticastDiscoveryService, self).__init__()
		if sys.platform == "darwin" or sys.platform == "win32" or sys.platform == "cygwin":
			self.ds = BonjourDiscoveryService(new_callback, del_callback)
		else:
			self.ds = AvahiDiscoveryService(new_callback, del_callback)
	
	def start(self):
		"""docstring for start"""
		self.ds.start()
	
	def stop(self):
		"""docstring for stop"""
		self.ds.stop()
		self.ds.join()


