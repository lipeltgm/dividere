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
    serverPort=dividere.registry.ServiceRegistry.Server.port
    serviceRegistry=dividere.registry.ServiceRegistry.Server(serverPort)
 
    serviceName='someService'
    servicePort=5001
    client=dividere.registry.ServiceRegistry.Client('localhost',serverPort)
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

# def test01(self):
#   m=MsgLib.unregisterService()
#   print(m.__class__.__name__)
