import unittest
import logging
import dividere 
import TestMsg_pb2 as TestMsg
import random
import uuid
import time
from dividere import MsgLib
import socket


def getLocalIp():
   #--create a temp socket to get the local ip address
   s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.connect(('8.8.8.8',1))
   retVal=s.getsockname()[0]
   s.close()
   return retVal

class serviceRegistryTests(unittest.TestCase):
  def test00(self):
    logging.info("executing test")
    serviceRegistry=dividere.registry.ServiceRegistry.Server()
 
    serviceName='someService'
    servicePort=5101
    client=dividere.registry.ServiceRegistry.Client('localhost',dividere.registry.ServiceRegistry.Server.port)
    client.registerService(serviceName, servicePort)
    m=client.lookupService(serviceName)
    print("m:",m)
    self.assertTrue(m.name==serviceName)
    self.assertTrue(m.server==getLocalIp())
    self.assertTrue(m.port==servicePort)
    client.unregisterService(serviceName, servicePort)
    m=client.lookupService(serviceName)
    print("m:",m)
    serviceRegistry.stop()
    time.sleep(3); #--give serviceRegistry a chance to cleanup for future tests

# def test01(self):
#   m=MsgLib.unregisterService()
#   print(m.__class__.__name__)
